---
title: "Traversal & LFI"
weight: 61
bookToc: true
---

# Path traversal and local file inclusion

**Prove a file read before trying code execution.** A download function may only read bytes; a PHP `include` also interprets PHP code. Those are different capabilities.

## 1. First probes

Candidate parameters: `file`, `filename`, `path`, `page`, `template`, `lang`, image/download IDs that contain paths.

| Raw value | Control | Evidence |
| --- | --- | --- |
| `../../../../etc/passwd` | Same traversal to `etc/ctf-does-not-exist` | Recognizable account file vs missing-file response |
| `/etc/passwd` | `/etc/ctf-does-not-exist` | Absolute path accepted by the file operation |
| `..\..\..\Windows\win.ini` | Missing `.ini` path | Windows path traversal, if its contents return |
| `../../../../proc/self/cmdline` | Missing proc path | Linux process arguments, possibly NUL-separated |

Start with one `../`, then add depth while retaining the filename. A `200 OK` page containing a fixed error is a negative result. Match real file contents and compare a nonexistent path.

## 2. Bypass according to observed path handling

```text
../etc/passwd
../../../../etc/passwd
....//....//....//etc/passwd
..%2f..%2f..%2fetc/passwd
%2e%2e%2f%2e%2e%2fetc/passwd
%252e%252e%252f%252e%252e%252fetc/passwd
..\..\..\Windows\win.ini
```

| Variant | Required mistake |
| --- | --- |
| `....//` | A single nonrecursive removal of `../` leaves `../` behind |
| `%2e` / `%2f` | Decoding occurs after the relevant validation |
| `%252e` / `%252f` | Two decoding stages occur in the path to the sink |
| Backslashes | Downstream OS/library treats `\` as a separator |
| Absolute path | Join operation permits replacing the intended base path |

Do not infer double decoding merely because a payload contains `%25`. Observe a decoding difference or inspect source. URI routing and filesystem normalization happen at different layers.

## 3. Once arbitrary read works

Use the process and source clues to locate the challenge:

```text
/etc/passwd
/proc/self/cmdline
/proc/self/environ
/proc/self/cwd/app.py
/proc/self/cwd/package.json
/proc/self/cwd/.env
/var/www/html/index.php
/flag.txt
```

These are candidates, not guaranteed locations. `/proc/self` refers to the process performing the read. Environment data may contain NUL separators, lack expected variables, or be access-restricted. An empty environment response is not proof no secret exists.

Read routing code → imports/config → actual file/DB locations. A read primitive does not list directories unless the vulnerable endpoint supports directory listing.

## 4. PHP source disclosure with filters

If the sink accepts PHP stream wrappers:

```text
php://filter/read=convert.base64-encode/resource=index.php
php://filter/convert.base64-encode/resource=/var/www/html/config.php
php://filter/read=convert.base64-encode/resource=/flag.txt
```

Decode the returned Base64 using your permitted local decoder. Wrapping PHP source prevents `include` from executing it and returns encoded source instead. `resource=` belongs at the end; paths are resolved under the process's permissions and working directory. [PHP documents the wrapper and its filter order](https://www.php.net/manual/en/wrappers.php.php).

If the application appends `.php`, your resource becomes `index.php.php` unless the payload accounts for the suffix. First read the source and find exactly where concatenation happens.

## 5. Include-only execution paths

These need an actual include/evaluation sink. `file_get_contents()` alone returns bytes.

| Candidate | Preconditions |
| --- | --- |
| Include an uploaded PHP-bearing file | Know its local path; contents remain intact |
| Include an application log | Control a logged field; know log path; log readable |
| Include a session file | PHP session storage is file-based; session data is controllable and path known |
| `data://text/plain,...` | Wrapper accepted and required URL include settings enabled |
| `php://input` | Body reaches the sink and wrapper/include configuration allows it |
| Archive wrapper | Relevant extension exists and exact archive/member path is known |

For a lab file you control, use a fixed marker rather than a general command endpoint:

```php
<?php echo "CTF_INCLUDE_71"; ?>
```

The marker must execute, not merely appear as source. For inclusion chains, the uploaded extension may be irrelevant: `include` interprets PHP tags inside the selected file.

Remote URL inclusion depends on PHP configuration and wrapper support; successful local traversal does not establish RFI. See [PHP include behavior](https://www.php.net/manual/en/function.include.php).

## 6. Things that often waste time

| Symptom | Check |
| --- | --- |
| `/etc/passwd` works, source does not | Wrong path, suffix concatenation or permissions |
| Traversal returns an image error | App may decode/rescale the file after reading |
| Source appears blank | PHP may have executed; try Base64 filter disclosure |
| Base64 output is wrapped in HTML | Decode only the actual encoded data |
| Old `%00` payload fails | Modern PHP path APIs reject NUL; old truncation recipes are not a default |
| `phar://` reads a member but no effect | Archive access does not guarantee metadata deserialization; PHP/version and API matter |

Related: [uploads](../file-upload/), [XXE](../xxe/), [encoding](../encoding-filters/).

References: [path traversal](https://portswigger.net/web-security/file-path-traversal), [PHP conversion filters](https://www.php.net/manual/en/filters.convert.php).
