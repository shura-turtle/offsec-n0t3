---
title: "Text, Whitespace & Unicode"
weight: 70
bookToc: true
---

# Text, whitespace and Unicode channels

**Inspect code points and raw bytes before normalizing or copying text.** The displayed sentence may hide a different logical character sequence.

## 1. First inspection

```sh
xxd -l 256 message.txt
python3 text_unicode.py message.txt --limit 200
```

Download [text_unicode.py](/snippets/steganography/text_unicode.py). It uses only the standard library. Suspicious characters are printed using escaped representations and Unicode names, so BiDi controls cannot silently reorder the terminal report.

```text
index=12 U+200B escaped='\u200b' category=Cf bidi='BN' name=ZERO WIDTH SPACE total=64
```

The index counts decoded code points, **not raw byte offsets or visual columns**. The script does not strip, normalize or repair text. Invalid UTF-8 is a diagnostic failure: identify the actual encoding instead of dropping bytes with `errors="ignore"`.

## 2. Useful code-point clues

| Code point | Name / possible role |
| --- | --- |
| U+0009 | Tab: whitespace symbol distinct from space |
| U+0020 | Ordinary space |
| U+00A0 | Nonbreaking space |
| U+200B | Zero-width space |
| U+200C / U+200D | Zero-width non-joiner / joiner |
| U+2060 | Word joiner |
| U+FEFF | BOM at the start of some text; elsewhere a format character |
| U+202A–U+202E | BiDi embedding/override controls and termination |
| U+2066–U+2069 | BiDi isolation controls |
| U+FE00–U+FE0F | Variation selectors |

These have legitimate uses in language and typography. Two frequent invisible symbols are a binary-channel hypothesis, not proof of hidden data. [Unicode's BiDi algorithm](https://www.unicode.org/reports/tr9/) explains logical versus display order.

## 3. Two-symbol binary extraction

If evidence indicates U+200B means zero and U+200C means one:

```sh
python3 text_unicode.py message.txt --zero U+200B --one U+200C --output hidden.bin
xxd -l 128 hidden.bin
strings -a hidden.bin
```

The extractor ignores all other characters, preserving the order of selected symbols. By default the first selected bit becomes the output byte's most significant bit. It discards an incomplete final byte and reports the count.

Controls and alternatives:

```sh
python3 text_unicode.py message.txt --zero U+200C --one U+200B --output inverted.bin
python3 text_unicode.py message.txt --zero U+200B --one U+200C --pack lsb --output little-bits.bin
python3 text_unicode.py message.txt --zero U+200B --one U+200C --skip-bits 3 --output shifted.bin
```

Try a change because it fits an encoding hypothesis; do not treat a random short printable substring as proof. Validate a complete phrase, expected prefix, file header or checksum.

## 4. Tabs, spaces and trailing whitespace

```python
from pathlib import Path

raw = Path("message.txt").read_bytes()
for number, line in enumerate(raw.splitlines(keepends=True), 1):
    # repr shows tabs and line endings without rendering them as layout.
    print(number, repr(line))
```

If only tabs/spaces at line ends appear meaningful, isolate precisely that region rather than every space in the cover sentence:

```python
from pathlib import Path

lines = Path("message.txt").read_bytes().splitlines()
trailers = [line[len(line.rstrip(b" \t")):] for line in lines]
for index, trailer in enumerate(trailers, 1):
    print(index, repr(trailer), "bits", "".join("0" if b == 32 else "1" for b in trailer))
```

Determine whether each line is a separate byte/codeword, whether newlines are delimiters and whether there is a header/length. Plain copying through an editor or Markdown can remove trailing whitespace and invalidate the channel.

## 5. Capitalization, acrostics and layout

| Clue | Targeted extraction |
| --- | --- |
| Weird capitals | Preserve letter order; try a binary upper/lower hypothesis |
| Forced line breaks | First/last character of each original line |
| Odd word choices | Word lengths, initial letters, clue-specific indices |
| Similar-looking letters | Compare Unicode code points before transliteration |
| Strange line lengths | Record byte count and code-point count separately |

For a line-initial hypothesis:

```python
from pathlib import Path
lines = Path("message.txt").read_text(encoding="utf-8").splitlines()
print("".join(line[0] for line in lines if line))
```

This takes the actual first code point, including a leading space if present. Do not call `.strip()` unless the hypothesis requires removing that evidence.

## 6. Normalization comparison

```python
from pathlib import Path
import unicodedata

text = Path("message.txt").read_text(encoding="utf-8")
for form in ("NFC", "NFD", "NFKC", "NFKD"):
    normalized = unicodedata.normalize(form, text)
    print(form, "changed", normalized != text, "length", len(normalized))
```

Do this for comparison; preserve the original. Compatibility normalization can merge distinct characters and erase a deliberate distinction. It does not universally remove invisible characters or turn every confusable into ASCII. See [Unicode normalization](https://www.unicode.org/reports/tr15/).

## Troubleshooting

| Problem | Next check |
| --- | --- |
| Symbols visible in report but no full bytes | Wrong mapping or too few symbols |
| One byte correct then nonsense | Character order, per-line framing or a third delimiter symbol |
| Text looks reversed | Logical code-point order versus display BiDi |
| Text changed after paste | Editor normalization, stripped whitespace or changed line endings |
| Lots of non-ASCII language text | Legitimate script, combining marks and joiners before stego assumptions |

Tools: [Notepad++](../../ajcbbc_allow_tools/notepad_plus_plus/), [HxD](../../ajcbbc_allow_tools/hxd/), [CyberChef](../../ajcbbc_allow_tools/cyberchef/), [Python](../../ajcbbc_allow_tools/python3/).
