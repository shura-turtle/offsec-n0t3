---
title: "Packer"
date: 2026-10-26T01:53:00+06:30
bookToc: true
description: "Catch a Windows payload after allocation and unpacking, then find its embedded flag."
---

# Packer

## Original illustrated walkthrough

The pages below reproduce the supplied PDF in order, including every screenshot and code image. Select a page to open it at full size. [Download the original PDF](/writeups_ctf/reversing/packer/source.pdf).

### Page 1: Challenge setup and VirtualAlloc investigation

[![packer PDF page 1: Challenge setup and VirtualAlloc investigation](/writeups_ctf/reversing/packer/page-1.jpg)](/writeups_ctf/reversing/packer/page-1.jpg)

### Page 2: Allocation size and breakpoint placement

[![packer PDF page 2: Allocation size and breakpoint placement](/writeups_ctf/reversing/packer/page-2.jpg)](/writeups_ctf/reversing/packer/page-2.jpg)

### Page 3: Unpacked memory region and dump command

[![packer PDF page 3: Unpacked memory region and dump command](/writeups_ctf/reversing/packer/page-3.jpg)](/writeups_ctf/reversing/packer/page-3.jpg)

### Page 4: Dumped payload strings and flag

[![packer PDF page 4: Dumped payload strings and flag](/writeups_ctf/reversing/packer/page-4.jpg)](/writeups_ctf/reversing/packer/page-4.jpg)

## Searchable solve steps

The challenge PDF describes a packed Windows executable that initially displays a message box. The archive password is `csg2025`. It reports a flag inside the unpacked payload. The executable was not present with this PDF, so the debugger observations are documented source evidence rather than a fresh replay.

## 1. Find the allocation path

Open the executable in Ghidra and find its `VirtualAlloc` import and caller. The call sits near code that transforms an encrypted blob and copies it into the allocated region. The PDF gives three RVAs to watch in x64dbg: `0x102e`, `0x1079`, and `0x1095`.

At the `VirtualAlloc` call on Windows x64, `RDX` carries the second argument, allocation size. The observed value is `0x19a00`. After the call, `RAX` contains the allocated base address. Record that address and step past the routine at RVA `0x1095`; the PDF reports that the payload is written there afterward.

## 2. Dump the unpacked image

Inspect the allocated region for an `MZ` header. Dump `0x19a00` bytes starting at that header, using x64dbg's command with the actual runtime address:

```text
savedata unpacked.bin, MZ_ADDRESS, 19A00
```

`MZ_ADDRESS` is a placeholder for the address observed in the dump view. Inspect `unpacked.bin` in Ghidra and search **Defined Strings**. The PDF reports this flag in the unpacked data:

```text
CSG_FLAG{packer_daisuki}
```

The PDF does not give the original sample hash or runtime allocation address, so those values must be collected from the supplied challenge binary when repeating the steps.

