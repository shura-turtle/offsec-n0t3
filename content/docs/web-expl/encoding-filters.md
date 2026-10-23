---
title: "Encoding & Filter Bypasses"
weight: 90
bookToc: true
---

# Encoding, filters and parser differences

**Write down the bytes at each layer.** Most failed payloads come from the wrong context, a changed transport encoding, or a bypass aimed at a parser the input never reaches.

```text
Your editor → HTTP transport → URL/form/JSON decoder → validation
→ framework parsing → query/template/shell/path parser → output encoding
```

Move validation in that diagram if source shows a different order. The same `%27` can be a quote, literal text, or a blocked token depending on the point inspected.

## 1. Transport reference

| Raw byte/character | URL percent form | Notes |
| --- | --- | --- |
| Space | `%20` | `+` means space only for form-style decoding |
| `+` | `%2B` | Literal plus in form values |
| `'` | `%27` | SQL quote only after URL decoding |
| `"` | `%22` | Does not replace JSON escaping |
| `#` | `%23` | Raw URL fragment is not sent to the server |
| `&` | `%26` | Raw form/query `&` separates fields |
| `=` | `%3D` | Useful inside encoded parameter values |
| `/` | `%2F` | Routers/proxies may treat encoded separators specially |
| `\` | `%5C` | Windows separator or parser-specific escape |
| `%` | `%25` | Encodes a percent; important for a second decoding stage |
| Tab / LF / CR | `%09` / `%0A` / `%0D` | Acceptance and normalization vary by sink |

In Burp's decoded parameter editor, enter the raw intended value and inspect the encoded request. In its raw editor, encode only what the transport requires. Do not encode the same layer twice accidentally.

## 2. Nested URL example

Intended inner URL:

```text
http://127.0.0.1:5000/search?q=a&limit=1
```

As the value of the outer `url` parameter:

```text
url=http%3A%2F%2F127.0.0.1%3A5000%2Fsearch%3Fq%3Da%26limit%3D1
```

Without `%26`, the outer parser may create a separate `limit` parameter instead of passing it to the inner service. Conversely, encoding the inner query twice can leave `%26` in the final URL rather than an argument separator.

## 3. JSON is not a form body

```json
{"name":"a\"b","path":"C:\\temp\\flag.txt"}
{"name":"\u0027"}
{"name":"%27"}
```

The first document contains a quote and Windows backslashes after JSON decoding. `\u0027` becomes a quote in a standard JSON string; `%27` normally remains percent-sign text unless the application explicitly URL-decodes it later.

Duplicate JSON keys are not a portable first/last-value bypass. Compare actual parser behavior and downstream reserialization.

## 4. Identify what the filter really does

Use a benign marker and compare the returned/stored value:

```text
AAunionBB
AAUNIONBB
AAUnIoNBB
AAuniuniononBB
```

| Observation | Candidate behavior | Follow-up |
| --- | --- | --- |
| Entire request rejected | Validation/WAF | Compare status, body and whether sink runs |
| Only lowercase disappears | Case-sensitive substring removal | Mixed case helps only if sink is case-insensitive |
| `uniunionon` becomes `union` | One-pass stripping | Test whether remaining token reaches the sink |
| Token removed repeatedly | Recursive cleanup | Double-writing the token will not help |
| Stored raw but displayed escaped | Output encoding | Inspect raw storage/next consumer; do not confuse display with sink |

A SQL case trick does not automatically apply to case-sensitive filenames or JavaScript property names.

## 5. Parser-specific substitutions

| Context | Candidate | Required condition |
| --- | --- | --- |
| SQL whitespace | `1/**/AND/**/1=1` | SQL dialect accepts block comments here |
| MySQL-specific syntax | `/*!50000SELECT*/` | Versioned comment syntax applies and version gate matches |
| POSIX shell spaces | `cat${IFS}/flag.txt` | Shell expands/splits variable outside quotes |
| POSIX shell keyword | `ca''t /flag.txt` | Shell quote concatenation occurs after filter |
| URL path | `%2e%2e%2f` | Decode/normalize order differs from validation |
| JSON keyword | `"\u0061dmin"` | Filter sees raw escape; JSON parser later emits `admin` |
| HTML text | `&#x3c;` | Becomes a literal `<` text character, not a new tag; another HTML parsing stage would be needed |

HTML entities do not decode inside ordinary JavaScript source as they do in HTML attributes. JavaScript escapes only work where JavaScript grammar permits them. URL encodings do not become SQL syntax without decoding first.

## 6. Normalization and parameter pollution

```text
role=user&role=admin
role=admin&role=user
```

Compare both orders and the two single-value controls. Record what validation sees and what the final sink sees. Depending on the stack, duplicate keys can become first value, last value, list, joined string or rejection.

For path filters, compare normalized vs raw values. For account identifiers, compare case, trailing spaces and Unicode only when the application has a concrete normalization discrepancy. Unicode “lookalike” punctuation is not necessarily interpreted as SQL/JavaScript syntax.

## 7. Offline standard-library encoding helper

Run locally to prepare exact payload bytes; it sends no network request:

```python
import base64
import json
from urllib.parse import quote, unquote, urlencode

payload = "../../flag.txt"
print("URL:", quote(payload, safe=""))
print("Form:", urlencode({"file": payload}))
print("JSON:", json.dumps({"file": payload}))
print("Base64:", base64.b64encode(payload.encode()).decode())
print("Bytes:", payload.encode().hex())
print("One decode:", unquote("%252e%252e%252f"))
```

`unquote()` decodes percent escapes; `unquote_plus()` additionally changes `+` into spaces. Choose based on the actual transport. Python's [URL quoting documentation](https://docs.python.org/3/library/urllib.parse.html) describes these differences.

## 8. Debugging checklist

1. Capture a working baseline and preserve auth/state.
2. Choose the exact parser context and a minimal probe.
3. Inspect raw HTTP bytes after your editor transforms them.
4. Compare a negative control.
5. Identify the one filter/normalization step blocking the probe.
6. Change only the representation relevant to that step.
7. Confirm the intended final value reaches the sink.

Related: [SQLi](../sqli/), [SSTI](../ssti/), [command injection](../command-injection/), [CyberChef decoder recipes](../../ajcbbc_allow_tools/cyberchef/).

Reference: [curl's URL parser differences](https://curl.se/docs/url-syntax.html).
