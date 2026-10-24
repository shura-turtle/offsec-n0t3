---
title: "A Matter of Time"
date: 2026-10-24
weight: 1
bookToc: true
description: "Trace an obfuscated Windows crackme, extract its ciphertext, recover the account-name AES key, and check an inferred IV against the original AES code."
---

# A Matter of Time

This crackme builds its AES key from a Windows account name. Its IV depends on a file timestamp and the executable's PE timestamp. The code is split across jump trampolines and duplicated blocks, which makes the first decompiler output misleading.

The useful break was CBC itself: the IV affects only the first plaintext block. Once the right username decrypted the remaining blocks, I could work on the first block separately.

| Item | Value |
| --- | --- |
| Event | Crackmes.one Reverse Engineering CTF 2026, identified by the program's banner |
| File | `a_matter_of_time.exe` |
| Format | Windows PE32+, x86-64 |
| Image base in IDA | `0x140000000` |
| Tools used | IDA, Python, Capstone, Unicorn, PyCryptodome |
| Result | Original AES routine reproduced the candidate; the public challenge README independently confirms the exact flag |

**The IV remains inferred:** I did not recover the original timestamp pair that generated it. Replaying AES confirms the bytes for that IV, but CBC alone does not make the first block unique. The public challenge README now confirms the complete flag string. Section 8 shows why that confirmation matters.

## 1. Check the file and the IDA database

Start by identifying the file:

```bash
file a_matter_of_time.exe
sha256sum a_matter_of_time.exe
```

Output:

```text
a_matter_of_time.exe: PE32+ executable for MS Windows 6.00 (console), x86-64, 7 sections
bc8583d082c42efa9ad0959792af49c063368db0241dabccb9138fa29ef5e7dc  a_matter_of_time.exe
```

The solve started with an IDA database already supplied for this file. The later public ZIP contains another build (`deae388b0b8f9cbea0303ab3a9fc77dc11989bba069c5e5097df7fde4486912d`); these are distinct artifacts, so the addresses and snapshot below apply to the analyzed hash. The database reported the same input SHA-256. Its mapped segments were:

```text
.text   0x140001000 - 0x14000b000
.idata  0x14000b000 - 0x14000b480
.rdata  0x14000b480 - 0x140011000
.data   0x140011000 - 0x140012000
.pdata  0x140012000 - 0x140013000
.ch     0x140015000 - 0x140029000
```

The `.ch` mapping matters. The supplied database has code and layout that differ from the raw file's section layout. The scripts here use that database image. **This writeup starts from the supplied IDB; it does not include an independently recovered unpacking step.** Opening only the raw EXE in a fresh database may therefore give different results at the addresses below.

Use the attached [mapped segments](files/ida_segments.json) to reproduce this analysis, or export the corresponding segments from the supplied IDB with [export_ida.py](files/export_ida.py). Edit its output path, then run it through IDA's **File → Script file**.

The exported JSON maps each segment's virtual address to its Base64-encoded bytes. It is input for the analysis scripts, not a runnable PE file.

### Prepare the helpers

Download [analysis-tools.zip](analysis-tools.zip), extract it, and enter that directory:

```bash
unzip analysis-tools.zip -d a-matter-of-time
cd a-matter-of-time
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pycryptodome unicorn capstone
```

PyCryptodome is enough for the final `solve.py`. Unicorn runs the original machine code. Capstone is used by the control-flow helper.

## 2. Find main through the CRT startup

The entry point is `0x140009188`. Decompiling it immediately produced a stack warning and jumps into `.ch`. That was a reason to inspect the instructions before trusting the pseudocode.

I followed references to `__p___argv`. One startup path contains:

```asm
1400219fe  call    __p___argv
140021a03  mov     rbx, [rax]
140021a06  call    __p___argc
140021a0b  mov     r8, rdi
140021a0e  mov     rdx, rbx
140021a11  mov     ecx, [rax]
140021a13  call    0x140004290
```

The Windows x64 argument registers are `RCX`, `RDX`, and `R8`. The caller is passing the argument count, argument vector, and another startup argument into `0x140004290`. This identifies the main routine despite its missing function boundary.

At `0x140004290`, the first two instructions are:

```asm
140004290  jp      0x14001ceb9
140004296  jnp     0x14001cef3
```

One branch is taken when the parity flag is set, and the other when it is clear. There is no executable fallthrough after the pair. Both destinations contain copies of the main prologue and converge at `0x1400042c2`.

The same pattern appears elsewhere:

```asm
14001d306  jo      0x14000453b
14001d30c  jno     0x14000453b
```

Here both outcomes reach the same address. Bytes following the pair are junk, even if decoding linearly makes them look like instructions.

Other transfers use a register:

