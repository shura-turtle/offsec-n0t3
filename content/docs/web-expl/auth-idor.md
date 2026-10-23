---
title: "Auth & IDOR · Compare Two Accounts"
weight: 40
bookToc: true
---

# Authentication, authorization and IDOR

**Use two accounts and known object IDs.** The strongest first test is whether account B can read one private object created by account A. Guessing lots of IDs is less informative.

## 1. Build a small ownership matrix

| Request | Expected |
| --- | --- |
| A token → A private object | Allowed |
| B token → B private object | Allowed |
| B token → A private object | Denied |
| No token → A private object | Denied |

Keep cookies separate in browser profiles or Repeater tabs. Verify identity at `/me` before each comparison. Public profiles are not automatically IDOR; test data intended to be private.

```http
GET /api/notes/731 HTTP/1.1
Host: ctf.invalid
Authorization: Bearer ACCOUNT_B_TOKEN
```

If note 731 belongs to A and contains A's private marker, B reading it proves broken object authorization. Status `200` with a generic application shell proves nothing.

## 2. Where object identifiers hide

```text
/api/notes/731
/api/users/12/notes/731
/download?file_id=731
/api/export?ownerId=12
/api/profile/12/avatar
{"noteId":731}
{"input":{"ownerId":12,"id":731}}
```

Check path, query, JSON, nested objects, GraphQL arguments and multipart fields. UUIDs are identifiers, not authorization. Encoded IDs may decode to `User:12`; decode structure but preserve the expected format when substituting.

Nested route mismatch:

```http
GET /api/users/ACCOUNT_B_ID/notes/ACCOUNT_A_NOTE_ID HTTP/1.1
Host: ctf.invalid
Authorization: Bearer ACCOUNT_B_TOKEN
```

The parent route may validate B while the final lookup fetches A's note globally.

## 3. Read, modify and workflow authorization are different

First prove a read. For write checks, use only your own test object with a reversible marker:

```http
PATCH /api/notes/ACCOUNT_A_NOTE_ID HTTP/1.1
Host: ctf.invalid
Authorization: Bearer ACCOUNT_B_TOKEN
Content-Type: application/json

{"title":"CTF_AUTHZ_TEST"}
```

Refetch as A to confirm persistence. A successful-looking response can be ignored input. Avoid deleting objects when an update demonstrates the same missing check.

Compare list, detail, download, share, export, attachments and version-history endpoints. A protected `/notes/id` may coexist with an unprotected `/notes/id/export`.

## 4. Mass assignment / hidden fields

Look at frontend JSON and source for actual field names. Add one candidate at a time to your own profile/account creation request:

```json
{"displayName":"ctf-player","role":"admin"}
{"displayName":"ctf-player","isAdmin":true}
{"displayName":"ctf-player","user":{"role":"admin"}}
{"title":"test","ownerId":"ACCOUNT_A_ID"}
```

These are candidates, not magic names. Check `/me`, a privileged resource and persisted state afterwards. An echoed `role` or frontend badge is not evidence that the backend trusts it. A strict schema may silently discard unknown keys.

## 5. Authentication workflow gaps

| Flow | Manual comparison |
| --- | --- |
| Login | Change only password; verify error/body/cookies |
| MFA | With pre-MFA session, request the final protected endpoint directly |
| Reset | Use A's reset token with B's email/account ID; do not target other users |
| Email change | Is password/confirmation required before the new email becomes trusted? |
| Invite | Does changing team/role in acceptance body override the signed invitation? |
| Logout | Replay the previous token against a protected route |
| Step-by-step checkout | Request final step without the earlier required state |

Successful page navigation is weaker than a protected API returning data. A route guard in JavaScript does not establish server enforcement.

## 6. Password reset example

Capture the normal reset-confirm request for account A:

```http
POST /api/reset/confirm HTTP/1.1
Host: ctf.invalid
Content-Type: application/json

{"email":"account-a@example.invalid","token":"A_RESET_TOKEN","password":"NewTestPassword!"}
```

Repeat with **your second account's** email while keeping A's token. If B's password changes, the reset token is not bound correctly. Do not infer success from a generic “reset complete”; test login for B. A token reused after a successful reset tests single-use semantics separately.

If a reset link's origin derives from a request header, inspect a generated link in your own account's message view. `Host`/`X-Forwarded-Host` behavior depends on the proxy trust setup; changing a header alone proves no exploit.

## 7. Client trust and headers

```http
GET /admin HTTP/1.1
Host: ctf.invalid
Cookie: session=YOUR_SESSION
X-User-Id: 1
X-Role: admin
```

Only relevant if source, proxy config or client code identifies these as trusted headers. Arbitrary header names are usually ignored. Compare public-proxy and backend behavior only when both are within challenge scope.

Editable unsigned cookies such as `role=user` can indicate a trust flaw, but a signed session cookie cannot be changed by editing its visible data. Use [JWT](../jwt/) for token verification problems and [NoSQL](../nosqli/) or [SQLi](../sqli/) when login input reaches a query.

## 8. Parameter ambiguity

If app components choose different duplicate values, these raw bodies may produce different decisions:

```text
userId=A&userId=B
userId=B&userId=A
```

JSON duplicate keys are ambiguous across parsers; many use the last value, others reject them. Measure actual behavior. Do not assume a duplicate parameter bypasses authorization without observing the protected result.

## 9. False positives and completion

| Observation | Interpretation |
| --- | --- |
| All object IDs show same page | SPA shell / generic fallback, not evidence |
| Both accounts can read it | It may be public or intentionally shared |
| B edits only response preview | Check persisted server state |
| Admin page opens, API denies | Frontend route leak without backend privilege |
| Old JWT still works after logout | Could be intended stateless expiry; assess challenge objective |
| Unknown user and wrong password differ | Enumeration clue; not yet account access |

Record the exact missing ownership/role/state check and one private marker proving access. Restore reversible changes to your own test data.

## Tool workflow

Use [Burp Community Repeater](../../ajcbbc_allow_tools/burp_suite_community/) for paired manual requests. Keep the baseline in one tab and change one input in another. Browser-only behavior such as XSS, cookies and CORS still needs a real browser proof.

## References

[OWASP authorization testing](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/), [OWASP mass assignment](https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html), [OWASP password reset guidance](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html).
