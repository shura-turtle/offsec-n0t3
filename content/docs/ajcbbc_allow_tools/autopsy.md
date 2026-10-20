---
title: "Autopsy"
weight: 34
bookToc: true
---

**Use for:** disk image browsing, deleted files, browser history and timelines.  
**Run in:** Windows GUI. Uses The Sleuth Kit and additional ingest modules.

## Walkthrough: investigate a disk image

1. **New Case** → choose a case name and a separate output directory.
2. **Add Data Source → Disk Image or VM File** → select the artifact.
3. Set the source timezone from the challenge information.
4. Select relevant ingest modules and start processing.
5. Browse **Data Sources**, **Views**, and **Results** as results appear.
6. Search the expected flag prefix and challenge keywords.
7. Export useful files with **Extract File(s)** and record their source paths.

## Where to look

| Question | Useful view/module |
| --- | --- |
| What was deleted? | Deleted file entries / filesystem views |
| What did the user browse? | Recent Activity / web artifacts |
| Is a file extension misleading? | File Type Identification / Extension Mismatch |
| What happened at a given time? | Timeline |
| Is there hidden text or a named secret? | Keyword Search |
| Is an archive/document carrying another file? | Embedded File Extraction |

## Fast CTF workflow

Start with likely user folders, downloads and deleted entries. Add focused searches while ingest runs. Correlate a hit with its full path, timestamps and neighboring artifacts.

## Gotchas

- Some results appear only after the relevant ingest module completes.
- A keyword hit can come from metadata or an unrelated context.
- Preserve the original image and export recovered files separately.
- Use the tournament’s permitted modules; do not add AI/ML components.

For CLI recovery see [The Sleuth Kit](../sleuth_kit/).

## CTF: recover a deleted document

1. Identify the likely user/profile folder.
2. Inspect deleted filesystem entries and filename searches.
3. Preview candidates in text/hex views.
4. Extract the file to a separate directory.
5. Check whether it opens and whether its contents match the question.
6. Preserve the original path, deletion state and metadata address if available.

Recovery can be partial when clusters are overwritten. A recovered filename and a recovered complete file are different outcomes.

## CTF: reconstruct browsing activity

Use Recent Activity/web results to identify URLs, downloads and time windows. Follow a suspicious download to its filesystem artifact. Browser-history entries do not necessarily show that a user viewed all page content; correlate with other traces.

## CTF: identify a disguised file

Compare the filename extension with detected file type. Export a mismatch candidate and inspect its magic bytes in HxD/xxd. The extension mismatch module helps prioritize; a deliberate extension change does not itself explain the hidden content.

## CTF: timeline investigation

Start with a known event or narrow time window from the statement. Filter by path/artifact type, then correlate created/modified/accessed observations. Record the source timezone and whether the interface converts display times.

## Tune keyword searches

Search the actual tournament prefix, a distinctive username, a document title, a URL fragment or the name of an expected secret. Inspect hit context and source location. Whole-disk “password” hits can be numerous; narrower evidence-based queries are more useful.

## Ingest choices under tournament time limits

Choose modules based on the question: filesystem and keyword analysis for a missing document, Recent Activity for user behavior, and embedded file processing for archives/documents. You can inspect available filesystem data while longer ingest work continues.

## GUI action versus CLI flag

Autopsy’s data source settings and ingest checkboxes are GUI choices. They do not share fls/icat switches. For repeatable command-line recovery, the equivalent sequence is `mmls` → `fls` → `icat`; see [The Sleuth Kit](../sleuth_kit/) for each option’s meaning.

## What to save with a finding

```text
case / image: <name and hash>
source item: <path or artifact record>
view/search: <exact place and keyword>
time basis: <timezone and timestamp type>
exported file: <path and hash>
conclusion: <what this directly shows>
```

Reference: [Autopsy user documentation](https://sleuthkit.org/autopsy/docs/user-docs/4.22.0/).
