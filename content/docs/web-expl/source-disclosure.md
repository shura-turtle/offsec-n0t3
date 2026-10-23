---
title: "08 · Source / Backup Leaks"
weight: 17
bookToc: true
---

# Source, Backup, and Debug Leaks

**Start here before injection.** A leaked route, schema, secret, or source map can turn guessing into a direct source audit.

## 1. Compare against a nonexistent path

Request a deliberately nonexistent path first. Some applications return the same SPA shell or login page for everything. A `200` alone does not establish that a backup exists.

Check challenge-indicated names and linked resources:

```text
/robots.txt
/sitemap.xml
/.well-known/security.txt
/app.js
/app.js.map
/static/js/main.js.map
/.git/HEAD
/.git/config
/index.php.bak
/index.php~
/.index.php.swp
/backup.zip
/source
```

Do not assume every listed path is present. Follow actual asset names, comments, source map annotations, and error paths rather than trying arbitrary filenames indefinitely.

## 2. Interpret the response

| Evidence | Meaning | Next action |
| --- | --- | --- |
| `ref: refs/heads/...` from `.git/HEAD` | Exposed Git metadata | Check accessible refs/objects; source may be recoverable |
| `[core]` / `[remote ...]` config | Git config disclosure | Inspect relevant repo hints; don't assume object listing |
| Source text instead of executed PHP | Backup or source delivery | Trace request inputs to sinks |
| Source map JSON `sources`, `sourcesContent` | Browser source reconstruction | Read routes, hidden fields, API URLs |
| `PK` / `application/zip` | Possible ZIP | Verify magic and list archive before interpreting |
| Debug stack trace | Code paths and component versions | Identify exact handler, query, template, environment |
| Same HTML as random path | Catch-all / fallback | Not confirmed disclosure |

Git packfiles, loose objects, refs, and ignored/untracked files are different. Exposed `.git/HEAD` does not guarantee every source file is downloadable, and downloading a working tree does not prove access to deleted commits.

## 3. Audit recovered source

```text
routes → input names → validators → transformations → sink
database init → table names → seed rows → hidden predicates
Dockerfile → working directory → flag path → service user
templates → escaped vs raw output → second render
auth → server session vs client claims → object ownership
```

Read dependency lockfiles for exact versions. A version string suggests research, not a proven vulnerability. Inspect configuration and reachable code paths before applying a known payload.

## 4. Debug pages

| Component | Things worth reading | What not to assume |
| --- | --- | --- |
| Flask / Werkzeug | Stack frame locals, source lines, app paths | Debug console is not automatically unlocked |
| Django | Routes, settings names, error SQL | DEBUG does not guarantee arbitrary code execution |
| PHP | Include paths, warning source locations | A warning is not necessarily a file read |
| Node | Stack paths, source files, package names | `SyntaxError` is not itself a NoSQL fingerprint |
| Java | Class names, template engine, binding errors | Expression evaluation depends on the exact sink |

## 5. Map to tools

- [Chrome](../../ajcbbc_allow_tools/google_chrome/): DevTools Sources/Network and pretty printing.
- [Burp](../../ajcbbc_allow_tools/burp_suite_community/): replay source/backup requests and compare responses.
- [jq](../../ajcbbc_allow_tools/jq/): inspect source map JSON.
- [strings](../../ajcbbc_allow_tools/strings/): quick inspection of recovered files.

**Next:** [SQLi](../sqli/) · [SSTI](../ssti/) · [PHP quirks](../php-quirks/) · [Auth](../auth-idor/)

Reference: [PortSwigger information disclosure](https://portswigger.net/web-security/information-disclosure).
