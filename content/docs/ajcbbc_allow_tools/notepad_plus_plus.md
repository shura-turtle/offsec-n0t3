---
title: "Notepad++"
weight: 37
bookToc: true
---

**Use for:** source/log inspection, regular expression searches and small text edits.  
**Run in:** Windows GUI.

## Open an artifact from PowerShell

```powershell
# If installed in the default location
& 'C:\Program Files\Notepad++\notepad++.exe' 'C:\CTF\output.txt'
```

## Useful keys

| Action | Key |
| --- | --- |
| Find | Ctrl+F |
| Replace | Ctrl+H |
| Find in files | Ctrl+Shift+F |
| Go to line | Ctrl+G |

## CTF: search a text dump

1. Open the extracted text or source file.
2. **Ctrl+F → Search Mode → Regular expression**.
3. Search a pattern below.
4. Choose **Find All in Current Document** for a list of matches.

```regex
flag\{[^}\r\n]+\}
https?://[^\s"'<>]+
(?i)(password|secret|token|api[_-]?key)
```

Replace `flag` with the tournament’s actual prefix.

## Search many files

**Ctrl+Shift+F** → set the directory and a filename filter such as `*.py *.js *.txt` → enter a keyword → **Find All**. Open each hit with its file/line context.

## Fix text representation

Use **View → Show Symbol** for invisible whitespace, **Edit → EOL Conversion** for line endings, and the **Encoding** menu when the supplied text encoding is known.

## Gotchas

- Choose Normal, Extended or Regular expression mode deliberately.
- Encoding conversion changes bytes; preserve the original artifact.
- Use HxD/xxd for binary edits.
- Notepad++ plugins may not be preinstalled; these steps use built-in features.

## Understand the three search modes

| Mode | Use |
| --- | --- |
| Normal | Search literal text |
| Extended | Recognize escapes such as `\n`, `\r`, `\t` |
| Regular expression | Search patterns and capture groups |

In regex mode, `.` means one character, `*` repeats zero or more times, `+` repeats one or more times, `^` anchors the start and `$` anchors the end. Check the “. matches newline” setting before searching across lines.

## CTF: extract and label candidate values

```regex
(?i)flag\{[^}\r\n]+\}
[A-Za-z0-9+/]{24,}={0,2}
\b[0-9A-Fa-f]{32,}\b
```

The first is a flag-shaped candidate, the second a possible long Base64 string, and the third a possible hex value. The latter two deliberately overmatch; validate the candidate alphabet, length and decode result.

## CTF: search a source tree

Use Find in Files with filters such as `*.js *.py *.cs *.json`. Start with route names, visible messages, `secret`, `token` or a specific clue. A configuration example is not necessarily active configuration; inspect the caller and surrounding code.

## CTF: clean a copy of structured text

Use a regex capture group when the transformation is understood. Example: with regex mode enabled, search `^prefix:(.*)$` and replace with `$1` to keep the value after a known prefix.

Preview a small sample first. Replacements on encoded/binary material can silently destroy delimiters or padding, so keep the original.

## CTF: detect hidden whitespace

Turn on Show Symbol and inspect tabs, spaces and line endings. If the clue suggests a whitespace encoding, count and preserve the actual bytes with Python/xxd; the visual editor can normalize line endings when saved.

## CLI and parameters on this page

The launcher’s file path is a positional argument, and `&` is PowerShell’s call operator for a quoted executable path. There is no generic `-r` that makes Notepad++ recursively search; use **Find in Files** and its directory/filter controls.

## Avoid false negatives

| Search failed because… | Fix |
| --- | --- |
| Match case enabled | Disable it or use `(?i)` in regex mode |
| Only current selection searched | Clear selection-only scope |
| File type filters exclude evidence | Review filters and directory |
| Wrong encoding | Inspect bytes and reopen correctly |
| Huge/binary artifact | Extract useful text with the appropriate parser first |

Reference: [Notepad++ search manual source](https://github.com/notepad-plus-plus/npp-usermanual/blob/master/content/docs/searching.md).
