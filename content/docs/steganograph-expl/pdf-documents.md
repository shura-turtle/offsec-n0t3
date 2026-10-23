---
title: "PDF & Office Documents"
weight: 60
bookToc: true
---

# PDF and document hiding places

**Start with metadata, extracted text and attachments.** A document that looks blank may contain ordinary invisible text, compressed streams, prior revisions or embedded files.

## 1. First inspection

```sh
exiftool -a -u -g1 challenge.pdf
pdftotext -layout challenge.pdf layout.txt
pdftotext -raw challenge.pdf raw.txt
qpdf --check challenge.pdf
qpdf --show-encryption challenge.pdf
qpdf --show-npages challenge.pdf
```

Compare viewer appearance with both text extraction modes. The visual layout can reorder characters relative to stream order. A scanned page may have no text until OCR, while an OCR layer may contain text absent from the visible image.

Do not infer an empty PDF from empty `strings` output; page content often lives in compressed streams.

## 2. Attachments

```sh
qpdf --list-attachments challenge.pdf
qpdf --show-attachment='exact-key-from-list' challenge.pdf > attachment.bin
xxd -l 64 attachment.bin
strings -a attachment.bin
```

Use the exact attachment key. Choose a fresh output path before shell redirection. Attachment filenames and stream bytes are separate evidence; record both.

## 3. Readable object structure

```sh
qpdf --qdf --object-streams=disable challenge.pdf readable.pdf
strings -a -n 5 readable.pdf
qpdf --show-pages challenge.pdf
```

Search the derivative for names such as:

```text
/EmbeddedFiles /EmbeddedFile /Filespec /Annots
/Metadata /XMP /ActualText /Alt /OCProperties
/JavaScript /OpenAction /AA
```

These are clues, not universal executable payloads. Inspect JavaScript/macros as text rather than executing them. Optional-content layers, text clipping, white-on-white text, off-page placement and annotations can hide content from ordinary viewing.

## 4. Inspect a selected stream

```sh
qpdf --show-object=12 challenge.pdf
qpdf --show-object=12 --filtered-stream-data challenge.pdf > object12.bin
xxd -l 64 object12.bin
```

Object `12` is only an example: choose a page/content/attachment reference from your document. `--filtered-stream-data` decodes supported filters; the result can still be image bytes or other binary data. The [qpdf CLI manual](https://qpdf.readthedocs.io/en/stable/cli.html) documents object, attachment and stream inspection.

Text represented with font-specific glyph codes may need `pdftotext` and the document's font mappings; raw stream strings are not always readable text.

## 5. Incremental revisions and trailing data

PDF edits can append new objects/xref information while retaining old bytes. A repaired/rewritten PDF can discard orphaned historical data, so preserve the original for revision work.

```sh
strings -a -t x challenge.pdf
python3 file_carver.py scan challenge.pdf
```

Multiple `%%EOF` markers can be legitimate incremental revisions; the first one is not a universal extraction endpoint. A `%PDF-` hit inside a stream or attachment is not necessarily an independent complete document. Follow xref/trailer structure or carve a justified standalone attachment.

## 6. Office Open XML as ZIP

DOCX/PPTX/XLSX normally contain XML/media inside a ZIP package:

```sh
python3 -m zipfile -l document.docx
```

Inspect likely members without extracting archive-controlled paths:

```python
import zipfile
with zipfile.ZipFile("document.docx") as z:
    for name in z.namelist():
        if name.startswith(("docProps/", "word/comments", "word/media/",
                            "ppt/notesSlides/", "xl/worksheets/")):
            print(repr(name))
    item = z.getinfo("word/document.xml")
    if item.file_size > 2 * 1024 * 1024:
        raise ValueError("XML exceeds the example size limit")
    xml = z.read(item)
    print(repr(xml[:2000]))
```

| Package location | Possible clue |
| --- | --- |
| `docProps/core.xml`, `custom.xml` | Author, description, custom properties |
| `word/comments*.xml` | Comments hidden from ordinary page view |
| `word/document.xml` | Runs, hidden text, tracked insertions/deletions |
| `word/media/`, `ppt/media/` | Original embedded images/audio |
| `ppt/notesSlides/` | Speaker notes |
| `xl/worksheets/`, `sharedStrings.xml` | Hidden cells/rows/sheets and shared text |
| `*.rels` | Relationships to embedded or external resources |

Read relationship targets as evidence; do not automatically request external URLs. A workbook's visible cell can reference a shared-string index instead of storing its text inline.

## 7. Verify the layer

Extract an embedded image → run metadata/LSB workflow on that original member. Extract a text hint → preserve its exact Unicode/whitespace before copying it. A rendering can hide information that remains plainly visible in XML or the text layer.

## Troubleshooting

| Symptom | Next action |
| --- | --- |
| Text output empty | Image-only page, permissions, unsupported font/text mapping |
| Viewer and extraction disagree | Hidden/OCR text, glyph mapping or layout order |
| Rewritten file loses clue | Return to original and inspect old/orphaned bytes |
| ZIP parser rejects `.doc` | Legacy binary Office is not OOXML ZIP |
| Attachment extracts but looks random | Classify its format before decoding text |

Tools: [qpdf](../../ajcbbc_allow_tools/qpdf/), [pdftotext](../../ajcbbc_allow_tools/pdftotext/), [PDF viewer](../../ajcbbc_allow_tools/pdf_viewer/), [ExifTool](../../ajcbbc_allow_tools/exiftool/).

Next: [text/Unicode](../text-unicode/), [archive members](../archives-carving/).
