---
title: "File Upload"
weight: 64
bookToc: true
---

# File upload

**Track four stages separately: accepted → stored → reachable → interpreted.** An upload success message proves only the first stage.

## 1. Establish the normal path

Upload an allowed small file with a unique marker. Save the multipart request, response URL, final stored filename and retrieval response headers. Compare the retrieved bytes with the original: resizing/re-encoding can remove appended content and metadata.

```http
POST /upload HTTP/1.1
Host: ctf.invalid
Content-Type: multipart/form-data; boundary=ctf71

--ctf71
Content-Disposition: form-data; name="file"; filename="marker.txt"
Content-Type: text/plain

CTF_UPLOAD_71
--ctf71--
```

Keep other required fields, cookies and CSRF tokens from the captured request. Let Repeater update `Content-Length`. Multipart delimiters use the exact declared boundary with two leading dashes; the last delimiter has two trailing dashes.

## 2. Isolate the check

Change one dimension per request:

| Dimension | Test | Interpretation |
| --- | --- | --- |
| Filename extension | Valid image bytes as `marker.txt` vs `marker.png` | Name-based restriction |
| Part MIME | Same bytes/name, `image/png` vs `text/plain` | Trust in attacker-controlled part header |
| File signature | Real image vs plain marker with identical name/MIME | Magic-byte or decoder validation |
| Actual decoder | Valid image vs truncated signature-only file | Full decoding rather than prefix inspection |
| Stored location | Original name vs random server name | Need response/source to locate the file |
| Response handling | Direct URL vs download endpoint | Web server interpretation may differ |

The multipart part MIME is separate from the outer `multipart/form-data` content type.

## 3. Extension candidates

```text
marker.php
marker.phtml
marker.php5
marker.PHP
marker.php.jpg
marker.jpg.php
marker.php.
```

These are hypotheses about extension checks and server handlers. `.php5` and `.phtml` execute only if configured. A double extension does not inherently execute. Trailing-dot normalization varies by OS/server. `%00` truncation is an old behavior, not a modern default.

Confirm actual behavior with a fixed executable marker in a matching PHP lab:

```php
<?php echo "CTF_EXEC_71"; ?>
```

If the browser shows PHP source or downloads it, execution failed. If only the generated marker appears, compare a different marker to rule out an existing static response. Then use a fixed file read where the challenge's file path is known:

```php
<?php echo file_get_contents('/flag.txt'); ?>
```

File permissions and runtime restrictions remain in force. Source disclosure, execution and static hosting have different outcomes. [PortSwigger describes this handler dependency](https://portswigger.net/web-security/file-upload).

## 4. Content and image processing

A prefix-only checker may accept a crude GIF-prefixed PHP payload:

```text
GIF89a
<?php echo "CTF_EXEC_71"; ?>
```

This is **not a valid fully decoded image**. If the server decodes/resizes images, start with a genuine allowed image and determine which metadata or byte regions survive. A polyglot must satisfy the actual decoder and later execution parser.

An image stored as `.jpg` does not execute PHP merely because it contains PHP tags. You also need an execution handler or a second inclusion sink. See [LFI chains](../lfi-traversal/).

## 5. Filename path handling

```text
../marker.txt
..\marker.txt
../../uploads/marker.txt
```

Compare returned name and retrieval path. Some libraries discard directory components; others preserve them. Encoding is useful only if a later layer decodes it. Do not assume the name displayed in the UI is the filesystem name.

Prove a benign marker write outside the intended upload directory before reasoning about config overwrite. Arbitrary overwrite also requires writable paths and a filename the application actually preserves.

## 6. Other useful upload chains

| Surface | Follow-up |
| --- | --- |
| SVG preview | Test stored browser context/XSS or server-side [XXE](../xxe/) according to processing |
| HTML attachment | Is it served inline under the application origin or forced as download? |
| ZIP import | Inspect member path traversal and extraction root; reading a ZIP is not extraction |
| Avatar/document IDs | Test ownership when reading, replacing and deleting files |
| External image import | Follow [SSRF](../ssrf/) flow |
| Conversion command | Follow [command injection](../command-injection/) flow |
| Uploaded template | Does the application actually render it? Then inspect [SSTI](../ssti/) |

Serving an SVG under an isolated storage origin or as an image does not automatically produce application-origin script execution.

## 7. Execution fails: decision table

| Observation | Likely next question |
| --- | --- |
| Accepted, retrieval `404` | Private storage, renamed file, processing queue or wrong URL? |
| Accepted, bytes changed | Image/document sanitization or conversion? |
| Accepted, source/download returned | Static handler or download controller? |
| `403` only for executable names | Directory execution rule or edge extension block? |
| Upload works briefly | Temporary storage before validation or asynchronous cleanup? |
| Same name replaces old file | Is name collision intentional, and does ownership get checked? |

Inspect the actual retrieval response rather than the upload success toast. Use returned IDs and application routes before guessing paths.

References: [PHP upload handling](https://www.php.net/manual/en/features.file-upload.php), [PortSwigger upload vulnerability workflow](https://portswigger.net/web-security/file-upload).
