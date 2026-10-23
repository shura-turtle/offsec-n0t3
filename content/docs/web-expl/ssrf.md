---
title: "SSRF"
weight: 62
bookToc: true
---

# Server-side request forgery

**Establish that the server fetches a URL, then identify the URL parser, protocol and network location.** Typical sinks: previews, webhook testers, imports, stock checks, image/PDF renderers.

## 1. First probe and control

Give the endpoint a unique path on a challenge-provided callback service:

```text
http://YOUR-LAB-HOST/ssrf-marker-71
```

Then compare an ordinary valid fetch and an intentionally missing path. Inspect request method, headers, source and callback timing. A browser loading your image is not a server fetch; submit the same request in Repeater without rendering the page.

No callback facility? Compare an already known local service with a closed port. A timeout or connection error is a clue, not a reliable service identification on its own.

## 2. Local address ladder

```text
http://127.0.0.1/
http://localhost/
http://[::1]/
http://127.0.0.1:5000/
http://127.0.0.1:8000/
http://127.0.0.1:8080/
```

Choose ports from source, Docker Compose, errors or supplied challenge services. A localhost fetch happens inside the fetcher's container/network namespace; it may not reach the host machine or another container.

| Result | Meaning / next step |
| --- | --- |
| Internal page body appears | Response-reading SSRF; enumerate that service's actual routes |
| Immediate connection refused | Address reached but service may not listen at that port |
| Timeout | Could be filtering, unroutable address or a slow service |
| Callback logged but no body shown | Blind SSRF; look for later report storage or challenge-supported out-of-band proof |
| Your browser contacts the host | Client-side fetch; investigate browser restrictions separately |

## 3. Filter bypass: identify the failing layer

| Payload candidate | What it tests |
| --- | --- |
| `http://127.1/` | Client accepts abbreviated IPv4 |
| `http://2130706433/` | Client accepts integer IPv4 |
| `http://0x7f000001/` | Client accepts hexadecimal IPv4 |
| `http://[::ffff:127.0.0.1]/` | IPv4-mapped IPv6 handling differs |
| `http://allowed.invalid@127.0.0.1/` | Naive prefix/userinfo validation; actual host is loopback |
| `http://127.0.0.1/#allowed.invalid` | Naive substring validation; fragment is not sent as HTTP path |
| `http://allowed.invalid.YOUR-LAB-HOST/` | Substring check instead of a correct hostname boundary |

These forms are parser-dependent. Modern clients may reject or normalize them before any connection. A hostname ending in attacker-controlled text is not the allowlisted domain.

Observe **which host the HTTP client actually uses**. A parser disagreement requires two parsers with different results, not a cleverly formatted URL by itself.

## 4. Redirect checks

If a permitted lab host can return redirects, compare:

```http
HTTP/1.1 302 Found
Location: http://127.0.0.1:5000/
Content-Length: 0

```

Does the server follow redirects? Does it revalidate each destination and resolved IP? Some clients change POST to GET on a `302`; `307`/`308` preserve method under standard behavior. The target's client configuration decides what is followed.

## 5. Duplicate parameters and request construction

When a frontend validates one value but forwards a raw query downstream:

```text
url=http://allowed.invalid/&url=http://127.0.0.1:5000/
url=http://127.0.0.1:5000/&url=http://allowed.invalid/
```

These show raw query fragments: encode each inner URL as required. Compare both orders and single-value controls. Some parsers select first, last, an array, or reject duplicates. Never assume a language fixes this behavior for every framework/configuration.

## 6. Protocol and method limitations

| Candidate | Requirement / implication |
| --- | --- |
| `file:///etc/passwd` | Fetch library permits local-file scheme; this becomes a file-read path |
| `gopher://...` | Client supports Gopher and accepts crafted bytes; not a universal HTTP feature |
| HTTP internal admin GET | Endpoint is reachable and GET performs useful read/action |
| Internal POST | Need method/body control, redirect behavior or a genuine protocol pivot |
| Header-based internal auth | Need control of those headers; URL control alone is insufficient |

Do not paste a Redis or database payload into an HTTP-only fetcher and expect raw TCP. Identify the actual library's allowed protocols first.

## 7. Cloud-shaped labs

`http://169.254.169.254/` is a link-local metadata candidate in cloud-style challenges. Providers differ in paths, required headers, request methods and session tokens. A fetcher with only GET and no custom headers may be unable to complete a token-based flow. Inspect the challenge's provider clues rather than using one provider's paths everywhere.

## 8. Finish the chain

Internal service discovered → read its landing page/source/API documentation → reproduce its required method and parameters → satisfy auth/state prerequisites → retrieve the challenge result. An internal `200` proves reachability, not administrative access.

DNS rebinding is a later step: it requires resolution/connection timing that actually differs, a domain under your control and a permitted network path. First exhaust literal IP, redirect and parser-difference evidence.

Related: [XXE](../xxe/), [HTTP parsing](../http-cache/), [encoding](../encoding-filters/).

References: [PortSwigger SSRF](https://portswigger.net/web-security/ssrf), [curl URL syntax](https://curl.se/docs/url-syntax.html).
