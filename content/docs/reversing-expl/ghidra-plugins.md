---
title: "Ghidra Plugins · Built-ins & Offline Extras"
weight: 3
bookToc: true
---

# Ghidra plugins and offline extensions

**Start with the supplied installation.** Built-in analysis can cover most CTF reversing. External extensions are optional tools with their own compatibility and event-approval status. This page contains no AI/MCP assistant extensions.

## 1. Plugin, extension and script are different

| Type | Meaning | Typical entry point |
| --- | --- | --- |
| Built-in plugin | Feature already bundled with Ghidra | File → Configure in a tool; Window panels |
| Extension | Extra packaged module, often Java | Project Manager → File → Install Extensions |
| Script | A local Java/Python automation file | Window → Script Manager and script directories |
| Standalone companion | Separate program operating on sample/output | Its own executable and dependencies |

Menu labels differ slightly across releases. A missing feature may only need enabling in the current tool configuration. Do not download a third-party package to obtain a panel already bundled with Ghidra.

## 2. Useful bundled features

| Feature | Good use | Limitation |
| --- | --- | --- |
| Function ID | Recognize known compiled library functions | Needs compatible signatures; optimized variants may differ |
| Function Graph | Visualize basic-block branches | Control-flow model can be incomplete for indirect jumps |
| Function Call Trees | Find callers and callees | Indirect calls may be unresolved |
| Data Type Manager | Apply structures, enums and headers | Wrong types can mislead decompilation |
| Version Tracking | Transfer validated matches/annotations between two related programs | Matches need review; differences can invalidate assumptions |
| BSim | Similarity search against a prepared corpus | Requires signature/database setup; similarity is not identity |
| Debugger tool | Connect supported backends and correlate static/dynamic state | Backend setup and supported OS/architecture vary |
| Script Manager | Repetitive local extraction and annotation | Scripts can change the program database |

### Version Tracking workflow

Import and analyze both known and unknown builds, create a tracking session, select source/destination and run a suitable correlator. Review proposed matches before applying names/types. Confirm both call structure and important constants; a same-looking function can have a changed check.

### BSim workflow

Choose a corpus you already possess and are permitted to use, generate/ingest function signatures using the installed version's documentation, then query interesting functions. Use the result as a lead to known implementations. It is excessive setup for a tiny one-off byte validator with no relevant corpus.

## 3. Optional non-AI companions

These are **not established as allowed by the supplied tournament list**. Prepare them only if your event permits them; the manual workflow remains usable without them.

| Project | Purpose | Compatibility/installation notes |
| --- | --- | --- |
| [ret-sync](https://github.com/bootleg/ret-sync) | Synchronize debugger location with Ghidra/other disassemblers | Requires both debugger-side and disassembler-side components; match release/backend and address mapping |
| [FLOSS](https://github.com/mandiant/flare-floss) | Recover several classes of obfuscated strings | Standalone companion, not a stock Ghidra plugin; supported formats/architectures and runtime requirements apply |
| [capa](https://github.com/mandiant/capa) | Identify capabilities from rule matches | Standalone rule-based companion; prepare matching rules and supported analyzer backend offline |
| [Ghidra C++ Class Analyzer](https://github.com/astrelsky/Ghidra-Cpp-Class-Analyzer) | Historical RTTI/class reconstruction extension | Repository archived in 2023; no assumption it builds against your current Ghidra |

There is no universal current extension zip that works across all Ghidra releases. For each candidate, record the exact release/tag, intended Ghidra version, Java requirements, dependency list and install method from its own README. An archived extension is a reference candidate rather than a default installation recommendation.

## 4. Installing a packaged extension

1. Read the extension's compatibility matrix/release notes. Record **your actual Ghidra version** from Help → About.
2. Use the release built for that version, or build source using the documented matching Ghidra development setup.
3. In Project Manager, open **File → Install Extensions**, select the package using the add control, enable it and restart if requested.
4. Open the analysis tool and enable its plugin/panel in tool configuration if the extension requires that step.
5. Test on a small known local executable before the event, then preserve the package and dependencies offline.

A generic Gradle extension build often uses the following shape; it applies only when the repository explicitly provides that build configuration:

```bash
gradle -PGHIDRA_INSTALL_DIR=/path/to/exact-ghidra-install buildExtension
```

Do not rename a zip or edit `extension.properties` to pretend a different version is compatible. Successful loading alone is weaker than successful analysis on a fixture.

## 5. Running local scripts

Add a scripts directory through Script Manager's directory controls. Refresh, inspect the script source and select the correct runtime. The classic Ghidra Python integration is Jython-based; PyGhidra is a separate CPython integration with its own setup. A Python 3 script using `pathlib`, f-strings or third-party CPython packages does not automatically run as a classic Jython script.

The downloadable scripts in [Python snippets](../python-snippets/) are **ordinary command-line Python 3**, not Ghidra scripts. Export bytes first and run them outside Ghidra.

## 6. Debugger synchronization caveats

For ret-sync or native Ghidra Debugger workflows, write down:

```text
Static image base:
Runtime module base:
RVA = static address - static image base:
Runtime address = runtime module base + RVA:
Debugger backend / architecture:
Extension build and Ghidra version:
```

ASLR changes runtime bases. A correct plugin connection with an incorrect module mapping highlights the wrong code. On Linux, mappings differ per segment; on Windows, record the module load base. Confirm one known instruction's bytes at the correlated address.

## 7. Pre-event offline check

Open a test program, show one useful result, disconnect network and reopen the project. Ensure local help, rule bundles and signature databases remain available. Document the matching manual fallback: string references, library constants, structures and breakpoints are still useful without extensions.

## References

[Ghidra distribution/source](https://github.com/NationalSecurityAgency/ghidra), [Version Tracking source/docs](https://github.com/NationalSecurityAgency/ghidra/tree/master/Ghidra/Features/VersionTracking), [BSim feature](https://github.com/NationalSecurityAgency/ghidra/tree/master/Ghidra/Features/BSim), [ret-sync installation and backend docs](https://github.com/bootleg/ret-sync).
