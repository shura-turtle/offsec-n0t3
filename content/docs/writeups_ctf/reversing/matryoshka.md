---
title: "Matryoshka Is a Russian Nested Doll"
date: 2026-10-26T01:53:00+06:30
bookToc: true
description: "Peel nested PHP encodings by capturing eval and decoding the innermost payload."
---

# Matryoshka Is a Russian Nested Doll

## Original illustrated walkthrough

The pages below reproduce the supplied PDF in order, including every screenshot and code image. Select a page to open it at full size. [Download the original PDF](/writeups_ctf/reversing/matryoshka/source.pdf).

### Page 1: PHP obfuscation layers and eval hook example

[![matryoshka PDF page 1: PHP obfuscation layers and eval hook example](/writeups_ctf/reversing/matryoshka/page-1.jpg)](/writeups_ctf/reversing/matryoshka/page-1.jpg)

### Page 2: Interception strategy and recovered flag

[![matryoshka PDF page 2: Interception strategy and recovered flag](/writeups_ctf/reversing/matryoshka/page-2.jpg)](/writeups_ctf/reversing/matryoshka/page-2.jpg)

### Page 3: Creator harness.php screenshot

[![matryoshka PDF page 3: Creator harness.php screenshot](/writeups_ctf/reversing/matryoshka/page-3.jpg)](/writeups_ctf/reversing/matryoshka/page-3.jpg)

### Page 4: Creator decode.sh screenshot

[![matryoshka PDF page 4: Creator decode.sh screenshot](/writeups_ctf/reversing/matryoshka/page-4.jpg)](/writeups_ctf/reversing/matryoshka/page-4.jpg)

## Searchable solve steps

The supplied archive, password `CyberSeaGame`, contains a large obfuscated PHP script. This is a PHP challenge, separate from the existing [Matryoshka v2](/docs/writeups_ctf/reversing/matryoshka-v2/) Windows DLL writeup. The PHP archive itself was not included with the PDF here, so the final flag comes from the PDF and was not reproduced locally.

## 1. Map the layers

The PDF identifies `hex2bin`, `base64_decode`, escaped strings, `gzuncompress` or `gzinflate`, and nested `eval` calls. Inspect each decoded stage as data in a disposable analysis environment. The output of one decoder may be binary compressed input for the next; keep it as bytes rather than assuming text at every stage.

## 2. Capture and repeat

The PDF suggests using `php-eval-hook` to capture evaluated code and `uopz_set_hook` to observe selected PHP calls. An eval hook captures only the second payload if later layers still contain decoding calls. For each captured stage, identify the outermost decoder, decode it, and feed the resulting PHP source into the next pass. When a captured fragment needs to be run as standalone PHP, wrap it in `<?php` and `?>`. Track raw compressed bytes and escaped strings separately; some layers require unescaping even where no named function is called.

The PDF contains screenshots of a creator-provided `harness.php` and `decode.sh`, but their code is not available as text in the PDF extraction. No complete runnable decoder or count of layers can be verified from this source alone.

## 3. Result

The PDF reports that the final decoded layer reveals:

```text
CSG_FLAG{A_Matryoshka_Obfuscated_Script}
```