```asm
140004858  push    rsi
140004859  lea     rsi, [rip + 0x19276]
140004860  jmp     rsi
```

The `lea` resolves to `0x14001dad6`. That destination starts with `pop rsi`, restoring the saved register. A normal direct-jump-only walk would miss this block.

### Walk reachable instructions

Run the helper from the download:

```bash
python recover_cfg.py 0x140004290 > main.asm
python recover_cfg.py 0x140001000 > startup.asm
python recover_cfg.py 0x14000326c > aes-cbc.asm
```

It follows direct branches, complementary branch pairs, and the nearby `lea`/register and `lea`/`ret` trampolines used here. It keeps both branch destinations instead of assuming every duplicated block is equivalent.

The output is sorted by address for reference; it is **not execution order**. Follow the branch targets to move between `.text` and `.ch`. The helper also stops at calls, so run it again with a callee's address when tracing into another routine. It is specific to these patterns and does not resolve arbitrary indirect jumps or exception paths.

## 3. Recover the ciphertext from the initializer

The main routine eventually reads a C++ string at `0x140011d98`. Searching the raw file for a readable flag was not useful because the string is constructed during startup.

The initializer starts at `0x140001000` and transfers into a block at `0x14001f415`. It loads encrypted constants into a stack buffer, then applies:

```asm
lea     eax, [rcx - 0x28]
xor     byte ptr [rbp + rcx - 0x19], al
inc     rcx
cmp     rcx, 0x60
```

The transform is:

```python
decoded = bytes(
    byte ^ ((index - 0x28) & 0xff)
    for index, byte in enumerate(encrypted)
)
```

The comparison with `0x60` gives 96 decoded bytes. These are ASCII hex characters, so they represent 48 bytes of ciphertext.

Rather than transcribe every stack constant, I ran just this initializer in Unicorn. The extraction hook stops at `0x140007bc4`, before the C++ string-copy helper executes. At that point:

```text
RCX = destination std::string
RDX = decoded stack-buffer address
R8  = string length, 96
```

The attached [extract.py](files/extract.py) performs that extraction:

```bash
python extract.py
```

Relevant output:

```text
Ciphertext hex: 4c4635258cf6eca5d80b8e050a9e5b04f1a9c979bc55f3f4773971ed2f81a96967bb3569fa002f549cc970a18779b3a7
Ciphertext bytes: 48
Time source: C:\\Windows\\System32\\winevt\\Logs\\System.evtx
```

The decoded path has doubled backslashes, as printed above; elsewhere on this page I show it with single path separators for readability. The script also writes `ciphertext.hex`. It stops before library calls in each extraction path, so it does not need to emulate Windows or the full C++ runtime.

## 4. Identify AES and the CBC loop

At this stage the important functions are:

| Address | What the code does |
| --- | --- |
| `0x1400010b0` | Expands an AES-128 key into 44 words |
| `0x140001498` | Applies AES inverse rounds to one 16-byte block |
| `0x14000326c` | Decrypts a byte vector using CBC chaining |
| `0x1400033b4` | Gets the Windows account name and converts it to UTF-8 |
| `0x140003734` | Reads the loaded module's PE timestamp |
| `0x140003750` | Gets the last-write time of `System.evtx` |
| `0x1400034f8` | Converts the file-time value to seconds through a chrono helper |
| `0x140003d98` | Formats a string with zero fill and width 16 |
| `0x140007034` | Converts an unsigned 32-bit integer to decimal text |

The key expansion copies 16 key bytes, uses the substitution and round-constant tables, and expands to `0x2c` words. The inverse cipher then operates on 16-byte blocks. The surrounding loop establishes the mode: it saves each ciphertext block, decrypts the block, XORs it with the previous ciphertext block or initial IV, and carries the saved ciphertext forward.

In pseudocode:

```python
previous = iv
for offset in range(0, len(ciphertext), 16):
    current = ciphertext[offset:offset + 16]
    plaintext_block = xor(aes_decrypt_block(key, current), previous)
    previous = current
```

This is AES-128-CBC. The original inverse cipher at `0x140001498` is also used in the final machine-code verification.

## 5. Trace the key back to the account name

The routine at `0x1400033b4` calls:

```text
GetCurrentProcess
OpenProcessToken
GetTokenInformation(TokenUser)
LookupAccountSidW
```

It gets the account name associated with the process token. The following conversion makes that UTF-8 text available to the key-building code.

The formatter at `0x140003d98` uses width `0x10` and fill byte `0x30`. For the short strings relevant here, its behavior is equivalent to:

```python
formatted = text.rjust(16, "0")
```

There is hexadecimal stream formatting nearby, but the operand is a string. That does not turn `nicetryboogeyman` into the ASCII string `6e696365...`. The bytes passed to AES remain the formatted account-name bytes.

