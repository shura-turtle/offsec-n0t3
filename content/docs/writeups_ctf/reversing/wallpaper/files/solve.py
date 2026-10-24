#!/usr/bin/env python3
"""Validate the author-supplied slide sequence and replay the native handout."""
import argparse
from pathlib import Path
import subprocess

MOVES = '1012321103210033011233322110103321001'
INITIAL = 0xb6fd071e9c8a3425
GOAL = 0xfedcba9876543210

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('binary',type=Path); args=p.parse_args()
    board = [(INITIAL >> (4*i)) & 15 for i in range(16)]
    assert len(MOVES) == 37
    for index, move in enumerate(MOVES):
        blank = board.index(0)
        delta = {'0':-4,'1':-1,'2':4,'3':1}[move]
        other = blank + delta
        assert 0 <= other < 16
        if move in '13': assert blank // 4 == other // 4, (index,move)
        board[blank],board[other] = board[other],board[blank]
    assert sum(value << (4*i) for i,value in enumerate(board)) == GOAL
    r = subprocess.run([str(args.binary.resolve())],input=(MOVES+'\n').encode(),capture_output=True,timeout=5)
    # The assembly exits with RDI still equal to 1. Its success text is decisive.
    assert b'good job, validate with CMO{your_input}' in r.stdout, repr(r.stdout+r.stderr)
    print('CMO{'+MOVES+'}')

if __name__ == '__main__':main()
