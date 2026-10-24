---
title: "Fatmike 02 — Record Player"
date: 2026-10-24
weight: 1
bookToc: true
description: "Fix two playback settings, then recover the flag from a checked XOR window in the embedded audio."
---

# Fatmike 02 — Record Player

[Download solver](files/solve.py)

The record player forces backward playback and pitch processing when the PLAY button is pressed. The official solution describes changing those two settings. I reproduced the patches against the handout and extracted the flag directly from its audio resource, then checked the result with the original hash function.

```text
CMO{y0u_g0t_r1ckr0ll3d}
```

The verification here is offline: original x64 code confirms the hash and the effect of the two patches. I did not launch the complete GUI or listen to playback.

## 1. Identify the binary

The handout is `Fatmike_02/Handout/RecordPlayer.exe` in the public repository.

```bash
file RecordPlayer.exe
sha256sum RecordPlayer.exe
objdump -d -M intel RecordPlayer.exe > record-player.asm
```

The file is a native Windows x64 GUI executable. Its preferred image base is `0x140000000`.

```text
c0846e7b630e3d307ed795378b5346b90cc524a508d35a118979f85938d0f5a3
```

The imports give two useful starting points: `waveOutOpen`/`waveOutWrite` identify the audio path, while `FindResourceW`, `LoadResource`, and `LockResource` identify embedded data. A `SOUND` resource name is also visible in the binary.

## 2. Find the PLAY handler and its two settings

The control-command handler begins at `0x140003860`. It dispatches control ID `0x3e9` to the PLAY path. That path loads sound resource ID `0x8d` and then forces two settings before starting playback:

```asm
14000392d  mov     dl, 1
14000392f  mov     rcx, [rbx+0x50]
140003933  call    0x140003a00
140003938  mov     dl, 1
14000393a  mov     rcx, [rbx+0x50]
14000393e  call    0x140003a20
140003943  mov     rcx, [rbx+0x50]
140003947  call    0x1400020f0
```

Both setters take the audio-object pointer in `RCX` and a Boolean value in `DL`.

The first setter calculates the byte-step direction:

```asm
140003a00  movzx   eax, dl
140003a03  xor     eax, 1
140003a06  lea     eax, [rax*2-1]
140003a0d  mov     [rcx+0x18], eax
```

With `DL=1`, the stored signed step is `-1`; with `DL=0`, it is `+1`.

The second setter writes the pitch-processing flag:

```asm
140003a20  mov     [rcx+0x1d], dl
```

Changing the two call arguments from one to zero selects forward playback with pitch processing disabled.

| Instruction VA | File offset | Original bytes | Patched bytes |
| --- | --- | --- | --- |
| `0x14000392d` | `0x2d2d` | `b2 01` | `b2 00` |
| `0x140003938` | `0x2d38` | `b2 01` | `b2 00` |

The addresses printed in the official README were from a different loaded address range. Use the RVAs or the addresses measured in this handout rather than copying a runtime address literally.

## 3. Extract the audio resource

The only RIFF/WAVE object in the file starts at raw offset `0x78708`. Reading its chunk headers gives:

```text
44100 samples per second
1 channel
8-bit PCM
720623 samples
```

The audio loader at `0x140001f50` checks PCM format, reads the channel count, sample rate, and bit depth, finds the `data` chunk, and copies its samples into the audio object.

The accompanying solver can save the WAV independently:

```bash
python solve.py RecordPlayer.exe --extract-audio sound.wav --details
```

The WAV itself is not a plaintext flag container. The next part explains why a particular window of its samples matters.

## 4. Recover the encrypted flag bytes

The audio-object constructor builds a 23-byte vector from constants loaded at `0x1400017b6`–`0x1400017df`:

```text
30 2b 3d fc f6 b6 06 3b 0e b1 ed c0 e1 48 07 0c
0b bb f4 f9 48 01 19
```

It stores an expected hash at object offset `0x150`:

```asm
14000183f  mov dword ptr [rdi+0x150], 0x18940a3d
```

The sound-buffer fill routine starts at `0x140002310`. It keeps a sliding queue of recently emitted audio bytes. Once that queue contains a complete 23-byte window, it XORs the window with the constructor's vector:

```asm
14000252c  movzx   r12d, byte ptr [rax+rdx]
140002531  xor     r12b, byte ptr [r8+r9]
```

The decoded candidate is then checked by the routine at `0x140001030`. Its seed is `0x811c9dc5`, and each byte is XORed into the state before multiplication by `0x01000193`: FNV-1a-32.

Only a candidate with hash `0x18940a3d` reaches the callback at `0x1400026b3`. That callback carries the decoded string back to the window code, which updates the displayed text.

## 5. Search audio windows instead of playing the song

After the two playback fixes, the samples are emitted in their original forward order. We can therefore search the embedded sample bytes directly:

```python
def fnv1a(data):
    value = 0x811c9dc5
    for byte in data:
        value = ((value ^ byte) * 0x01000193) & 0xffffffff
    return value

for start in range(len(samples) - len(encrypted) + 1):
    candidate = bytes(
        encrypted[i] ^ samples[start + i]
        for i in range(len(encrypted))
    )
    if all(32 <= c < 127 for c in candidate):
        if fnv1a(candidate) == 0x18940a3d:
            print(start, candidate)
```

Exactly one printable candidate matches:

```text
132300 b'CMO{y0u_g0t_r1ckr0ll3d}'
```

At 44100 samples per second, sample `132300` is exactly three seconds into the audio. That explains why the program needs a short period of correct playback before it can display the flag.

## 6. Reproduce the extraction and patches

The solver extracts the constants and WAV from the binary rather than embedding the official flag:

```bash
python solve.py RecordPlayer.exe --details
```

Output:

```text
WAV raw offset: 0x78708
Audio: 44100 Hz, mono 8-bit, 720623 samples
Encrypted bytes: 302b3dfcf6b6063b0eb1edc0e148070c0bbbf4f9480119
FNV-1a target: 0x18940a3d
Matching sample: 132300 (3.0 seconds)
Patch VA/file offsets: 0x14000392d/0x2d2d and 0x140003938/0x2d38
CMO{y0u_g0t_r1ckr0ll3d}
```

To produce a patched copy:

```bash
python solve.py RecordPlayer.exe --patch-output RecordPlayer.patched.exe
cmp -l RecordPlayer.exe RecordPlayer.patched.exe
```

`cmp` reports just two changed bytes. Its positions are one-based and its byte values are octal:

```text
  11567   1   0
  11578   1   0
```

The solver refuses to overwrite its input file.

## 7. Verify the original code's checks

For the optional machine-code comparison:

```bash
python -m pip install unicorn
python solve.py RecordPlayer.exe --verify-native --details
```

The verifier first executes the original FNV-1a routine at `0x140001030` over the extracted candidate and confirms its result is `0x18940a3d`.

It then executes the two PLAY-handler call sites and their original setters in two fresh emulators:

| Code image | Audio-object step | Pitch flag |
| --- | --- | --- |
| Original | `-1` | `1` |
| Two-byte patched copy | `+1` | `0` |

The emulator stops before entering the playback setup. Thus the proof covers the patched settings and checked audio-window extraction, not a full GUI execution. Re-XORing the recovered candidate with the matching audio bytes also reproduces the 23 encrypted bytes exactly.

## Source

[Official challenge and patch description](https://github.com/crackmesone/ctf-2026-challenges-public/tree/5f8857cf3556e4e36d7e7fc4650044ae682701b8/Fatmike_02).