The PDB path gives a username worth testing:

```text
0x14000d5a8
C:\Users\nicetryboogeyman\cmo\x64\Release\cmo.pdb
```

That name is exactly 16 ASCII bytes:

```python
key = b"nicetryboogeyman"
assert len(key) == 16
```

A PDB path alone would only be a lead. The next step checks the key against ciphertext without guessing the IV.

## 6. Decrypt the blocks that do not need the IV

For CBC decryption:

```text
P1 = AES_DEC(K, C1) XOR IV
P2 = AES_DEC(K, C2) XOR C1
P3 = AES_DEC(K, C3) XOR C2
```

Only `P1` depends on the IV. The ciphertext already supplies the chaining bytes for the later blocks.

Run this from the directory containing the extracted `ciphertext.hex`:

```python
from pathlib import Path
from Crypto.Cipher import AES

ciphertext = bytes.fromhex(Path("ciphertext.hex").read_text())
key = b"nicetryboogeyman"
intermediate = AES.new(key, AES.MODE_ECB).decrypt(ciphertext)

for offset in range(16, len(ciphertext), 16):
    decrypted = intermediate[offset:offset + 16]
    previous = ciphertext[offset - 16:offset]
    block = bytes(a ^ b for a, b in zip(decrypted, previous))
    print(offset // 16 + 1, repr(block))
```

Output:

```text
2 b't0_l34rn_fr0M_n0'
3 b'T_t0_l1V3_1n}\x03\x03\x03'
```

The suffix reads `t0_l34rn_fr0M_n0T_t0_l1V3_1n}`. Three trailing `0x03` bytes are valid PKCS#7 padding for a 45-byte plaintext.

Together, the readable suffix and padding strongly support the username as the AES key. Padding by itself would be much weaker evidence.

## 7. Check what the time code actually reads

My first notes described the time input as the current clock. Inspecting the code more closely showed a file lookup instead.

At `0x140003750`, another XOR-decoded stack string resolves to:

```text
C:\Windows\System32\winevt\Logs\System.evtx
```

`extract.py` stops at `0x140009a80`, after that decode and before the library work, and reads the path through `R13`. The subsequent filesystem-stat call at `0x140009bbc` requests the last-write-time field. Main converts the returned file time, keeps its low 32 bits, and XORs that with the loaded module's PE timestamp before calling the decimal formatter.

The PE timestamp reader is short enough to recognize directly:

```asm
xor     ecx, ecx
call    GetModuleHandleW
mov     rcx, rax
movsxd  rax, dword ptr [rax + 0x3c]
mov     eax, dword ptr [rax + rcx + 8]
```

`0x3c` is the DOS header's `e_lfanew`. The final read gets the COFF `TimeDateStamp` at NT headers +8.

The IV-building path can be described as:

```python
# Model of the data flow, not an exact replacement for the chrono conversion.
file_seconds = convert_last_write_time(system_event_log)
value = (file_seconds & 0xffffffff) ^ loaded_module_pe_timestamp
iv_text = str(value).rjust(16, "0")
```

There are also warnings based on `0x698fbb00`, corresponding to 2026-02-14 UTC. The elapsed-hour calculation uses a multiply by `0x91a2b3c5` followed by a 43-bit shift. Those warning paths converge before decryption; reaching the CTF date window is not sufficient to identify the IV.

The current raw EXE has a zero PE timestamp. That does not tell us the original `System.evtx` time or establish which timestamp pair the author used when encrypting the flag. The solve therefore does not claim to have reproduced the intended Windows environment.

## 8. Reconstruct the first block, and keep the uncertainty visible

With the key known, decrypting the first ciphertext block without CBC XOR gives:

```python
from Crypto.Cipher import AES

ciphertext = bytes.fromhex(
    "4c4635258cf6eca5d80b8e050a9e5b04"
    "f1a9c979bc55f3f4773971ed2f81a969"
    "67bb3569fa002f549cc970a18779b3a7"
)
decrypted_first = AES.new(b"nicetryboogeyman", AES.MODE_ECB).decrypt(
    ciphertext[:16]
)
print(decrypted_first.hex())
```

Output:

```text
737d7f4b0558036a430363426701466c
```

The readable suffix suggests the sentence “the past is to learn from, not to live in.” A candidate for its first 16 bytes is:

```python
first_block = b"CMO{5h3_p4St_1s_"
iv = bytes(a ^ b for a, b in zip(decrypted_first, first_block))
print(iv)
print(int(iv))
```

Output:

```text
b'0000000537068053'
537068053
```

That matches the expected IV representation: a zero-padded decimal unsigned 32-bit value. Decrypting with it produces a coherent complete string.

