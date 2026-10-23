---
title: "pdftotext (Poppler utils)"
weight: 15
bookToc: true
---

**Use for:** extracting searchable PDF text and preserving reading layout.  
**Run in:** WSL; Poppler utilities.

## Quick commands

```bash
pdftotext -v                                  # Check the installed Poppler version
pdftotext document.pdf output.txt             # Extract normal reading-order text
pdftotext -layout document.pdf output_layout.txt  # Preserve approximate columns
pdftotext document.pdf -                      # Print text directly to the terminal
pdftotext -f 2 -l 4 document.pdf pages_2_to_4.txt  # Restrict extraction to pages 2–4
pdftotext -enc UTF-8 document.pdf output_utf8.txt  # Request a specific output encoding
```

`-` sends output to stdout. Page numbers start at 1.

## Walkthrough: search a document

```bash
pdftotext -layout challenge.pdf extracted.txt
grep -niE 'flag|secret|password|https?://' extracted.txt

# Compare reading order if columns or spacing are confusing
pdftotext challenge.pdf extracted_default.txt
```

Read the matching page in a PDF viewer to connect extracted text with the visual context.

## Password supplied by challenge

```bash
pdftotext -upw 'supplied-password' challenge.pdf output.txt
```

## Gotchas

- A scanned page may have no text layer. `pdftotext` does not perform OCR.
- Custom font encodings can make extraction incomplete or scrambled.
- Hidden text may differ from what the viewer displays.
- Embedded attachments need [qpdf](../qpdf/) or a viewer’s attachment panel.

## Flags explained

| Flag | Meaning |
| --- | --- |
| `-v` | Print the version |
| `-layout` | Preserve approximate physical spacing/columns |
| `-f N` | Start at page N, using one-based numbering |
| `-l N` | Stop at page N |
| `-enc UTF-8` | Choose output text encoding |
| `-upw PASSWORD` | Supply a known PDF user password |
| `-bbox-layout` | Emit word bounding boxes with layout information |
| `-nopgbrk` | Omit form-feed page separators |
| `-` as output filename | Write extracted text to standard output |

The first positional filename is the PDF; the second is the output. `-l` means last page here, unlike tools where it means length or list.

## CTF: compare rendered order with reading order

```bash
pdftotext challenge.pdf reading_order.txt
pdftotext -layout challenge.pdf physical_layout.txt
diff -u reading_order.txt physical_layout.txt
```

Read differences alongside the displayed page. A multi-column page, positioned letters or off-page words can change the result of simple extraction.

## CTF: locate words by coordinates

```bash
pdftotext -bbox-layout challenge.pdf word_positions.html
```

Open the generated structured output as text to inspect word coordinates. Coordinates help relate extracted words to visible positions; they do not automatically prove hidden content or reading order.

## CTF: inspect page separators and invisible characters

```bash
pdftotext -enc UTF-8 challenge.pdf extracted.txt
xxd -l 256 extracted.txt

# A second export without PDF page-break characters
pdftotext -nopgbrk challenge.pdf without_page_breaks.txt
```

If a regex fails across pages, check form-feed bytes, nonbreaking spaces and unusual Unicode characters before assuming the word is absent.

## Follow the evidence to another tool

| Extraction result | Next move |
| --- | --- |
| No selectable text | PDF Viewer and visual inspection |
| Attachment filename mentioned | qpdf attachment listing/export |
| Encoded string | CyberChef/Python, preserving exact characters |
| Text differs from visible content | qpdf objects and word positions |
| Password required | Use the challenge-provided password; inspect encryption with qpdf |

Reference: [Poppler pdftotext manual source](https://github.com/tsdgeos/poppler_mirror/blob/master/utils/pdftotext.1).

## Related playbooks

- [PDF and document analysis](../../steganograph-expl/pdf-documents/)
