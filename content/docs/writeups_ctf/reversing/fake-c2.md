---
title: "Fake C2"
date: 2026-10-26T01:53:00+06:30
bookToc: true
description: "Redirect a local Go implant emulator, inspect its RC4 key check, and recover the supplied flag."
---

# Fake C2

## Original illustrated walkthrough

The pages below reproduce the supplied PDF in order, including every screenshot and code image. Select a page to open it at full size. [Download the original PDF](/writeups_ctf/reversing/fake-c2/source.pdf).

### Page 1: Challenge setup and localhost port mismatch

[![fake-c2 PDF page 1: Challenge setup and localhost port mismatch](/writeups_ctf/reversing/fake-c2/page-1.jpg)](/writeups_ctf/reversing/fake-c2/page-1.jpg)

### Page 2: Burp capture of GET /check and POST /post

[![fake-c2 PDF page 2: Burp capture of GET /check and POST /post](/writeups_ctf/reversing/fake-c2/page-2.jpg)](/writeups_ctf/reversing/fake-c2/page-2.jpg)

### Page 3: Go binary strings and client/server entry points

[![fake-c2 PDF page 3: Go binary strings and client/server entry points](/writeups_ctf/reversing/fake-c2/page-3.jpg)](/writeups_ctf/reversing/fake-c2/page-3.jpg)

### Page 4: Server handler and RC4 operation

[![fake-c2 PDF page 4: Server handler and RC4 operation](/writeups_ctf/reversing/fake-c2/page-4.jpg)](/writeups_ctf/reversing/fake-c2/page-4.jpg)

### Page 5: Debugger length comparison and key inspection

[![fake-c2 PDF page 5: Debugger length comparison and key inspection](/writeups_ctf/reversing/fake-c2/page-5.jpg)](/writeups_ctf/reversing/fake-c2/page-5.jpg)

### Page 6: Expected key and reported flag

[![fake-c2 PDF page 6: Expected key and reported flag](/writeups_ctf/reversing/fake-c2/page-6.jpg)](/writeups_ctf/reversing/fake-c2/page-6.jpg)

## Searchable solve steps

The supplied PDF describes a Go binary that contains both a client and a local C2 emulator. The client connects to `127.0.0.1:5555`, while the server listens on `127.0.0.1:5556`. The archive password is `csg2025`. The binary itself was not included with the PDF here, so the runtime and debugger observations below come from the PDF; they have not been replayed locally.

## 1. Redirect the local request

Run the sample in an isolated analysis environment. Its console reports a listener on port `5556` and a failed client connection. A packet capture shows the client trying port `5555`. Redirect the client connection to `127.0.0.1:5556` through an intercepting proxy and forward the `GET /check` request. The program then asks for a decryption key. Submitting a test key produces a `POST /post` request containing `decryptkey` and an encrypted response.

## 2. Locate the key check

In Ghidra, the strings and function names identify Go code. `main.main` calls `main.startServer` and `main.runClient`. The server handler `main.startServer.func2` calls `rc4.NewCipher` and `XORKeyStream`, which places the RC4 operation in the response path.

Attach a debugger to the isolated process. The PDF identifies RVA `0x287034` near the conditional branch before `XORKeyStream`. With a six-character test key such as `foobar`, the comparison sees `RCX = 6` and `RDX = 0x15`. These are lengths: the supplied key has six bytes and the expected key has 21. A 21-byte test input passes that length check. At this point, the PDF locates the submitted bytes at `rsp+0x68` and expected bytes at `rsp+0x80`.

## 3. Supply the recovered key

The expected 21-byte string shown in the PDF is:

```text
RC4JsonMarshalLocalC2
```

Enter it at the prompt after forwarding the local requests. The PDF reports the resulting flag as:

```text
CSG_FLAG{go_rev_startingpoint}
```

The PDF documents this result, but the challenge binary and a live capture were not available for independent replay.