This is still an inference. For example, changing the first-block candidate from `..._1s_` to `..._0s_` produces another decimal-looking IV:

```text
CMO{5h3_p4St_1s_  ->  0000000537068053
CMO{5h3_p4St_0s_  ->  0000000537068153
```

Both preserve the exact same later plaintext blocks and padding. The wording favors the first, but CBC does not authenticate it.

The executable's success branch is also too weak to settle this. Its relevant comparisons are equivalent to:

```c
if (plaintext[0] == 'C' || plaintext[1] == 'M') {
    print_success();
    print_plaintext();
}
```

At `0x1400048a3`, equality with `C` jumps directly to the success path. If that fails, equality with `M` at `0x1400048a9` reaches the same path. It does not require the whole `CMO{...}` prefix or compare the full flag.

The local AES replay still does not choose uniquely between those first-block candidates. The [public challenge README](https://github.com/crackmesone/ctf-2026-challenges-public/blob/5f8857cf3556e4e36d7e7fc4650044ae682701b8/A_MatterOfTime/README.md) explicitly gives `CMO{5h3_p4St_1s_t0_l34rn_fr0M_n0T_t0_l1V3_1n}`, which resolves the flag text independently of the inferred IV. The original timestamp pair remains unknown.

## 9. Run the solver

Save this as `solve.py`, or use the [attached solver](files/solve.py):

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

ciphertext = bytes.fromhex(
    "4c4635258cf6eca5d80b8e050a9e5b04"
    "f1a9c979bc55f3f4773971ed2f81a969"
    "67bb3569fa002f549cc970a18779b3a7"
)
key = b"nicetryboogeyman"

# Inferred from a readable first block; not an observed runtime timestamp.
iv = b"0000000537068053"

padded = AES.new(key, AES.MODE_CBC, iv).decrypt(ciphertext)
plaintext = unpad(padded, AES.block_size)
assert AES.new(key, AES.MODE_CBC, iv).encrypt(padded) == ciphertext
print(plaintext.decode("ascii"))
```

Run:

```bash
python solve.py
```

Output:

```text
CMO{5h3_p4St_1s_t0_l34rn_fr0M_n0T_t0_l1V3_1n}
```

Keep `5h3` exactly as shown. Substituting a more natural spelling changes the bytes and the inferred IV.

## 10. Compare with the original AES routine

The downloadable solver also supports:

```bash
python solve.py --verify-native
```

This calls [verify_aes.py](files/verify_aes.py), which maps the exported segments and enters the original CBC routine at `0x14000326c`.

The emulated call uses the Windows x64 argument registers:

```text
RCX -> ciphertext vector
RDX -> key vector
R8  -> IV vector
```

Each vector is represented as three 64-bit pointers:

```text
begin, end, capacity_end
```

For example, a 48-byte ciphertext at `0x120000` has:

```python
struct.pack("<QQQ", 0x120000, 0x120030, 0x120030)
```

The emulator models four helpers:

| Address | Emulator replacement |
| --- | --- |
| `0x140007e08` | Supply a scratch allocation and initialize its vector pointers |
| `0x140009fb1` | Perform `memset` |
| `0x140008ef4` | Return from the free helper |
| `0x140008c50` | Return from the security-cookie check |

The key expansion, inverse rounds, CBC XOR, and block chaining execute as original machine instructions. No crypto instruction is patched, and the complete application is not launched.

The resulting bytes are:

```text
b'CMO{5h3_p4St_1s_t0_l34rn_fr0M_n0T_t0_l1V3_1n}\x03\x03\x03'
```

The verifier asserts that those 48 bytes match PyCryptodome. The solver also removes the padding and re-encrypts to the extracted ciphertext. These checks confirm the AES model and chosen inputs; they do not independently recover the original IV.

## Files

Everything needed for the recorded analysis is in [analysis-tools.zip](analysis-tools.zip). Individual files:

| File | Purpose |
| --- | --- |
| [solve.py](files/solve.py) | Final decryption and optional machine-code comparison |
| [extract.py](files/extract.py) | Recover the ciphertext and hidden file path from the mapped code |
| [recover_cfg.py](files/recover_cfg.py) | Follow the branch/trampoline patterns used by this binary |
| [verify_aes.py](files/verify_aes.py) | Run the original AES-CBC routine in Unicorn |
| [export_ida.py](files/export_ida.py) | Export mapped segments from the supplied IDA database |
| [ida_segments.json](files/ida_segments.json) | Segment snapshot used in this solve |
| [ciphertext.hex](files/ciphertext.hex) | Extracted 96-character ciphertext string |

The raw challenge EXE is not included in this bundle. The mapped snapshot is enough to replay the recorded initializer and AES routine.
