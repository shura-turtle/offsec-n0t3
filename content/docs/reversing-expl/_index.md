---
title: "Reverse Engineering"
weight: -7
bookToc: true
---

# Reverse Engineering Field Notes

**Identify the format. Find the real check. Recover the exact bytes. Verify them in the original program.**

Offline manual workflows and reusable Python for authorized CTF binaries. Every tool link below leads to the existing supplied-tool notes. Optional extensions and Z3 are separate from that list; inclusion here does not establish tournament permission.

![Reversing decision flow: triage, stored/checked/computed classification, model and original-program verification](/images/reversing/workflow.svg)

Original workflow diagram, not a captured tool screenshot.

## Choose by evidence

| What you see | Start here | Next move |
| --- | --- | --- |
| Unknown file / wrong architecture | [Triage](triage/) | Format, ABI and runnable status |
| Native binary, no source | [Ghidra cheatsheet](ghidra-cheatsheet/) | Strings → references → check function |
| Complex native logic | [Static analysis](static-analysis/) | Types, widths, branch and data flow |
| Decrypted data only in memory | [Dynamic debugging](dynamic-debugging/) | Break after transform, dump exact length |
| UTF-16 / hex / XOR array | [Strings and encodings](strings-encodings/) | Extract bytes, confirm decoding layer |
| XOR/rotate/hash/VM | [Crypto and obfuscation](crypto-obfuscation/) | Recognize then model exact operations |
| Managed Windows executable | [.NET](dotnet/) | dnSpyEx metadata, resources and IL |
| Need repeatable byte operations | [Python snippets](python-snippets/) | Download stdlib tools and test fixtures |
| Need stronger Ghidra tooling | [Ghidra plugins](ghidra-plugins/) | Built-ins first, explicit compatibility checks |

## Pick the right tool

| Task | Supplied-tool notes |
| --- | --- |
| Native static analysis | [Ghidra](../ajcbbc_allow_tools/ghidra/), [objdump](../ajcbbc_allow_tools/objdump/) |
| Linux runtime | [GDB](../ajcbbc_allow_tools/gdb/) |
| Windows native runtime | [x64dbg](../ajcbbc_allow_tools/x64dbg/) |
| Windows managed code | [dnSpyEx](../ajcbbc_allow_tools/dnspyex/) |
| Bytes, offsets, patches | [HxD](../ajcbbc_allow_tools/hxd/), [xxd](../ajcbbc_allow_tools/xxd/) |
| Assembly experiments | [LLVM MC](../ajcbbc_allow_tools/llvm_mc/) |
| Data transforms | [Python](../ajcbbc_allow_tools/python3/), [CyberChef](../ajcbbc_allow_tools/cyberchef/) |
| Static text | [strings](../ajcbbc_allow_tools/strings/) |

## Three flag shapes

- **Stored:** plaintext/resource/encoded bytes already exist. Follow references and verify the live printing path; decoys are common.
- **Checked:** input is transformed and compared. Recover preprocessing, transforms, constants and exact length; invert or solve the resulting model.
- **Computed:** input/state drives decryption or flag construction. A patched “success” branch may still produce garbage because the decryption key depends on valid state.

## Keep a small evidence card

```text
SHA-256 / original filename:
Format / architecture / ABI:
Native tool / managed tool:
Input source and newline rules:
Success and failure references:
Check function / address / RVA:
Expected data address and length:
Transform widths / signedness / byte order:
Candidate / forward-model result:
Original unpatched program result:
```

A patched success popup is a useful experiment, not proof that the recovered input is correct. Finish by running the candidate through the original unmodified validator when the challenge permits execution.
