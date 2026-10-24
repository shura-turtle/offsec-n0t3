# A Matter of Time analysis files

Run commands from this directory, with Python, PyCryptodome, Unicorn, and
Capstone available:

```sh
python extract.py
python solve.py
python solve.py --verify-native
python recover_cfg.py 0x140004290 > main.asm
```

`ida_segments.json` is the supplied IDA database's mapped code/data snapshot.
It is not a runnable executable and this bundle does not supply an unpacker.
`export_ida.py` can re-export the current database; edit its OUTPUT first.

The readable first block implies IV `0000000537068053`. The original timestamp
pair was not recovered. Native AES replay confirms the chosen key/IV's output,
not uniqueness or external flag acceptance. The account-name key is corroborated
by the PDB path, readable later CBC blocks, and valid PKCS#7 padding.

The hidden time source is the last-write time of the System.evtx file. It is
not a direct read of the wall clock. The writeup records the corresponding
code and extraction point.
