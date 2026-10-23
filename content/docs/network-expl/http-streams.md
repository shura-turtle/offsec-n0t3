---
title: "02 · HTTP / File Streams"
weight: 2
bookToc: true
---

# HTTP Requests, Responses, and Objects

**Flow:** identify the HTTP version → locate request → match response → decode transport framing → export object → inspect bytes.

**Tools:** [Wireshark](../../ajcbbc_allow_tools/wireshark/), [TShark](../../ajcbbc_allow_tools/tshark/), [Burp Community](../../ajcbbc_allow_tools/burp_suite_community/), [CyberChef](../../ajcbbc_allow_tools/cyberchef/), [HxD](../../ajcbbc_allow_tools/hxd/).

## 1. Find the actual protocol

```text
http
http2
tls
tcp.port == 8080
```

For plaintext HTTP on an unusual port, inspect the bytes for a request/status line, then use **Analyze → Decode As → HTTP**. A port alone is insufficient.

```bash
tshark -r traffic.pcapng -d tcp.port==8080,http -Y 'http.request'
```

HTTP/2 uses binary frames and stream IDs. A TCP connection can contain many simultaneous HTTP/2 requests. Match an HTTP/2 stream within its connection; a `tcp.stream` value alone is not a single request.

## 2. Extract request metadata first

```bash
tshark -r traffic.pcapng -Y 'http.request' -T fields \
  -E header=y -E separator=/t \
  -e frame.number -e tcp.stream -e http.request.method \
  -e http.host -e http.request.uri -e http.user_agent
```

Useful GUI filters:

```text
http.request.method == "POST"
http.request.uri contains "upload"
http.request.uri contains "flag"
http.authorization
http.cookie
http.set_cookie
http.response.code >= 400
```

Requests can reveal the endpoint, parameters, session cookie, file name, or password required elsewhere. Preserve duplicates and order when a later request depends on an earlier one.

## 3. Pair requests and responses

1. Select the request in Wireshark.
2. Expand the HTTP tree and follow the linked response frame when provided.
3. Record request/response frame numbers and TCP stream.
4. For redirects, inspect the destination and subsequent request.
5. For downloads, inspect status, Content-Type, Content-Disposition, and body length.

A `200` may be an error JSON wrapper or login page. A `302` may return to login. The response body determines whether the requested object was returned.

## 4. Export objects before hand-carving

```text
File -> Export Objects -> HTTP
Choose object -> Save to an evidence directory
```

TShark equivalent:

```bash
tshark -r traffic.pcapng --export-objects http,http_objects
```

Choose a fresh directory to avoid filename collisions with earlier runs. Check the generated files and protocol tree. A recovered file may still be an archive, compressed payload, or encrypted application object.

Use [xxd](../../ajcbbc_allow_tools/xxd/) or HxD to inspect magic bytes:

```bash
xxd -l 64 http_objects/download.bin
```

| Header bytes | Candidate |
| --- | --- |
| `50 4b 03 04` | ZIP-like container |
| `1f 8b` | gzip stream |
| `25 50 44 46` | PDF |
| `89 50 4e 47` | PNG |
| `7f 45 4c 46` | ELF executable |

A signature is a lead. Validate by opening/parsing the object with the corresponding approved tool.

## 5. Separate framing from content

An HTTP response can contain:

```text
HTTP headers
  -> chunked transfer framing (HTTP/1.1 when selected)
     -> gzip/content encoding
        -> MIME or archive data
```

Chunk lengths and CRLF separators are not part of the downloaded file. `Content-Encoding: gzip` differs from a gzip file intentionally downloaded as an object.

Do not Base64-decode the entire followed TCP stream. First isolate the actual encoded field or attachment. A raw bidirectional stream mixes client requests with server responses.

If object export produces invalid bytes, compare its size to reassembled data and check truncation, missing packets, and encryption. Avoid “fixing” a file by deleting unexplained bytes until framing explains them.

## 6. Forms and file uploads

For a POST, inspect the request Content-Type:

| Type | Inspect |
| --- | --- |
| `application/x-www-form-urlencoded` | Percent encoding, `+` as space, duplicate keys |
| `application/json` | Nested values, escaped strings, literal JSON types |
| `multipart/form-data` | Boundary, part headers, filename, binary body |
| `application/octet-stream` | Raw bytes, known application framing |

A multipart file part begins after its part headers and ends before the next MIME boundary. Do not include the boundary text in an exported file.

Use Burp's message editor/Decoder on the isolated request when reproducing a supplied challenge request. Preserve the original method, path, cookies, and content type.

## 7. Basic authentication and cookies

```text
Authorization: Basic dXNlcjpwYXNz
```

The Base64 value represents `user:pass`; it is encoding, not encryption. Decode the field in CyberChef. A cookie may instead be a session identifier, signed data, or encrypted state; a readable cookie does not imply forgery is possible.

For attack workflows following an observed HTTP lead, continue to [Web Exploitation](../../web-expl/).

## 8. HTTPS / HTTP/2 / HTTP/3 caveats

- TLS must be decrypted before ordinary HTTP fields appear.
- HTTP/2 may require connection context and reassembly.
- HTTP/3 runs over QUIC/UDP; a TCP-only filter excludes it.
- Matching key material and supported dissectors matter; renaming a protocol with Decode As does not remove encryption.
- A capture started mid-connection can lack essential negotiated state.

See [TLS/SSH](../tls-ssh/) before attempting encrypted object export.

## Final checks

Record the parent capture, request frame, response frame, stream, exported filename, hash, and extraction method. Reopen the artifact and verify its intended structure. If only one direction was saved, record that choice.

Reference: [Wireshark User's Guide](https://www.wireshark.org/docs/wsug_html_chunked/) for stream-follow and object-export interfaces; [TShark](https://www.wireshark.org/docs/man-pages/tshark.html) for export syntax.
