---
title: "xz"
weight: 25
bookToc: true
---

**Use for:** decompressing XZ/LZMA streams and checking archive integrity.  
**Run in:** WSL.

## Inspect before decompressing

```bash
xz --version
xz -l evidence.xz             # Size, ratio and stream summary
xz -lv evidence.xz            # More stream/block details
xz -t evidence.xz             # Integrity test; no extracted output
```

## Decompress while preserving the input

```bash
xz -dk evidence.xz

# Explicit output filename; keeps original and writes bytes to stdout
xz -dc evidence.xz > evidence.bin

# Legacy .lzma stream
xz --format=lzma -dc evidence.lzma > evidence.bin
```

## CTF walkthrough

1. Identify an XZ stream directly or through binwalk.
2. Record its offset if it is embedded inside another file.
3. Carve it, check integrity with `xz -t`, then decompress.
4. Inspect the resulting bytes with `xxd` and `strings`.

```bash
# Example embedded offset; replace 4096 with the actual value
dd if=container.bin of=carved.xz bs=1 skip=4096 status=none
xz -dc carved.xz > recovered.bin
xxd -l 64 recovered.bin
```

## Gotchas

- `xz -d` normally removes the compressed input after success; add `-k` to keep it.
- `.tar.xz` decompresses into a tar archive, not its individual members.
- A raw LZMA stream needs the correct filter settings; it is different from a `.lzma` container.

## Flags explained

| Flag | Meaning |
| --- | --- |
| `-d` | Decompress |
| `-k` | Keep the original input after successful operation |
| `-c` | Write output to stdout instead of a generated filename |
| `-t` | Test compressed-stream integrity |
| `-l` | List compressed-stream information |
| `-v` | Verbose output; combines with `-l` |
| `--format=lzma` | Select the legacy .lzma container |
| `--memlimit-decompress=LIMIT` | Bound decompression memory use |

`-dk` combines `-d` and `-k`; `-dc` combines decompression with stdout output. Shell `>` saves that stdout into the requested filename.

## CTF: recognize container signatures

```bash
xxd -l 16 evidence.bin
```

An XZ stream starts with `FD 37 7A 58 5A 00`. A file extension alone is insufficient; legacy LZMA and raw streams have different framing.

## CTF: decompress without trusting a filename

```bash
# Explicit input format, output filename and memory bound
xz --format=xz --memlimit-decompress=256MiB -dc evidence.bin > out.bin
```

If the output is a tar archive, inspect/extract it using available approved utilities or Python’s standard `tarfile` module. Decompression and archive member extraction are separate steps.

## CTF: inspect a decompressed TAR from Python

```python
import tarfile

with tarfile.open("out.bin", "r:") as archive:
    for member in archive.getmembers():
        print(member.name, member.size, "file" if member.isfile() else "other")
```

Inspect names before extraction. For one chosen regular member, use `extractfile()` and save it to your own chosen output path rather than honoring arbitrary member paths.

## Troubleshooting

| Symptom | Next check |
| --- | --- |
| File format not recognized | Offset, wrapper and correct input bytes |
| Unexpected end of input | Truncation or wrong carve length |
| Integrity check failed | Corruption, missing bytes or incorrect boundary |
| Memory limit exceeded | Required dictionary size versus available budget |
| Decompression works, file still unreadable | Another container/encoding layer |

Reference: [XZ manual](https://tukaani.org/xz/man/xz.1.html).

## Related playbooks

- [Archives and embedded files](../../steganograph-expl/archives-carving/)
