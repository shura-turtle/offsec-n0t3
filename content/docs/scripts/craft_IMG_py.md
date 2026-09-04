---
title: "Craft Img Py"
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
from PIL import Image, ImageDraw

# Create a 400x300 white image
img = Image.new("RGB", (400, 300), "white")

# Draw something on it
draw = ImageDraw.Draw(img)
draw.rectangle((50, 50, 350, 250), fill="skyblue")
draw.text((120, 130), "Hello JPG!", fill="black")

# Save as JPG
img.save("example.jpg", "JPEG")

print("Created example.jpg")
```
