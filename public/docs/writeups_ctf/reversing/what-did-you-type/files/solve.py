#!/usr/bin/env python3
"""Recover the captured exfiltration offline. No captured executable is run.

Usage: python solve.py /path/to/ctf-2026-challenges-public --out recovered
The image fragment is a manual transcription of the recovered JPG.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def read_blob(data, offset):
    length = u32(data, offset)
    end = offset + 4 + length
    if end > len(data):
        raise ValueError('Truncated serialized blob')
    return data[offset + 4:end], end


def rva_reader(pe):
    nt = u32(pe, 0x3c)
    sections = struct.unpack_from('<H', pe, nt + 6)[0]
    optional_size = struct.unpack_from('<H', pe, nt + 20)[0]
    section_table = nt + 24 + optional_size

    def read(rva, size):
        for index in range(sections):
            section = section_table + 40 * index
            virtual_size, start, raw_size, raw = struct.unpack_from('<IIII', pe, section + 8)
            if start <= rva and rva + size <= start + max(virtual_size, raw_size):
                return pe[raw + rva - start:raw + rva - start + size]
        raise ValueError(f'RVA {rva:#x} is outside file-backed sections')
    return read


def resource(pe, kind, name):
    read = rva_reader(pe)
    nt = u32(pe, 0x3c)
    # PE32+ optional header, resource directory is data-directory index 2.
    root = u32(pe, nt + 24 + 112 + 2 * 8)

    def entries(relative):
        head = read(root + relative, 16)
        count = sum(struct.unpack_from('<HH', head, 12))
        raw = read(root + relative + 16, count * 8)
        return [struct.unpack_from('<II', raw, i * 8) for i in range(count)]

    branch = dict(entries(0))[kind] & 0x7fffffff
    branch = dict(entries(branch))[name] & 0x7fffffff
    leaf = entries(branch)[0][1] & 0x7fffffff
    data_rva, size = struct.unpack_from('<II', read(root + leaf, 16))
    return read(data_rva, size)


def tshark(path, display_filter, fields):
    command = ['tshark', '-r', str(path), '-Y', display_filter, '-T', 'fields']
    for field in fields:
        command += ['-e', field]
    return subprocess.run(command, check=True, capture_output=True, text=True, timeout=60).stdout


def usb_text(rows):
    normal = {i + 4: char for i, char in enumerate('abcdefghijklmnopqrstuvwxyz')}
    normal.update({i + 30: char for i, char in enumerate('1234567890')})
    normal.update({40: '\n', 42: '[BACKSPACE]', 43: '\t', 44: ' ', 45: '-', 46: '=',
                   47: '[', 48: ']', 49: '\\', 51: ';', 52: "'", 53: '`', 54: ',', 55: '.', 56: '/'})
    shifted = {i + 4: char for i, char in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}
    shifted.update({i + 30: char for i, char in enumerate('!@#$%^&*()')})
    shifted.update({45: '_', 46: '+', 47: '{', 48: '}', 49: '|', 51: ':', 52: '"', 53: '~', 54: '<', 55: '>', 56: '?'})
    previous = set()
    output = []
    for line in rows.splitlines():
        _, _, value = line.partition('\t')
        report = bytes.fromhex(value.replace(':', ''))
        if len(report) != 8:
            continue
        current = set(report[2:]) - {0}
        for code in sorted(current - previous):
            table = shifted if report[0] & 0x22 else normal
            output.append(table.get(code, normal.get(code, f'[KEY{code}]')))
        previous = current
    return ''.join(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', type=Path)
    parser.add_argument('--out', type=Path, default=Path('recovered'))
    parser.add_argument('--image-fragment', default='_P3r50n_', help='Transcription of the recovered JPG')
    args = parser.parse_args()
    source = args.repository / 'What did you type' / 'Handout'
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source / 'chall.zip') as archive:
        for name in ('monitor_network', 'monitor_hardware'):
            with archive.open(name, pwd=b'crackmes.one') as stream:
                (out / name).write_bytes(stream.read())

    rows = tshark(out / 'monitor_hardware', 'usb.transfer_type==0x01 && usb.data_len==8',
                  ['frame.number', 'usbhid.data'])
    (out / 'usb-reports.tsv').write_text(rows)
    text = usb_text(rows)
    (out / 'keystrokes.txt').write_text(text)
    password = re.search(r'unzip -P (\S+)', text)[1]
    print('ZIP password from USB:', password)
    with zipfile.ZipFile(io.BytesIO(base64.b64decode((source / 'PbWE.txt').read_bytes()))) as archive:
        module = archive.read('module.exe', pwd=password.encode())
    (out / 'module.exe').write_bytes(module)

    rows = tshark(out / 'monitor_network', 'http', ['frame.number', 'http.file_data'])
    (out / 'http-bodies.tsv').write_text(rows)
    bodies = {}
    for line in rows.splitlines():
        frame, _, value = line.partition('\t')
        if value:
            bodies[int(frame)] = bytes.fromhex(value.replace(':', ''))
    # Frame 8 is the GET response used by the first-stage loader.
    stage_key = bodies[8]
    stage_iv = rva_reader(module)(0xa078, 16)
    shellcode = unpad(AES.new(stage_key, AES.MODE_CBC, stage_iv).decrypt(resource(module, 255, 254)), 16)
    (out / 'stage-shellcode.bin').write_bytes(shellcode)

    # Locate the call/pop accessor for serialized flat-program data.
    accessor = shellcode.index(bytes.fromhex('e800000000584883c008c3'))
    header = accessor + 13
    flat_size = u32(shellcode, header)
    argument_header = header + 4 + flat_size
    arguments, _ = read_blob(shellcode, argument_header)
    mode, unpacked_size = struct.unpack_from('<II', arguments)
    assert mode == 0  # Copy after XOR; no RtlDecompressBuffer call needed.
    encrypted, offset = read_blob(arguments, 8)
    xor_key, offset = read_blob(arguments, offset)
    clear = bytes(byte ^ xor_key[i % len(xor_key)] for i, byte in enumerate(encrypted))
    assert len(clear) == unpacked_size
    label, offset = read_blob(clear, 0)
    exfil, offset = read_blob(clear, offset)
    assert exfil.startswith(b'MZ')
    (out / 'exfil.exe').write_bytes(exfil)
    iv = rva_reader(exfil)(0x6078, 16)

    files = [(16, 32), (43, 54), (65, 77), (88, 103)]
    manifest = []
    for name_frame, data_frame in files:
        name = bodies[name_frame].decode('ascii')
        assert Path(name).name == name
        encrypted = bodies[data_frame]
        key = hashlib.sha256(encrypted[:4]).digest()
        padded = AES.new(key, AES.MODE_CBC, iv).decrypt(encrypted[4:])
        clear = unpad(padded, 16)
        assert AES.new(key, AES.MODE_CBC, iv).encrypt(padded) == encrypted[4:]
        (out / name).write_bytes(clear)
        manifest.append({'name': name, 'frame': data_frame, 'prefix': encrypted[:4].hex(),
                         'length': len(clear), 'sha256': hashlib.sha256(clear).hexdigest()})
        print(f'Recovered frame {data_frame}: {name} ({len(clear)} bytes)')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))

    with zipfile.ZipFile(out / 'IDK_why_I_saved_this.xlsx') as archive:
        root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
        beginning = next(element.text for element in root.iter() if element.text and element.text.startswith('CMO{'))
    with zipfile.ZipFile(out / 'Cool_Story.docx') as archive:
        root = ET.fromstring(archive.read('word/header2.xml'))
        ending = next(element.attrib['string'] for element in root.iter()
                      if element.tag.endswith('}textpath') and 'string' in element.attrib)
    print('XLSX fragment:', beginning)
    print('JPG fragment (manual transcription):', args.image_fragment)
    print('DOCX fragment:', ending)
    flag = beginning + args.image_fragment + ending
    (out / 'flag.txt').write_text(flag + '\n')
    print(flag)


if __name__ == '__main__':
    main()
