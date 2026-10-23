---
title: "Audio: Samples & Spectrograms"
weight: 50
bookToc: true
---

# Audio steganography

**Identify encoding, channels and sample width before interpreting sound bytes.** Metadata, appended files, spectrogram drawings, sample LSB and timing codes need different extraction paths.

## 1. Triage and PCM inspection

```sh
exiftool -a -u -g1 audio.wav
strings -a -n 6 -t x audio.wav
binwalk audio.wav
```

For an uncompressed PCM WAV, standard-library Python can inspect the actual audio frames:

```python
import wave
with wave.open("audio.wav", "rb") as w:
    print("channels", w.getnchannels(), "width_bytes", w.getsampwidth(),
          "rate", w.getframerate(), "frames", w.getnframes(),
          "compression", w.getcomptype())
    print("duration", w.getnframes() / w.getframerate())
```

`wave` support varies by Python version; older releases do not handle all float/extensible WAV variants. MP3/FLAC are not WAV because their filenames change. Read [Python's WAV support](https://docs.python.org/3/library/wave.html) for the installed release.

## 2. Sample layout

```text
16-bit stereo PCM frame:
    L low byte, L high byte, R low byte, R high byte
next frame repeats the same structure
```

| Width | Common PCM interpretation |
| --- | --- |
| 8-bit WAV | Unsigned samples centered around 128 |
| 16-bit WAV | Signed little-endian integers |
| 24-bit WAV | Signed three-byte integers; manual sign extension required |
| 32-bit WAV | Could be integer or float; inspect the format tag |

RIFF files can have metadata and other chunks before/after `data`. Do not assume every WAV has a 44-byte header. `wave.readframes()` isolates frame data for formats it supports.

## 3. Visual waveform and spectrogram

This optional snippet requires **NumPy and Matplotlib already installed and allowed**. It handles only 16-bit uncompressed PCM, takes the first channel and limits analysis to 30 seconds.

```python
from pathlib import Path
import wave
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

output = Path("spectrogram.png")
if output.exists():
    raise FileExistsError(output)
with wave.open("audio.wav", "rb") as w:
    if w.getsampwidth() != 2 or w.getcomptype() != "NONE":
        raise ValueError("this example requires 16-bit PCM")
    rate, channels = w.getframerate(), w.getnchannels()
    raw = w.readframes(min(w.getnframes(), rate * 30))
samples = np.frombuffer(raw, dtype="<i2").reshape(-1, channels)
x = samples[:, 0].astype(np.float64) / 32768.0
fig, axes = plt.subplots(2, 1, figsize=(12, 7))
axes[0].plot(np.arange(len(x)) / rate, x, linewidth=0.4)
axes[0].set(xlabel="Time (s)", ylabel="Amplitude", title="Channel 0")
axes[1].specgram(x, NFFT=1024, Fs=rate, noverlap=768, cmap="magma")
axes[1].set(xlabel="Time (s)", ylabel="Frequency (Hz)")
fig.tight_layout()
fig.savefig(output, dpi=160)
plt.close(fig)
```

The generated picture is a diagnostic plot, not a challenge screenshot. Inspect both channels separately. Compare FFT sizes `256`, `1024`, `4096`: a larger window improves frequency detail while reducing time detail. Keep overlap below FFT size. No pattern in one parameter setting is not proof nothing is encoded.

## 4. PCM sample-LSB extraction

For one low bit of each **16-bit channel-0 sample**, packed first-bit-as-MSB:

```python
from pathlib import Path
import struct
import wave

with wave.open("audio.wav", "rb") as w:
    if w.getsampwidth() != 2 or w.getcomptype() != "NONE":
        raise ValueError("requires 16-bit PCM")
    channels = w.getnchannels()
    data = w.readframes(min(w.getnframes(), 8 * 4096))
values = struct.unpack("<" + "h" * (len(data)//2), data)
bits = [(value & 1) for value in values[0::channels]]
result = bytes(sum(bits[i+j] << (7-j) for j in range(8))
               for i in range(0, len(bits)-7, 8))
with Path("audio-lsb.bin").open("xb") as output:
    output.write(result)
print(repr(result[:100]))
```

For channel 1 change `values[0::channels]` to `values[1::channels]` only if there are at least two channels. Interleaving all channels is a different stream. Taking each raw byte's LSB is also a different method from each sample's low bit.

## 5. Morse and tone clues

Waveform/spectrogram pulses may encode duration rather than amplitude bits. Establish short/long pulse clusters and word/letter gaps before translating.

```text
A .-    B -...  C -.-.  D -..   E .     F ..-.
G --.   H ....  I ..    J .---  K -.-   L .-..
M --    N -.    O ---   P .--.  Q --.-  R .-.
S ...   T -     U ..-   V ...-  W .--   X -..-
Y -.--  Z --..
```

DTMF uses pairs of simultaneous frequencies, as defined by [ITU-T Q.23](https://www.itu.int/rec/T-REC-Q.23/en):

| Hz | 1209 | 1336 | 1477 | 1633 |
| --- | --- | --- | --- | --- |
| 697 | 1 | 2 | 3 | A |
| 770 | 4 | 5 | 6 | B |
| 852 | 7 | 8 | 9 | C |
| 941 | * | 0 | # | D |

Do not decode one frequency peak as a full key. Identify both peaks in the same tone interval and account for silence/repeated keys.

## 6. Diagnostics and next steps

| Result | Next check |
| --- | --- |
| WAV decoder rejects input | Actual format, format tag, truncation, Python version |
| Flat line / no visible spectrogram | Wrong channel, silence, bad sample interpretation or quiet region |
| One channel noisy, other meaningful | Inspect independently; then compare sum/difference as a separate hypothesis |
| Speech backward or odd speed | Make a derivative only after preserving original; record rate/reversal |
| Sample LSB looks random | Different channel/order/plane or a non-LSB method |
| MP3 converted to WAV still fails LSB | Lossy coding may have destroyed exact sample bits |

Use [carving](../archives-carving/) for embedded file signatures, [CyberChef](../../ajcbbc_allow_tools/cyberchef/) for an identified encoded text layer, and [Python notes](../../ajcbbc_allow_tools/python3/) for offline processing.

Reference: [Matplotlib spectrogram parameters](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.specgram.html).
