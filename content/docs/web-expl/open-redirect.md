---
title: "Open Redirect / URL Parsing"
weight: 75
bookToc: true
---

# Open Redirect and URL Parsing

Look for `next`, `return`, `redirect`, `url`, `continue`, `callback`, or client-side navigation reading a URL parameter.

## 1. Establish the navigation sink

```http
GET /login?next=%2Fprofile HTTP/1.1
Host: ctf.invalid

```

Determine whether navigation is:

- An HTTP `Location` header on a 3xx response.
- An HTML `<meta http-equiv="refresh">`.
- A JavaScript assignment such as `location = input`.
- A link that only navigates when clicked.

Reflection in an anchor or message is not automatic redirection. Inspect the actual destination in the browser as well as the response headers.

## 2. Test URL components independently

Raw input candidates:

```text
/profile
https://ctf.invalid/profile
https://YOUR-LAB-HOST/
//YOUR-LAB-HOST/
https://ctf.invalid.evil.invalid/
https://ctf.invalid@YOUR-LAB-HOST/
https://YOUR-LAB-HOST/#ctf.invalid
https://YOUR-LAB-HOST/?allowed=ctf.invalid
```

| Candidate | What it tests |
| --- | --- |
| Absolute external URL | No destination validation |
| `//host/` | Network-path reference / missing scheme checks |
| Allowed name as prefix of another host | Prefix match instead of host equality |
| `allowed@other` | Userinfo mistaken for hostname |
| Allowed name in fragment/query | Substring match over full URL |

`YOUR-LAB-HOST` is a placeholder for the challenge-provided / permitted destination. Never infer the host from visual string position: parse scheme, userinfo, host, port, path, query, fragment.

## 3. Encoding and parser differences

Try encoded variants only when a real decode/reparse stage exists:

```text
%2F%2FYOUR-LAB-HOST%2F
https%3A%2F%2FYOUR-LAB-HOST%2F
```

A browser, reverse proxy, server framework, and URL library can normalize backslashes, encoded separators, and duplicate parameters differently. There is no universal backslash bypass. Capture the final parsed destination on the actual component.

## 4. Follow the chain

An open redirect might be useful for:

```text
OAuth allowlisted callback → redirect endpoint → permitted result collector
SSRF validator accepts first URL → fetcher follows unchecked redirect
admin bot visits same-origin link → navigates to a permitted challenge page
```

Each chain needs its own preconditions. A redirect alone does not provide server-side fetch, XSS, or token disclosure. URL fragments are not sent as HTTP request targets, though client-side code can read them.

## 5. Negative controls

1. Confirm the normal same-origin destination works.
2. Try a clearly invalid scheme / URL and record rejection.
3. Try the candidate bypass, inspect `Location` and browser destination.
4. Verify the relevant follow-up behavior, such as an SSRF response or OAuth callback handling.

Tool map: [Burp](../../ajcbbc_allow_tools/burp_suite_community/) · [Chrome](../../ajcbbc_allow_tools/google_chrome/) · [CyberChef](../../ajcbbc_allow_tools/cyberchef/).

References: [WHATWG URL Standard](https://url.spec.whatwg.org/), [PortSwigger DOM open redirect](https://portswigger.net/web-security/dom-based/open-redirection).
