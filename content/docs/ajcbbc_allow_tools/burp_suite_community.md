---
title: "Burp Suite Community Edition"
weight: 20
bookToc: true
---

**Use for:** intercepting HTTP, editing requests and comparing responses.  
**Run in:** WSL GUI according to the supplied list; needs a working display.  
**Listed version:** 2026.4.x; verify the competition build under Help/About.

## Launch the supplied application

```bash
# If the installation provides a launcher on PATH
burpsuite

# Alternative only when the organizer supplies a JAR and Java
java -jar /path/to/burpsuite_community.jar
```

## Walkthrough: modify a request

1. Start a temporary project with default settings.
2. **Proxy → Intercept → Open browser** uses Burp’s configured browser.
3. Browse to the assigned challenge.
4. Find the request in **Proxy → HTTP history**.
5. Right click → **Send to Repeater**.
6. In **Repeater**, send the unchanged request to establish a baseline.
7. Change one parameter; compare status, response length and body.

## Useful tools

| Tool | Use |
| --- | --- |
| Repeater | Manually replay and edit requests |
| Decoder | Convert URL/Base64/hex representations |
| Comparer | Spot differences between responses |
| Intruder | Small controlled payload sets; Community has restrictions |
| HTTP history | Recover actual cookies, headers and request bodies |

## Gotchas

- Leave **Intercept off** when ordinary browsing appears stuck.
- Repeater needs the correct target host, port and HTTPS setting.
- CSRF tokens and session cookies can expire.
- Windows Chrome talking to a WSL proxy may need additional routing/proxy setup; prefer the configured Burp browser when available.
- Community does not include the Professional automated scanner. Follow the tournament’s ban on AI related additions.

## Read an HTTP request before editing it

```http
POST /api/item HTTP/1.1
Host: challenge.example
Content-Type: application/json
Cookie: session=REPLACE

{"id":7}
```

The method/path chooses the action, `Host` chooses the virtual host, the cookie identifies the session, and Content-Type tells the server how to parse the body. Keep a baseline before editing any of them.

## CTF: compare an authorization boundary

1. Obtain two accounts/resources that belong to you in the challenge.
2. Capture account A requesting its own item.
3. Send the request to Repeater and confirm the unchanged response.
4. Change only the item ID to account B’s known item.
5. Compare authorization status and returned ownership fields.
6. Repeat the control request to rule out logout/token expiry.

A `200` can contain an error wrapper; verify actual protected content or state. Keep both requests and responses as evidence.

## CTF: test server-side validation

Use Repeater to remove one optional-looking field, change a number into a string, or change a client-controlled value. Inspect the server’s handling rather than relying on disabled UI controls. For JSON, maintain valid syntax so a parser error is not confused with application behavior.

## CTF: examine an upload

Capture one valid upload and identify the multipart boundary, field names, filename and content type. Change one property at a time on a working request. Preserve the boundary and let Burp update the body length. An upload response is separate from successful retrieval or processing of the uploaded bytes.

## CTF: encoded values and duplicate parameters

Use Decoder to inspect URL/Base64 representations before altering a token. `%2f` is encoded text for `/`; double encoding introduces a second layer. If testing duplicate parameters, record whether the application selects the first, last, or multiple values; do not assume a framework’s behavior.

## Cookies, CSRF and redirects

| Symptom | Check |
| --- | --- |
| Browser works, Repeater fails | Fresh cookie/CSRF token, origin/referer, target host |
| `302` response | Destination and Set-Cookie; inspect before following |
| Redirect loop | Scheme, cookie path/domain and authentication state |
| Request waits forever | Intercept state, network route and service liveness |
| Edited body rejected immediately | Content-Type, valid syntax and required fields |

## Small Intruder experiments

Choose a short list of evidence-based candidate values, mark only the intended position, and compare response content/length. Community throttling can make large brute-force runs impractical. Use Repeater for decisions that require seeing every response.

## Launcher syntax explained

`java -jar FILE.jar` asks Java to launch the application packaged in that JAR. `-jar` is a Java switch, not a Burp scanning option. The `burpsuite` launcher may be a distribution wrapper; inspect its supplied help if needed. These notes use the GUI for testing.

References: [PortSwigger getting started](https://portswigger.net/burp/documentation/desktop/getting-started), [Repeater documentation](https://portswigger.net/burp/documentation/desktop/tools/repeater).

## Related playbooks

- [Web payload index](../../web-expl/)
- [Encoding and filters](../../web-expl/encoding-filters/)
- [WebSockets](../../web-expl/websockets/)
