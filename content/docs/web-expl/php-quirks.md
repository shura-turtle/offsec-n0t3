---
title: "PHP · Types / Hashes / Parsers"
weight: 73
bookToc: true
---

# PHP Quirks

**Read the comparison, PHP version, and input parser before choosing a trick.** Many classic PHP CTF payloads changed behavior in PHP 8.

## 1. Loose comparison and magic hashes

Vulnerable source pattern:

```php
if (md5($input) == $stored_hash) { /* challenge gate */ }
```

Two known MD5 inputs:

```text
240610708  → 0e462097431906509019562988736854
QNKCDZO    → 0e830400451993494058024219903391
```

Both digests look like numeric scientific notation for zero. Comparing those digest strings using `==` can treat them as equal even on modern PHP. `===` compares string identity and prevents this particular bypass.

The exact precondition is a **loose comparison between compatible numeric-looking hashes**. A random target hash will not become zero just because your hash starts with `0e`. Not every historical `0 == "nonnumeric"` example works on PHP 8; string/number comparison rules changed.

### Manual test order

1. Find the exact hash algorithm and operator in source / hint.
2. Check whether the stored digest itself has the numeric-string shape.
3. Submit the matching known preimage for that algorithm.
4. Compare with a normal wrong input and confirm the gated response/session.

Do not use MD5 preimages for a SHA-1 gate. A hash collision, magic-hash numeric comparison, and password-hash verification are different attacks.

## 2. Arrays instead of strings

URL-encoded form bodies can produce PHP arrays:

```text
password[]=x
username[role]=admin
```

If source calls `strcmp`, `md5`, or another string function on that value, older PHP versions could emit warnings and return values that interacted badly with loose checks. Current PHP often raises `TypeError`. An array-induced exception alone is not an authentication bypass.

First compare:

```text
password=x
password[]=x
```

Inspect the error and version, then trace what the application does with the return value. Do not assume `strcmp(array,...) == 0` works everywhere.

## 3. Request parsing and duplicate keys

```text
role=user&role=admin
user.name=alice
user_name=alice
user[name]=alice
```

PHP's ordinary query parsing can normalize dots/spaces in parameter names to underscores and can interpret bracket syntax as arrays. Duplicate ordinary names commonly select the last value. A proxy, framework, JSON parser, or upstream validator may see something different.

Record all stages:

```text
raw request → proxy validation → PHP parsing → framework normalization → sink
```

Use a source-defined echo/debug endpoint if present to see what arrives. JSON bodies parsed with `json_decode` are not automatically parsed like `$_GET` / `$_POST`.

## 4. Stream wrappers and file operations

For a PHP file-read/include sink:

```text
php://filter/read=convert.base64-encode/resource=index.php
```

This can disclose readable source as Base64 without executing it in common include contexts. It does not bypass arbitrary directory allowlists, file-existence checks, suffix appending, or wrapper restrictions automatically. See [LFI](../lfi-traversal/).

`data://`, remote URLs, archive wrappers, and `php://input` each have different configuration and sink preconditions. Identify whether the code reads bytes, includes PHP, or only checks metadata.

## 5. `extract` and mass assignment

```php
extract($_GET);
```

This can create/overwrite variables depending on the `extract` flags and existing variable scope. It does not automatically overwrite variables defined afterward. Trace the order:

```text
initial role assignment → extract → role check
```

Potential probe if the source shows `$is_admin` overwritten:

```text
?is_admin=1
```

The server's actual type/comparison determines whether `1`, `true`, or a string works.

## 6. Quick offline checks

Use the [web helper snippets](../python-snippets/) to compute digests and decode Base64. Python does not reproduce PHP's loose comparison rules; test PHP behavior using the installed PHP version when available.

Tool map: [CyberChef](../../ajcbbc_allow_tools/cyberchef/) · [Python](../../ajcbbc_allow_tools/python3/) · [Burp](../../ajcbbc_allow_tools/burp_suite_community/).

Official references: [comparison operators](https://www.php.net/manual/en/language.operators.comparison.php), [parse_str](https://www.php.net/manual/en/function.parse-str.php), [extract](https://www.php.net/manual/en/function.extract.php), [stream wrappers](https://www.php.net/manual/en/wrappers.php).
