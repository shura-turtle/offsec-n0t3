---
title: "00 · First 10 Minutes"
weight: 1
bookToc: true
---

# First 10 Minutes

## 1. Read what the challenge gives you

If source is supplied, start there. Find routes, database setup, templates, upload handling, authentication checks, Dockerfile, and the flag placement. Trace **input → transformation → guard → dangerous operation → response**.

| Sink in source | Investigate |
| --- | --- |
| String concatenation / interpolation in SQL | [SQLi](../sqli/) |
| `render_template_string`, `Environment.from_string`, template compilation | [SSTI](../ssti/) |
| `findOne(req.body)`, object spread into a database filter | [NoSQLi](../nosqli/) |
| `exec`, `shell=True`, `system`, backticks | [Command injection](../command-injection/) |
| `open`, `readFile`, `include` using user path | [LFI / traversal](../lfi-traversal/) |
| Server HTTP client using user URL | [SSRF](../ssrf/) |
| Raw HTML / `innerHTML` / unescaped template output | [XSS](../xss/) |
| Object deserialization | [Deserialization](../deserialization/) |
| Recursive merge of untrusted JSON | [Prototype pollution](../prototype-pollution/) |

`execute("... WHERE id=?", (id,))` is different from constructing the SQL string first. Parameterization protects values; dynamically assembled identifiers, sort directions, or a later query can remain vulnerable.

## 2. Black-box: inspect before injecting

1. Open page source, DevTools Network, scripts, and storage. Read comments and hidden fields.
2. Inspect redirects and actual API calls, including errors. Note cookies, CSRF tokens, content types, and response fields.
3. Check `robots.txt`, `sitemap.xml`, linked JS source maps, and challenge-indicated backups. A `200` might be a catch-all: compare with a random nonexistent path.
4. Map every input: query, form, JSON, path, cookie, headers, upload filename, stored profile fields.
5. Decide where the result likely lives: database row, server file, environment variable, browser/admin bot, or gated workflow.

An `nginx` header does not identify the application or database. Flask suggests Python, but not necessarily Jinja injection. A browser form can still send JSON to an API.

## 3. Save a baseline in Repeater

```http
GET /search?q=apple HTTP/1.1
Host: ctf.invalid
Cookie: session=YOUR_SESSION
Connection: close

```

Change **one field at a time**. Compare status, headers, response length, actual records, error text, timing, and asynchronous job output. Ignore random request IDs and rotating tokens when comparing bodies.

| First probe | Matching control | Potential lead |
| --- | --- | --- |
| `apple'` | `apple` and `apple''` | SQL syntax context; not proof alone |
| `1 AND 1=1` | `1 AND 1=2` | SQL boolean oracle |
| `A{{7*7}}B` | `A{{7*8}}B` | Template evaluation if raw response changes to A49B / A56B |
| JSON object instead of string | Original string / wrong operator condition | NoSQL or type confusion |
| `../../../etc/hostname` | Known nonexistent file | Traversal / file read |
| `127.0.0.1; printf CTFPROBE` | Valid original input | Shell command execution |

## 4. Follow evidence, not a payload lottery

```text
SQL error names database → engine-specific schema queries
Template arithmetic in raw HTTP → engine fingerprint → context inspection
JSON object changes query semantics → operator injection tests
Input appears as literal HTML → inspect browser context before XSS
URL fetched by server → inspect SSRF response / redirect behavior
Stored input causes later error → test second-order sink
```

If every payload produces the same response, check the route, method, session, parameter name, content type, caching, and whether another request actually consumes the input.

## 5. Common time traps

- A changed page may be a rate limit, validation failure, expired session, or CSRF rejection.
- A login `302` may redirect back to the login page. Follow it and inspect the authenticated session.
- A fragment after `#` never goes to the HTTP server unless encoded as `%23` in a parameter.
- Browser-only arithmetic can be client-side templating. Compare raw response before calling it SSTI.
- A WAF rejection is not a database fingerprint. Read backend errors or use controlled engine functions.
- Do not discard a preview, PDF, canvas, image, or JS response: it can be the actual challenge evidence.
- For a stateful challenge, keep the session and inspect status/job responses until the final result appears.

**Next:** [SQLi](../sqli/) · [SSTI](../ssti/) · [Auth / IDOR](../auth-idor/)
