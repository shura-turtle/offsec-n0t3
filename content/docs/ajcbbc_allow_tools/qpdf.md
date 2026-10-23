---
title: "qpdf"
weight: 26
bookToc: true
---

**Use for:** PDF structure, decompressed objects, encryption and attachments.  
**Run in:** WSL.

## Check the document

```bash
qpdf --check challenge.pdf
qpdf --show-encryption challenge.pdf
qpdf --show-npages challenge.pdf
qpdf --show-pages challenge.pdf
```

## Make objects easier to read

```bash
# Produces a separate PDF with readable object structure
qpdf --qdf --object-streams=disable challenge.pdf readable.pdf
strings -a readable.pdf | grep -iE 'flag|secret|JavaScript|EmbeddedFile'
```

This is structural inspection, not guaranteed text extraction. Use pdftotext for normal page text.

## Extract an attachment

```bash
qpdf --list-attachments challenge.pdf

# Use the exact key reported above; it may differ from the filename
qpdf --show-attachment='attachment-key' challenge.pdf > attachment.bin
```

## Inspect and extract a stream object

```bash
# Replace 12 with the relevant object number
qpdf --show-object=12 challenge.pdf
qpdf --show-object=12 --filtered-stream-data challenge.pdf > stream.bin
```

`--filtered-stream-data` decodes supported stream filters; the result may still be binary.

## Decrypt with a supplied password

```bash
qpdf --password='supplied-password' --decrypt challenge.pdf decrypted.pdf
```

## Gotchas

- Write to a new file to preserve the challenge artifact.
- Repairing/rebuilding can discard evidence from older PDF revisions.
- Object numbers and attachment keys are document specific.

## Flags explained

| Flag | Meaning |
| --- | --- |
| `--check` | Check PDF structure and report problems |
| `--show-encryption` | Describe document encryption settings |
| `--show-npages` | Print the page count |
| `--show-pages` | List page and content-stream object references |
| `--qdf` | Write a form intended for easier inspection/editing |
| `--object-streams=disable` | Store objects outside compressed object streams |
| `--list-attachments` | Print embedded attachment keys |
| `--show-attachment=KEY` | Write one attachment’s raw bytes to stdout |
| `--show-object=N` | Inspect object N |
| `--filtered-stream-data` | Emit decoded contents of the selected stream |
| `--raw-stream-data` | Emit the selected stream before filter decoding |
| `--password=VALUE` | Supply the known input password |
| `--decrypt` | Write decrypted output, when input can be opened |
| `--json` | Export supported structure as JSON |

## CTF: inspect PDF actions and embedded objects

```bash
qpdf --qdf --object-streams=disable challenge.pdf readable.pdf
grep -a -nE '/(OpenAction|JavaScript|JS|EmbeddedFiles|Filespec|URI)' readable.pdf
```

`grep -a` treats the file as text and `-n` gives lines in the rewritten file. Follow referenced objects rather than treating nearby text as belonging to the same action.

## CTF: export one identified content stream

```bash
qpdf --show-pages challenge.pdf

# Example object ID only; use the content reference printed above
qpdf --show-object=17 --filtered-stream-data challenge.pdf > page_stream.bin
xxd -l 128 page_stream.bin
strings -a page_stream.bin
```

A PDF content stream contains drawing/text operators and encoded font references. It may not read like the visible page; pdftotext performs an additional interpretation step.

## CTF: compare compressed and decoded bytes

```bash
qpdf --show-object=17 --raw-stream-data challenge.pdf > raw_stream.bin
qpdf --show-object=17 --filtered-stream-data challenge.pdf > decoded_stream.bin
```

This helps identify whether another encoding layer exists after PDF filter decoding. Both commands export only one selected stream.

## CTF: inspect the structure with jq

```bash
qpdf --json challenge.pdf > structure.json
jq 'keys' structure.json
jq -r '.. | strings | select(test("flag|secret|attachment"; "i"))' structure.json
```

JSON structure varies with the qpdf JSON version. Inspect keys before writing a filter; binary stream bytes are not guaranteed to be embedded by a basic JSON export.

## Recognize incremental revisions

PDFs can contain older objects and cross-reference revisions. A successful qpdf rewrite may retain only the resolved current structure. Preserve the original, inspect its raw bytes for prior evidence, and distinguish original offsets from rewritten offsets.

Reference: [qpdf CLI manual](https://qpdf.readthedocs.io/en/stable/cli.html).

## Related playbooks

- [PDF and document analysis](../../steganograph-expl/pdf-documents/)
