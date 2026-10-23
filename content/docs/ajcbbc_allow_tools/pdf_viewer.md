---
title: "PDF Viewer"
weight: 3
bookToc: true
---

**Use for:** visual clues, document properties, annotations, attachments.  
**Run in:** Windows PDF viewer, such as Adobe Acrobat Reader. Features vary by viewer.

## Walkthrough

1. Open a working copy of the PDF.
2. Read every page; zoom in on small text and unusual spacing.
3. Search with **Ctrl+F** for the flag prefix and challenge keywords.
4. Open **Document Properties** and record title, author and dates.
5. Inspect **Comments**, **Attachments**, and **Layers** panels when available.
6. Save relevant attachments separately and record their page/object context.

## What to inspect

| Clue | Next action |
| --- | --- |
| Text cannot be selected | Page may be an image; inspect visually |
| Copying gives different text | Compare rendered text with extracted text |
| Embedded file | Save attachment and inspect its real file type |
| Odd author/title | Check with ExifTool |
| Blank page or hidden content | Inspect objects with qpdf |

## Useful handoff

```bash
# WSL: extract selectable text, preserving layout
pdftotext -layout challenge.pdf output.txt

# Inspect PDF structure and attachment names
qpdf --check challenge.pdf
qpdf --list-attachments challenge.pdf
```

A PDF viewer does not expose every object or deleted revision. Continue with [pdftotext](../pdftotext/), [qpdf](../qpdf/), and [ExifTool](../exiftool/) when visual inspection is insufficient.

## CTF: compare visible and selectable content

Select a suspect line and copy it to a text editor. Compare with the rendered page and pdftotext output. Check whether visual spacing, hidden text, font mapping or word order explains the difference.

Record the page number and a short description of where the clue appears. A copied text string without page context is difficult to reproduce later.

## CTF: annotations and attachments

Comments can have their own author, dates and text. An attachment can contain a separate challenge artifact. Open the relevant panels, note the attachment name and export it into a new folder. If the viewer omits the panel, use qpdf’s attachment listing instead.

## CTF: layers and unusual rendering

Where supported, inspect optional layers and visibility controls. Compare zoom levels and page backgrounds when a clue suggests tiny, white or obscured text. A render difference can be a viewer limitation; verify it with another representation such as extracted text or object contents.

## CTF: metadata-driven password clue

Inspect title, author, subject and creator in Document Properties. Corroborate candidate clues with ExifTool. A visible name or date may explain a password supplied indirectly by the challenge; record the exact spelling/date format before trying it.

## Hand off to CLI with purpose and flags

```bash
# -layout preserves approximate page spacing for comparison
pdftotext -layout challenge.pdf page_text.txt

# --list-attachments prints embedded-file keys for later extraction
qpdf --list-attachments challenge.pdf

# -a retains duplicate metadata; -G1 labels its source group
exiftool -a -G1 challenge.pdf
```

The PDF viewer itself has application-specific launch arguments. The commands above belong to separate approved tools and their switches should not be mixed.

## Choose the next representation

| Question | Representation |
| --- | --- |
| What can a reader see? | Rendered page |
| What text does the PDF encode? | pdftotext / word coordinates |
| Which files are embedded? | Attachment panel / qpdf |
| Which metadata fields exist? | ExifTool |
| Which raw objects/revisions exist? | qpdf plus original-byte inspection |

Reference: [Adobe Reader](https://get.adobe.com/reader/); attachment controls depend on the selected viewer.

## Related playbooks

- [PDF and document analysis](../../steganograph-expl/pdf-documents/)
