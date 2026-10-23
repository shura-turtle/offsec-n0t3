---
title: "The Sleuth Kit"
weight: 23
bookToc: true
---

**Use for:** disk partitions, filesystem records and deleted file recovery.  
**Run in:** WSL. [Autopsy](../autopsy/) provides a Windows GUI workflow.

## Locate the filesystem

```bash
# Find partition start sectors
mmls disk.img

# Example start sector: replace 2048 with YOUR partition's start
fsstat -o 2048 disk.img
```

`-o` is a sector offset, not a byte offset. For a filesystem-only image, omit `-o`. Confirm sector size from the image/tool output; `-b` can specify it when needed.

## List current and deleted entries

```bash
fls -r -p -o 2048 disk.img > file_listing.txt
fls -r -d -p -o 2048 disk.img > deleted_listing.txt
grep -niE 'flag|secret|password' file_listing.txt
```

## Recover a selected entry

```bash
# Replace 12345 with the metadata address printed by fls
istat -o 2048 disk.img 12345
icat -o 2048 disk.img 12345 > recovered.bin

# Attempt deleted-file recovery using its listed metadata address
icat -r -o 2048 disk.img 12345 > recovered_deleted.bin
```

On NTFS, a listed address can include attribute components such as `12345-128-1`; preserve the complete address.

## Build a filesystem timeline

```bash
fls -r -m / -o 2048 disk.img > bodyfile.txt
mactime -b bodyfile.txt -d > timeline.csv
```

## Gotchas

- Wrong partition offset produces misleading errors.
- Deleted content may be overwritten or incomplete.
- Extract evidence into a separate output directory.

## Flags explained by command

| Tool / option | Meaning |
| --- | --- |
| `fls -r` | Recurse through directories; deleted directories have recovery limitations |
| `fls -p` | Show full paths |
| `fls -d` | Show deleted entries only |
| `fls -m /` | Emit bodyfile timeline records using `/` as the mount-point prefix |
| `-o N` on fls/icat/fsstat/istat | Filesystem starts at sector N |
| `-b N` on supporting tools | Device sector size in bytes |
| `icat -r` | Attempt deleted-file recovery |
| `mactime -b FILE` | Read a bodyfile; here `-b` does NOT mean sector size |
| `mactime -d` | Write comma-delimited output |
| `tsk_recover -e` | Export allocated and unallocated files |

## CTF: filesystem-only versus whole-disk image

```bash
mmls disk.img
fsstat filesystem.img
fsstat -o 2048 disk.img
```

Choose the latter offset from the partition listing, not from a copied example. A filesystem-only image can be valid even if `mmls` finds no partition table.

## CTF: recover all available files into a new directory

```bash
mkdir -p recovered_all
tsk_recover -e -o 2048 disk.img recovered_all/
```

Without `-e`, tsk_recover normally focuses on unallocated files. Broad extraction can be large; use `fls`/`icat` for a targeted candidate when time or space is limited.

## CTF: inspect an NTFS alternate stream

Read the full metadata/attribute address from `fls`; do not keep only the first numeric component.

```bash
# Example NTFS attribute address from a listing
icat -o 2048 disk.img 42-128-3 > named_stream.bin
```

The address is specific to the image. Verify name, type and length with `istat` and the directory listing.

## CTF: produce a timeline and filter a time window

```bash
fls -r -m / -o 2048 disk.img > bodyfile.txt
mactime -b bodyfile.txt -d > timeline.csv
grep -iE 'flag|secret|Downloads|Desktop' timeline.csv
```

Understand the filesystem’s timestamp semantics and selected timezone before comparing with event logs or packet timestamps. A changed filename does not necessarily imply the file’s contents changed at the same time.

## Interpret directory listing evidence

The metadata address identifies the file record/attribute used for extraction. A deleted marker indicates directory-entry status, not guaranteed recoverable data. If clusters were reused, a successful `icat` can still return unrelated or partially overwritten content.

## Recovery record

```text
image hash: <sha256>
partition start / sector size: <N> / <bytes>
filesystem: <type>
source path: <path from fls>
metadata address: <complete address>
command: <exact icat/tsk_recover invocation>
output hash and validation: <values>
```

References: [fls](https://www.sleuthkit.org/sleuthkit/man/fls.html), [icat](https://www.sleuthkit.org/sleuthkit/man/icat.html), [tsk_recover](https://www.sleuthkit.org/sleuthkit/man/tsk_recover.html), [mactime](https://www.sleuthkit.org/sleuthkit/man/mactime.html).

## Related playbooks

- [File signatures and bounded carving](../../steganograph-expl/archives-carving/)
- [Artifact triage](../../steganograph-expl/triage/)
