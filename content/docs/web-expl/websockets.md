---
title: "WebSockets / Live Sessions"
weight: 53
bookToc: true
---

# WebSockets and Live Sessions

**A successful upgrade is only the start.** Preserve message order, session state, sequence IDs, and asynchronous responses through the challenge's final result.

## 1. Capture the actual protocol

Browser DevTools → Network → WS → Messages, or Burp's WebSocket history.

```http
GET /socket HTTP/1.1
Host: ctf.invalid
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Origin: https://ctf.invalid
Cookie: session=YOUR_SESSION

```

That key is the RFC example. A real client generates a fresh key and handles the handshake. Do not send an arbitrary HTTP body after upgrading and assume it is a valid WebSocket frame. Browser/client libraries mask client frames, handle fragmentation, and respond to control frames.

## 2. Identify the application layer

| Message shape | Possible layer | Next step |
| --- | --- | --- |
| JSON objects | Custom protocol | Map action/type/id fields |
| `0{...}`, `40`, `42[...]` | Engine.IO / Socket.IO candidate | Determine transport and exact framing/version |
| Binary frames | Protobuf / custom bytes / compressed data | Capture bytes; read source/schema before changing offsets |
| Subscribe → ack → event messages | Topic protocol | Keep connection open and observe events |

Socket.IO is not interchangeable with a plain WebSocket JSON connection. A TCP socket is not automatically a WebSocket client.

## 3. Test one message at a time

Example baseline:

```json
{"type":"get_note","id":101,"request_id":1}
```

Potential object-authorization test using two authorized accounts:

```json
{"type":"get_note","id":202,"request_id":2}
```

Check whether the server verifies ownership for **every message**, not only at the handshake. Try unauthenticated messages only in a separately recorded session; do not confuse them with an authenticated connection that retained state.

Other sinks may be identical to HTTP:

```json
{"type":"chat","message":"<img src=x onerror=alert(1)>"}
```

That is an XSS lead only if another client renders the message as executable HTML. Database/template/command payloads must fit the server handler for that message type. See the corresponding web technique page.

## 4. Cross-site WebSocket hijacking

Inspect the `Origin` header check and session cookies. From a permitted lab page:

```javascript
const ws = new WebSocket('wss://ctf.invalid/socket');
ws.onopen = () => ws.send(JSON.stringify({type: 'whoami'}));
ws.onmessage = event => console.log(event.data);
```

In a browser, the actual page origin determines the handshake Origin. Repeater can edit it, but that does not prove a browser can authenticate cross-site. Cookie SameSite rules, partitioning, third-party cookie restrictions, and server checks matter. Browser CORS headers are not the WebSocket authorization mechanism.

## 5. Follow the full state machine

```text
connect → authenticate → select mode/topic → setup
  → arm/enable/start if protocol requires it
  → send command with correct message ID
  → ACK confirms receipt
  → keep receiving telemetry/status
  → final objective / flag / definitive error
```

Resolve numeric command IDs using the exact protocol dialect. A `200`, `ok`, or ACK can mean only accepted, not completed. If the server sends periodic heartbeats, keep replying as the protocol requires.

## 6. Troubleshooting

| Symptom | Check |
| --- | --- |
| `400` / failed upgrade | Origin, URL, required subprotocol, cookie, transport version |
| Connected but no action | Need auth/subscription/setup message first |
| ACK but no result | Continue reading; inspect state/mode/preconditions |
| Immediate close | Close code/reason, frame type, schema, heartbeat |
| Replayed message fails | Sequence ID, nonce, expiry, session-specific object IDs |

Tool map: [Burp](../../ajcbbc_allow_tools/burp_suite_community/) · [Chrome](../../ajcbbc_allow_tools/google_chrome/) · [Wireshark](../../ajcbbc_allow_tools/wireshark/). See [network sessions](../../network-expl/tcp-udp/) for raw TCP/UDP, which have different framing.

References: [WebSocket protocol RFC 6455](https://www.rfc-editor.org/rfc/rfc6455), [PortSwigger WebSocket testing](https://portswigger.net/web-security/websockets).
