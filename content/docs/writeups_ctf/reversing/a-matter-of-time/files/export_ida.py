"""Run with File -> Script file in the supplied IDA database.

Edit OUTPUT first. This exports the current IDB; it does not unpack an EXE.
"""
import base64
import json
from pathlib import Path

import idaapi
import ida_bytes
import idautils

OUTPUT = Path('/tmp/a-matter-of-time-ida-segments.json')

segments = {}
for start in idautils.Segments():
    end = idaapi.getseg(start).end_ea
    data = ida_bytes.get_bytes(start, end - start)
    if data is None:
        raise RuntimeError(f'Cannot read segment at {start:#x}')
    segments[hex(start)] = base64.b64encode(data).decode('ascii')

OUTPUT.write_text(json.dumps(segments))
print(f'Exported {len(segments)} mapped segments to {OUTPUT}')
