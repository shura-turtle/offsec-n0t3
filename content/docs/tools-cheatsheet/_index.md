---
title: "Tools · Visual Cheatsheets"
weight: -6
bookCollapseSection: true
bookToc: true
description: "Visual recipes, approved-tool routing, and reusable offline helpers."
---

# Tools Cheatsheet

**Which tool → where to click / what to run → what the result means → next tool.**

Your [AJCBBC allowed-tool notes](../ajcbbc_allow_tools/) remain the per-tool command reference. This collection adds visual walkthroughs, recipes, and a map from a challenge artifact to those tools.

| Need | Open |
| --- | --- |
| Decode, XOR, decompress, inspect keys/IVs | [CyberChef visual cheatsheet](cyberchef-cheatsheet/) |
| Ghidra navigation, decompiler, xrefs, types, patching | [Ghidra cheatsheet](../reversing-expl/ghidra-cheatsheet/) |
| Ghidra built-ins and optional non-AI extensions | [Ghidra plugins / extensions](../reversing-expl/ghidra-plugins/) |
| Pick from the 39 existing tool guides | [Tool-to-technique map](approved-tools-map/) |
| Download prepared Python helpers | [Snippet library](python-library/) |
| Web payload and database decision trees | [Web Exploitation](../web-expl/) |
| PCAPs, sessions, DNS, CAN, TLS | [Network Exploitation](../network-expl/) |
| Image, archive, PDF, audio, Unicode | [Steganography](../steganograph-expl/) |
| Native / .NET executable analysis | [Reversing](../reversing-expl/) |

## Use this flow during a challenge

![Artifact to evidence to tool workflow diagram](/images/tools/triage-map.svg)

*Original workflow diagram. Tool screenshots are identified separately on their guide pages.*

1. Preserve the original bytes and record their hash.
2. Identify the input format from bytes, not only its extension.
3. Choose one evidence-led operation.
4. Inspect the actual output bytes / message / file.
5. Save the recipe or command and continue only when the result supports the next step.

Examples use synthetic `flag{demo}` data. External plugins and optional Python packages are labeled separately; appearing in a note does not establish tournament approval.
