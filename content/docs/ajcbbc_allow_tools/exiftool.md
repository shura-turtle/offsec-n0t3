---
title: "ExifTool"
weight: 14
bookToc: true
---

**Use for:** image/document metadata, GPS coordinates, comments and thumbnails.  
**Run in:** WSL.

## Quick commands

```bash
exiftool image.jpg                            # Standard metadata overview
exiftool -a -u -g1 image.jpg                  # Include duplicates, unknowns and groups
exiftool -s -FileType -MIMEType image.jpg      # Compare detected type with extension
exiftool -GPSLatitude -GPSLongitude -n image.jpg  # Numeric location clues
exiftool -Comment -Artist -Author -Description image.jpg  # Creator and hidden notes
exiftool -json image.jpg > metadata.json      # Save machine-readable metadata
```

`-a`: duplicate tags. `-u`: unknown tags. `-g1`: group names. `-n`: numeric values without print conversion.

## Walkthrough: investigate a photo

1. Dump all metadata with `-a -u -g1`.
2. Check location, creator, software, timestamps and comments.
3. Compare metadata with visible clues.
4. Extract a thumbnail if the tag exists.

```bash
exiftool -b -ThumbnailImage image.jpg > thumbnail.jpg
exiftool -b -PreviewImage image.jpg > preview.jpg
```

An absent thumbnail/preview tag can produce an empty output file.

## Batch inspection

```bash
exiftool -r -ext jpg -ext png -csv photos/ > photos_metadata.csv
```

## Gotchas

- Metadata can be edited; treat it as a clue to corroborate.
- A leading minus option reads a tag; `-TAG=value` writes metadata.
- GPS reference tags matter when interpreting latitude/longitude manually.
- Check timezone information before correlating timestamps.

## Flags explained

| Flag | Meaning |
| --- | --- |
| `-a` | Show duplicate tags instead of suppressing them |
| `-u` | Include unknown tags that can be extracted |
| `-g1` | Group by metadata location/family 1 |
| `-s` | Print short tag names |
| `-n` | Print underlying numeric values without normal display conversion |
| `-b` | Emit raw/binary tag contents |
| `-json` | Output JSON for scripting |
| `-csv` | Output a CSV table |
| `-r` | Recurse into subdirectories |
| `-ext jpg` | Restrict processing to a filename extension; repeat for more |

`-Comment` reads that tag. `-Comment=VALUE` writes it. This difference matters when preserving an artifact.

## CTF: collect time clues with tag groups

```bash
# time:all requests tags in the time group; -a keeps duplicates
exiftool -a -G1 -s -time:all photo.jpg

# Group all metadata while keeping the original tag names
exiftool -a -u -G1 -s challenge.pdf > grouped_metadata.txt
```

Filesystem dates, EXIF capture dates and application edit dates are different observations. A missing timezone means you cannot directly assume UTC.

## CTF: inspect GPS without losing hemisphere information

```bash
exiftool -GPSLatitude -GPSLatitudeRef -GPSLongitude -GPSLongitudeRef photo.jpg
exiftool -GPSLatitude -GPSLongitude -n photo.jpg
```

Corroborate coordinates with visible landmarks, challenge context or another supplied artifact. Metadata can be deliberately misleading.

## CTF: inspect embedded text and alternate metadata

```bash
exiftool -a -u -G1 image.png | grep -iE 'comment|description|author|software|warning'
exiftool -XMP:all -IPTC:all image.jpg
```

PNG textual chunks and XMP fields can contain clues absent from standard EXIF summaries. A warning can reveal a malformed structure worth inspecting with HxD/xxd.

## CTF: correlate a directory of photos

```bash
exiftool -r -ext jpg -csv -FileName -DateTimeOriginal \
  -GPSLatitude -GPSLongitude -n photos/ > locations.csv
```

Use filenames plus timestamps to reconstruct a plausible sequence. A missing coordinate or date is not zero; keep missing values explicit in later processing.

## Avoid accidental binary corruption

Use `-b` output with binary-preserving shell redirection in WSL. Do not paste thumbnail bytes through a text editor. Check that the output file is nonempty and starts with the expected signature before continuing.

Reference: [ExifTool command documentation](https://github.com/exiftool/exiftool/blob/master/exiftool) and [official site](https://exiftool.org/).
