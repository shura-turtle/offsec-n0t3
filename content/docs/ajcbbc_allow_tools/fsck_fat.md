---
title: "fsck.fat (dosfstools)"
weight: 29
bookToc: true
---

**Use for:** diagnosing or repairing a FAT filesystem image.  
**Run in:** WSL. Despite the tournament category, this is a filesystem tool.

## Diagnose without changes

```bash
# Use a FAT filesystem image, not an entire partitioned disk
fsck.fat -n -v fat.img

# Also list processed paths
fsck.fat -n -l fat.img
```

`-n` performs a noninteractive check without writing. Keep this option for initial triage.

## Walkthrough: damaged FAT challenge

1. Identify whether the artifact contains a partition table with `mmls`.
2. If partitioned, extract the FAT partition first.
3. Run the read-only check and save the diagnosis.
4. Use Sleuth Kit to inspect recoverable entries.
5. If repair is needed, do it on a copy and compare recovery results.

```bash
# Example partition boundaries only: use values from YOUR image
dd if=disk.img of=fat.img bs=512 skip=2048 count=65536 status=none
fsck.fat -n -v fat.img > fat_check.txt 2>&1

# Repair the copy interactively
cp fat.img fat_work.img
fsck.fat -r fat_work.img
```

## Gotchas

- Repair can change directory entries, cluster chains and deleted evidence.
- Confirm sector size before using `dd`; 512 is only this example’s assumption.
- Do not run against a mounted filesystem or unrelated host drive.
- For file recovery, continue with [The Sleuth Kit](../sleuth_kit/) or [Autopsy](../autopsy/).

## Flags explained

| Flag | Meaning |
| --- | --- |
| `-n` | Check without writing changes; noninteractive |
| `-v` | Show verbose diagnostic information |
| `-l` | List paths while processing |
| `-r` | Repair interactively; can modify the filesystem |

`-r` means repair here, not recursive traversal. For a forensic artifact, run read-only diagnosis first and repair only a working copy.

## Understand the supporting dd options

```bash
dd if=disk.img of=fat.img bs=512 skip=2048 count=65536 status=none
```

| Argument | Meaning |
| --- | --- |
| `if=` | Input file |
| `of=` | Output file; existing content can be overwritten |
| `bs=512` | Use 512-byte blocks |
| `skip=2048` | Skip 2048 input blocks |
| `count=65536` | Copy at most 65536 blocks |
| `status=none` | Suppress ordinary status output |

The example start byte is `512 * 2048`, not 2048 bytes. Use the actual sector size and partition boundaries.

## CTF: preserve before/after evidence

```bash
sha256sum fat.img > original_hash.txt
cp fat.img fat_work.img
fsck.fat -n -v fat_work.img > before_check.txt 2>&1
fsck.fat -r fat_work.img
fsck.fat -n -v fat_work.img > after_check.txt 2>&1
sha256sum fat_work.img > repaired_hash.txt
```

The hash difference shows the copy changed; it does not establish which recovered bytes are original evidence. Keep recovery results from before repair too.

## Interpret common filesystem findings

| Finding | Investigation consequence |
| --- | --- |
| Lost/unreferenced cluster chain | Possible recoverable content; structure may be unclear |
| Invalid chain or cross-linked clusters | File contents may overlap or be incomplete |
| FAT copies disagree | Determine which structural interpretation is supported |
| Unexpected size/boot metadata | Wrong partition boundary or damaged metadata |

## When to stop repairing

If the objective is recovering a specific file and Sleuth Kit can already extract a valid copy, further repairs can add ambiguity. Save the recovered file, its source record and the read-only diagnosis. Repair is useful when it unlocks a necessary next step, not as a required action for every FAT image.

Reference: [dosfstools fsck.fat manual](https://github.com/dosfstools/dosfstools/blob/master/manpages/fsck.fat.8.in).
