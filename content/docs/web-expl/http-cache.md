---
title: "HTTP, Cache & Smuggling"
weight: 72
bookToc: true
---

# HTTP parsing, cache issues and request smuggling

**Map the components:** browser → CDN/cache → reverse proxy → application. Ask what each considers the host, path, cache key and end of the request.

## 1. Establish a baseline

Capture the exact HTTP version, route and response headers. Repeat the request to see whether a cache is present.

```http
GET /?probe=cache71 HTTP/1.1
Host: ctf.invalid

```

Inspect `Age`, `Via`, `X-Cache`, cache-status headers, `Cache-Control` and `Vary`. A missing cache header does not establish absence of caching; a header saying `HIT` is still weaker evidence than a controlled stored response difference.

Use a unique challenge-only path/query as a cache buster, **then verify that it changes the cache key**. If the cache ignores that parameter, it will not isolate your tests.

## 2. Cache poisoning: unkeyed input changes a stored response

Potential inputs include forwarded-host headers, rewrite headers and query parameters omitted from the cache key. Test one at a time:

```http
GET /?probe=poison71 HTTP/1.1
Host: ctf.invalid
X-Forwarded-Host: marker71.invalid

```

Look for a changed absolute link, redirect or resource URL. Then send the same keyed URL **without** the added header:

```http
GET /?probe=poison71 HTTP/1.1
Host: ctf.invalid

```

If the second response retains the injected marker because a shared cache stored it, you have a poisoning signal. Confirm a fresh key produces a clean response. Reflection in the first response alone is insufficient. Follow the exact cached resource used by the challenge victim; arbitrary response changes may have no useful impact.

Additional candidates, only when the stack uses them:

```http
X-Forwarded-Proto: http
X-Original-URL: /marker71
X-Rewrite-URL: /marker71
```

Header trust is configuration-dependent. These names have no universal semantics in HTTP.

## 3. Cache deception: private response classified as public/static

Try a known private route with a path suffix:

```text
/my-account/marker71.css
/my-account;marker71.css
```

Workflow:

1. As challenge user A, request the candidate once. Does it still return A's account content?
2. Request the **identical URL** without A's cookie or as user B.
3. Compare with a fresh unvisited candidate path and the normal protected route.
4. Confirm any leaked content belongs to A and was served by the cache.

This requires both origin routing that returns the private page and cache rules that store it. Static-looking extensions alone prove neither. Different delimiters and normalization behavior depend on the actual proxy/origin pair. See [web cache deception](https://portswigger.net/web-security/web-cache-deception).

## 4. CRLF response-header injection

Candidate sinks: redirect `next`, filename in `Content-Disposition`, reflected cookie/header values.

```text
/home%0d%0aX-CTF-Probe:%20marker71
```

Enter this as an encoded value only where a decoded parameter reaches a response header. Inspect the **raw response headers**: a new `X-CTF-Probe` header is evidence; the same text in `Location` or an HTML body is not.

Modern frameworks commonly reject CR/LF in header values. A `400` or exception is not a successful split. For request-header tests, `%0d%0a` often stays literal: HTTP headers are not automatically URL-decoded like form values.

## 5. Request smuggling: learn framing before payloads

HTTP/1.1 uses byte counts and chunk framing; parser disagreement may cause leftover bytes to become another request. [RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html) defines framing and handling of conflicting lengths.

| Name | Frontend uses | Backend uses |
| --- | --- | --- |
| CL.TE | Content-Length | Transfer-Encoding |
| TE.CL | Transfer-Encoding | Content-Length |
| TE.TE | Recognizes a TE variant | Ignores/parses that variant differently |
| H2.CL / H2.TE | HTTP/2 framing | Unsafe HTTP/1 downgrade framing |

These names describe an observed parser pair, not guaranteed behavior. A server accepting one request with both headers is not sufficient proof.

### Exact framing controls

A valid nonambiguous five-byte body:

```http
POST / HTTP/1.1
Host: ctf.invalid
Content-Type: text/plain
Content-Length: 5

hello
```

The body is exactly `hello`, with **no extra trailing newline**. The displayed code fence may visually add one: verify the raw bytes in Repeater.

A separate valid chunked control uses the body bytes `5\r\nhello\r\n0\r\n\r\n`:

```http
POST / HTTP/1.1
Host: ctf.invalid
Content-Type: text/plain
Transfer-Encoding: chunked

5
hello
0

```

Every displayed line ending must be CRLF on the wire; the final zero chunk ends with an empty line. Chunk size `5` is hexadecimal and counts only the five data bytes.

### Detection workflow in a dedicated challenge instance

1. Confirm ordinary Content-Length and chunked controls separately.
2. Confirm whether Repeater is sending HTTP/1.1 or HTTP/2; editor text is not necessarily wire framing.
3. For the suspected parser pair, design a one-byte/short-prefix discrepancy and calculate both parsers' consumed bytes.
4. Disable automatic Content-Length correction only when intentionally testing a mismatch.
5. Compare timeout behavior with a fully consumed control; use a fresh connection to rule out leftovers.
6. Confirm a controlled follow-up request gets a response altered by your chosen prefix, on the same relevant reused backend connection.

Timeouts alone are inconclusive: network delay, incomplete body buffering and generic rejection can look similar. HTTP/2-to-HTTP/1 conversion can rewrite or reject your test. Do not mix a copied CL.TE body with TE.CL length assumptions. [PortSwigger detection guidance](https://portswigger.net/web-security/request-smuggling/finding) gives parser-specific examples; compute lengths for the request you actually send.

## 6. Troubleshooting

| Symptom | Check |
| --- | --- |
| Poison only visible to your cookie | Private/session-keyed cache rather than shared poisoning |
| Cache buster has no effect | Parameter omitted from key; find an actually keyed component |
| One arbitrary request returns `400` | Syntax rejection alone is not desynchronization |
| Framing silently changes | HTTP version, proxy normalization, Repeater length correction |
| Correct prefix, no follow-up effect | Connection reuse, frontend routing or backend isolation |

Related: [encoding/parser differences](../encoding-filters/), [Burp notes](../../ajcbbc_allow_tools/burp_suite_community/).

References: [web cache poisoning](https://portswigger.net/web-security/web-cache-poisoning), [request smuggling model](https://portswigger.net/web-security/request-smuggling).
