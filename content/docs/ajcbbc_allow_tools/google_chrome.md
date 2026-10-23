---
title: "Google Chrome"
weight: 5
bookToc: true
---

**Use for:** browser challenges, DevTools, HTTP traffic, client side code.  
**Run in:** Windows. No extra extension needed for these workflows.

## Quick keys

| Action | Key |
| --- | --- |
| DevTools | F12 or Ctrl+Shift+I |
| Page source | Ctrl+U |
| Search loaded sources | Ctrl+Shift+F inside DevTools |
| Inspect element | Ctrl+Shift+C |

## Walkthrough: inspect a request

1. Open **DevTools → Network** before performing the action.
2. Enable **Preserve log** when navigation would clear requests.
3. Reload or submit the form.
4. Select the request; inspect **Headers**, **Payload**, **Response**, and **Initiator**.
5. Filter **Fetch/XHR** for APIs or **WS** for WebSocket messages.
6. Record the method, URL, cookies, body and response.

## Inspect browser state

Use **Application → Storage** for cookies, local storage, session storage and IndexedDB.

```javascript
// DevTools Console: inspect this origin's browser state
document.cookie
Object.entries(localStorage)
Object.entries(sessionStorage)

// Same-origin request using this browser session
fetch('/api/status').then(r => r.text()).then(console.log)
```

## Gotchas

- `HttpOnly` cookies are absent from `document.cookie`; inspect them in Application.
- Client side validation can differ from server behavior; inspect the actual request.
- A Console fetch follows browser origin/CORS rules.
- Save useful responses and source snippets before changing state.

## CTF: follow client-side flag generation

1. Open **Sources** and locate the script used by the challenge page.
2. Pretty-print minified code when needed.
3. Search for the visible button text, endpoint or success message.
4. Set a breakpoint in its event handler.
5. Trigger the action and inspect Scope/Watch values.
6. Step through decoding/transformation code and copy the resulting value.

The value accepted by the server can differ from a client-side display. Check the actual request/response if the challenge has a server component.

## CTF: pause before an API request

Use **Sources → XHR/fetch Breakpoints** and add a substring of the relevant URL. Trigger the request, inspect the caller and variables, then continue execution. This helps locate a request builder hidden inside a large script bundle.

## CTF: inspect inline and loaded resources

Look in page source, HTML comments, script files, source maps when available and network responses. Source search covers loaded resources; it does not prove every server file has been searched.

## Decode browser strings in Console

```javascript
// Base64 text → a binary string; not automatically UTF-8 text
atob('ZmxhZ3tkZW1vfQ==')

// Percent-encoded text → decoded text
decodeURIComponent('flag%7Bdemo%7D')

// Binary-safe Base64 → bytes → UTF-8
const bytes = Uint8Array.from(atob('ZmxhZ3tkZW1vfQ=='), c => c.charCodeAt(0));
new TextDecoder().decode(bytes)
```

`atob` uses ordinary Base64; URL-safe token alphabets and omitted padding need normalization. Re-running a `const` declaration in the same Console context can require renaming it or using a block.

## Replay one same-origin API call

```javascript
fetch('/api/item', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({id: 7})
}).then(async response => ({
  status: response.status,
  body: await response.text()
})).then(console.log)
```

Use the challenge’s exact URL, method, token headers and body. This runs in the current browser session; changing localStorage alone does not necessarily change the server’s session.

## CTF: inspect WebSocket state

In **Network → WS**, select the connection and inspect messages. Record direction, message type and order. A connection banner, command ACK and final objective notification are separate events. Keep the session open when the protocol requires asynchronous updates.

## Troubleshooting browser-only solves

| Problem | Inspect |
| --- | --- |
| Sources changed after reload | Cache, source maps and loaded script URLs |
| Request absent from Network | Open DevTools before triggering; preserve logs |
| Response blocked in JavaScript | CORS and actual Network status/body |
| Breakpoint never hits | Wrong file, handler or asynchronous branch |
| Flag-looking string is rejected | Decoy, encoding layer, prefix or incomplete generation |

References: [Network guide](https://developer.chrome.com/docs/devtools/network), [JavaScript breakpoints](https://developer.chrome.com/docs/devtools/javascript/breakpoints).

## Related playbooks

- [Web first 10 minutes](../../web-expl/methodology/)
- [XSS context testing](../../web-expl/xss/)
- [WebSockets](../../web-expl/websockets/)
