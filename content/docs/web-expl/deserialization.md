---
title: "Deserialization"
weight: 70
bookToc: true
---

# Insecure deserialization

**Identify the format and actual decoder before changing bytes.** Base64 is an encoding, not a serializer; an unsigned JSON cookie may be plain data tampering rather than object injection.

## 1. Find and unwrap the input

Look at cookies, saved preferences, cart/import blobs, queue messages and backup uploads. Save the original bytes before editing.

```text
Transport decoding → Base64/hex if present → compression if present → serialization
```

Decode only layers supported by evidence. Re-encode in reverse order after a single small change. A signature/MAC must still validate; knowing its encoding does not let you forge it.

| Prefix / clue | Candidate format | Next check |
| --- | --- | --- |
| `a:`, `O:`, `s:`, `i:` | PHP serialization | Locate `unserialize` and available classes |
| Binary `80 04` / `80 05`, Base64 often `gAS` | Python pickle protocol | Confirm `pickle.loads` or equivalent in source |
| Binary `ac ed 00 05`, Base64 often `rO0AB` | Java object serialization | Confirm `ObjectInputStream`, classpath and filtering |
| YAML tags such as `!!...` | YAML constructor | Identify library, loader class and version |
| JSON `@type` / `$type` | Type-enabled framework serializer | Identify exact library and configuration |

Prefixes are clues; arbitrary data may share them. JSON parsing itself does not execute arbitrary constructors.

## 2. PHP: controlled data modification

```text
a:2:{s:4:"user";s:5:"guest";s:5:"admin";b:0;}
a:2:{s:4:"user";s:5:"guest";s:5:"admin";b:1;}
```

If the application directly trusts this unsigned field, compare authorization behavior. A successful parse and displayed `admin=true` are weaker evidence than access to an actual protected endpoint.

### Syntax card

```text
N;                         null
b:1;                       boolean true
i:7;                       integer
d:7.5;                     double
s:5:"guest";               five-byte string
a:1:{s:4:"role";s:4:"user";} array with one key/value pair
O:4:"User":1:{s:4:"role";s:5:"admin";} object with one property
```

String/class lengths count bytes, not displayed Unicode characters. Array counts are key/value pairs. Object counts are properties. Wrong lengths often cause an offset error before application code runs.

## 3. PHP: source-guided object injection

Find entry points and magic methods:

```text
unserialize(...)
__unserialize
__wakeup
__destruct
__toString
__get / __set / __call
```

Trace input properties → magic method → file/command/template sink. A class name in a payload works only if that class is defined/autoloadable and permitted by the application's deserialization options.

For example, **only if source defines a class `Reader` with public `path` and a destructor that reads it**, a matching object is:

```text
O:6:"Reader":1:{s:4:"path";s:9:"/flag.txt";}
```

Without that exact behavior, this object does nothing useful. [PHP documents `unserialize` options and object reconstruction](https://www.php.net/manual/en/function.unserialize.php).

Private/protected property names contain NUL bytes and class prefixes. Do not type the literal characters `\0` and expect a NUL; use a byte-capable permitted editor. PHP typed properties, `__unserialize` and version differences can also invalidate an old property chain.

## 4. Python pickle: format and a manual proof

The following protocol-0 pickle resolves `builtins.str`, calls it with `71`, and returns the resulting string. The displayed line breaks are part of the pickle:

```text
cbuiltins
str
(I71
tR.
```

This is a constructor-call proof only if the sink unpickles your bytes and the returned value is observable. It may fail if the app expects a dictionary or uses a restricted unpickler. On Python 3, `builtins` is the module; Python 2 used different naming.

Do not assume a pickle byte prefix establishes execution. First confirm the actual load function and whether a signature blocks tampering. Python's [pickle documentation explains the code-execution risk](https://docs.python.org/3/library/pickle.html).

## 5. Java and YAML: prerequisites before payloads

| Stack | Required facts |
| --- | --- |
| Java native serialization | Classes/dependencies, versions, permitted types, reachable gadget entry point |
| YAML | Unsafe object-construction loader, accepted tag syntax and installed modules |
| JSON type metadata | Polymorphic typing enabled, allowed types and dangerous gadget behavior |
| Signed framework session | Signature key or verification flaw before modified data will be loaded |

A universal Java/YAML object payload is misleading: the same bytes can execute on one dependency set and merely error on another. Read supplied dependency manifests, lockfiles and source. If prebuilt gadget utilities are permitted by your event, match their chain to the exact installed classes; this page does not require a generated solver.

## 6. Troubleshooting

| Result | Check next |
| --- | --- |
| MAC/signature failure | Tampering is detected before decoding; investigate key/verification evidence |
| Offset/EOF error | Byte lengths, missing terminator, URL/Base64 encoding |
| Unknown class / incomplete class | Class loading, class allowlist, dependency mismatch |
| Object parses but no effect | Missing trigger, wrong property visibility or unreachable sink |
| Effect happens after response | Destructor, queued processing or subsequent session use |

Related: [auth and object trust](../auth-idor/), [encoding](../encoding-filters/), [uploads](../file-upload/).

Reference: [PortSwigger insecure deserialization](https://portswigger.net/web-security/deserialization).
