---
title: "Wallpaper"
date: 2026-10-24
weight: 1
bookToc: true
description: "Decode a nibble-packed sliding puzzle and replay a 37-move solution."
---

# Wallpaper

[Download solver](files/solve.py)

The handout `wallpaper/handout/wallpaper` is a tiny Linux x86-64 executable; its assembly source and an A* solution program are also included. The README supplies the 37-move answer. I checked the board transitions independently and replayed the sequence on the unmodified executable.

## 1. Read the board representation

The assembly stores 16 tiles as four-bit nibbles in one 64-bit integer, with board position zero in the low nibble. Its initial value is `0xb6fd071e9c8a3425`, which decodes to:

```text
 5  2  4  3
10  8 12  9
14  1  7  0
13 15  6 11
```

The blank is tile zero. The destination is `0xfedcba9876543210`, or tiles 0 through 15 in position order. This matters because it places the blank in the upper-left corner, unlike the usual sliding-puzzle picture.

## 2. Decode and verify the moves

The input loop accepts digits `0` through `3`; the final newline is permitted. It processes exactly 37 moves. The displacement of the blank is `0: -4` (up), `1: -1` (left), `2: +4` (down), `3: +1` (right). Boundary checks prevent horizontal wrapping and out-of-range vertical moves.

The author-supplied solution is:

```text
1012321103210033011233322110103321001
```

The [solver](files/solve.py) starts from the packed board, checks every move is legal, swaps the blank with its neighbor, and verifies that the resulting packed integer equals the goal. It then sends the moves plus a newline to the handout:

```bash
python3 solve.py wallpaper/handout/wallpaper
```

The native process prints `good job, validate with CMO{your_input}`. It exits with status 1 even on this path, so the solver checks the success text and final board instead of using the process exit code as an acceptance signal.

**Flag:** `CMO{1012321103210033011233322110103321001}`
