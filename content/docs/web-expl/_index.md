---
title: "Web Exploitation"
weight: -10
bookCollapseSection: true
bookToc: true
description: "Manual CTF playbooks: first probe, proof, fingerprint, payload, next step."
---

# Web Exploitation Field Notes

**Start with a signal. Confirm it. Identify the parser. Then choose the payload.**

Manual reference for CTF challenges and labs. Payloads are ready to adapt in a browser, Burp Repeater, or a request editor. No generated solver is needed to follow the workflows. Availability of notes and tools during your event depends on its rules.

## Pick your starting point

| What you have / what you see | Open this | First question |
| --- | --- | --- |
| A new URL or source archive | [First 10 minutes](methodology/) | Where does each input go? |
| Exposed backups, Git files, debug traces | [Source / backup leaks](source-disclosure/) | Can source reveal the actual sink and flag location? |
| Search, login, sorting, numeric ID | [SQL injection](sqli/) | Can I change a query condition? |
| Confirmed SQLi, unknown database | [Database fingerprinting](sqli/#3-identify-the-database) | Which engine actually executed the query? |
| MySQL / MariaDB | [MySQL](sqli-mysql/) | Current schema → tables → columns → data |
| PostgreSQL | [PostgreSQL](sqli-postgresql/) | Current schema → catalog → text casts |
| SQLite | [SQLite](sqli-sqlite/) | Read sqlite_schema and CREATE TABLE definitions |
| Microsoft SQL Server | [SQL Server](sqli-mssql/) | DB_NAME → sys.tables → sys.columns |
| Oracle | [Oracle](sqli-oracle/) | DUAL → USER_TABLES → USER_TAB_COLUMNS |
| SQLi confirmed, no rows displayed | [Blind / error SQLi](sqli-blind/) | What reliable true/false signal exists? |
| A greeting / preview evaluates expressions | [SSTI](ssti/) | Server evaluation or browser rendering? Which engine? |
| JSON login, MongoDB operators | [NoSQL injection](nosqli/) | Does the app accept an object where it expects a string? |
| Input becomes HTML or JavaScript | [XSS](xss/) | Which exact browser context contains the input? |
| Ping, convert, archive, DNS tools | [Command injection](command-injection/) | Shell string or direct argument list? |
| Filename, download, language/include | [Traversal / LFI](lfi-traversal/) | Can I read a known file outside the intended directory? |
| URL fetcher, webhook, PDF generator | [SSRF](ssrf/) | Which request does the server itself make? |
| XML, SOAP, SVG upload | [XXE](xxe/) | Does the parser resolve entities? |
| Upload form / attachment API | [File upload](file-upload/) | Accepted, stored, served, interpreted: which stages work? |
| Object IDs, roles, reset links | [Auth / IDOR](auth-idor/) | Does the server enforce ownership and workflow state? |
| Three-part bearer token | [JWT](jwt/) | What is verified, with which key and algorithm? |
| Serialized cookie / import | [Deserialization](deserialization/) | Which format and which server-side classes? |
| Deep object merge / JS config | [Prototype pollution](prototype-pollution/) | Can input alter inherited properties? |
| GraphQL endpoint | [GraphQL](graphql/) | Schema, resolver authorization, hidden arguments |
| Cookie-authenticated state changes | [CSRF / CORS](csrf-cors/) | Can another origin send or read this request? |
| OAuth login / account linking | [OAuth](oauth/) | Are callback, identity, state, and session bound correctly? |
| Live socket messages | [WebSockets](websockets/) | Which message changes state, and when is completion reported? |
| Coupon, payment, repeated claim | [Business logic / races](business-logic/) | Which invariant should hold after two requests? |
| Proxy, cache, suspicious framing | [HTTP / cache issues](http-cache/) | Do two HTTP components disagree? |
| PHP loose checks, arrays, hashes | [PHP quirks](php-quirks/) | Which types and PHP version participate in the check? |
| Directory/XML query syntax | [LDAP / XPath](ldap-xpath/) | What grammar and boolean oracle does the sink expose? |
| Redirect / return URL | [Open redirect](open-redirect/) | What hostname does the consuming parser actually use? |
| Blocked words / changed payloads | [Encoding / filters](encoding-filters/) | What bytes reach the final parser? |
| Need prepared Python helpers | [Reusable snippets](python-snippets/) | Byte transforms, JWT, or a confirmed boolean oracle? |

## The loop for every technique

```text
Baseline request
  → one small probe
  → matching negative control
  → repeat the difference
  → fingerprint the parser / engine
  → select the matching payload
  → enumerate actual names / paths
  → read the challenge result
```

An error is a clue; repeatable controlled behavior is evidence. A `200 OK`, accepted upload, or login redirect alone does not prove success.

## Payload notation

| Notation | Meaning |
| --- | --- |
| `ctf.invalid` | Placeholder challenge host; replace it |
| `YOUR-LAB-HOST` | Your permitted callback host, if callbacks are part of the challenge |
| `users`, `flags`, `flag`, `/flag.txt` | Example names; enumerate actual names first |
| `-- -` | SQL line comment with a trailing space after the two dashes |
| `NULL,NULL,EXPR` | Example three-column UNION; adapt count, types, and reflected position |
| `1' ... -- -` | Complete example input for a single-quoted query value |
| `SELECT ...` in an engine page | Standalone query fragment; insert it into your confirmed injection |
| `%XX` | URL-encoded bytes; do not encode twice unless two decoding stages exist |

Many pages deliberately show **raw payloads**. In Burp's decoded parameter editor, enter the raw payload; in an actual URL/form body, encode transport-sensitive characters. JSON, URL forms, HTML, and shell quoting are different layers. See [encoding](encoding-filters/).

## Keep a tiny evidence record

```text
Route / method:
Parameter and content type:
Baseline response:
True probe / false probe:
Observed difference:
Engine evidence:
Working payload:
Next step / result:
```

The reference links at the end of each page are optional further reading. The workflow and payloads are included here for offline use. Examples are not a claim that every payload works on every version or has been tested against your event's environment.

## Tool map and other artifact types

[Burp](../ajcbbc_allow_tools/burp_suite_community/) → capture/replay exact requests. [Chrome](../ajcbbc_allow_tools/google_chrome/) → inspect DOM, network and storage. [CyberChef recipes](../tools-cheatsheet/cyberchef-cheatsheet/) → decode evidence. [Python snippets](python-snippets/) → repeat confirmed operations.

[Network](../network-expl/) · [Steganography](../steganograph-expl/) · [Reversing](../reversing-expl/) · [All 39 tools](../tools-cheatsheet/approved-tools-map/).
