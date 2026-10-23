---
title: "Business Logic & Races"
weight: 71
bookToc: true
---

# Business logic and race conditions

**Write the invariant first:** “one account may redeem this code once,” “the charged amount equals the server's product price,” or “a completed order cannot change owner.” Then build the smallest request sequence that violates it.

## 1. Map the intended workflow

```text
Register → verify identity → add item → apply coupon → pay → confirm → download
```

Capture every request and object ID. Note which endpoint changes state, which values come from the client and which checks depend on previous steps. A disabled button is not a server check.

Use two challenge accounts where available. Check final balance, stored order and protected resource access instead of trusting a success toast.

## 2. Numeric and type boundaries

Assume the normal cart request is:

```json
{"product_id":7,"quantity":1}
```

Change only one field:

```json
{"product_id":7,"quantity":0}
{"product_id":7,"quantity":-1}
{"product_id":7,"quantity":0.5}
{"product_id":7,"quantity":"1"}
{"product_id":7,"quantity":null}
{"product_id":7,"quantity":[]}
```

| Observation | Next check |
| --- | --- |
| Negative item decreases total | Can checkout or refund increase balance? |
| Fractional quantity accepted | Are payment and fulfillment rounding consistent? |
| String accepted as number | Does another endpoint parse it differently? |
| Missing/null field uses a default | Is the default safer or more privileged? |
| Large value wraps or changes sign | Identify integer width and subsequent pricing calculation |

Try boundary values guided by the language/storage type, such as `2147483647` and `2147483648`, rather than assuming every stack uses 32-bit signed integers. JSON does not standardly allow `NaN` or `Infinity`; parser acceptance is implementation-dependent.

## 3. Trust in client-supplied prices and state

```json
{"product_id":7,"quantity":1,"price":1}
{"product_id":7,"quantity":1,"discount":100}
{"product_id":7,"quantity":1,"paid":true}
```

These keys only matter if the server actually reads or mass-assigns them. Inspect HTML/JS and normal request bodies first. If the price merely echoes in a response, compare the stored order and final payment amount.

Watch for mismatches between currency units (`1` dollar vs `1` cent), rounding per item vs per order, and discounts applied before vs after a minimum-value check.

## 4. State-machine tests

| Test | Example sequence |
| --- | --- |
| Skip a step | Call confirmation/download before payment |
| Replay a step | Redeem the same code twice sequentially |
| Reorder steps | Add expensive item after minimum-price/payment validation |
| Change identity midway | Start flow as A, complete with B's session |
| Change object midway | Pay order A, submit confirmation using order B |
| Reuse a token | Reuse reset/invitation/claim token after successful completion |
| Cancel then finish | Cancel/refund and later replay fulfillment |

Keep a normal sequence as the control. A `302` to the next step is not proof of a completed state transition. Refresh server-side state after every test.

## 5. Duplicate values / normalization

```text
quantity=1&quantity=-1
coupon=FIRST&coupon=SECOND
email=user@example.invalid
email=USER@example.invalid
```

Duplicate field handling differs by parser. Case normalization differs by application and identity policy. Demonstrate that two components disagree before using it as a bypass. Do not assume duplicate JSON keys are interpreted consistently.

## 6. Race conditions: first rule out ordinary replay

1. Get a clean account/item/token state.
2. Send the action twice **sequentially**. Record the final state.
3. Reset/recreate equivalent state.
4. Send the same two prepared requests **in parallel**, using Repeater's parallel group send if your installed version supports it.
5. Compare stored effects with the sequential control.

```http
POST /coupon/redeem HTTP/1.1
Host: ctf.invalid
Cookie: session=YOUR_SESSION
Content-Type: application/x-www-form-urlencoded

code=ONCE
```

If sequential replay already redeems twice, ordinary missing replay protection explains it; concurrency is not required. A genuine race signal is an extra persisted effect appearing only when checks and writes overlap.

## 7. Race prerequisites and failure modes

| Constraint | Consequence |
| --- | --- |
| One-time CSRF token | Identical replay may fail before the vulnerable operation |
| Session lock | Same-session requests may serialize; use the application's permitted parallel identities if relevant |
| Database transaction/unique constraint | Application timing window may still be protected at persistence |
| Client opens separate connections | Connection timing can dominate the overlap |
| Job queue | Effects may happen asynchronously; monitor until final state |
| Stock/code consumed by first attempt | New attempts require a fresh fixture/reset |

Begin with two requests. More volume does not establish correctness. For transfer races, check both source and destination balances plus the transaction ledger; two success responses can still correspond to one committed operation. [PortSwigger's race-condition model](https://portswigger.net/web-security/race-conditions) explains hidden intermediate states and synchronized testing.

## 8. Minimal evidence record

```text
Invariant:
Starting balance / state:
Normal sequence:
Modified sequence:
Sequential result:
Parallel result (if applicable):
Stored final state:
Protected resource / challenge result:
```

Related: [auth / IDOR](../auth-idor/), [Burp manual workflow](../../ajcbbc_allow_tools/burp_suite_community/).

Reference: [business logic vulnerabilities](https://portswigger.net/web-security/logic-flaws).
