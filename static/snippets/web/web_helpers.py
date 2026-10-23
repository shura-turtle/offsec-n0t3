#!/usr/bin/env python3
"""Offline CTF byte transforms and JWT inspection. Standard library only.

JWT inspection does NOT verify a signature. No network requests are made.
"""

import argparse
import base64
import binascii
import hashlib
import hmac
import json
import sys
from pathlib import Path
from urllib.parse import quote_from_bytes, unquote_to_bytes


def b64url_decode(value):
    raw = value.encode("ascii")
    return base64.b64decode(raw + b"=" * (-len(raw) % 4), altchars=b"-_", validate=True)


def b64url_encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def read_input(args):
    if args.file is not None:
        return Path(args.file).read_bytes()
    if args.text is not None:
        return args.text.encode("utf-8")
    return sys.stdin.buffer.read()


def transform(operation, data, key_hex=None):
    if operation == "hex-encode":
        return data.hex().encode()
    if operation == "hex-decode":
        return bytes.fromhex(data.decode("ascii"))
    if operation == "b64-encode":
        return base64.b64encode(data)
    if operation == "b64-decode":
        return base64.b64decode(b"".join(data.split()), validate=True)
    if operation == "b64url-encode":
        return b64url_encode(data).encode()
    if operation == "b64url-decode":
        return b64url_decode(data.decode("ascii").strip())
    if operation == "url-encode":
        return quote_from_bytes(data, safe="").encode()
    if operation == "url-decode":
        return unquote_to_bytes(data)
    if operation == "form-decode":
        return unquote_to_bytes(data.replace(b"+", b" "))
    if operation == "xor":
        if key_hex is None:
            raise ValueError("xor requires --key-hex (e.g. 42 or 494345)")
        key = bytes.fromhex(key_hex)
        if not key:
            raise ValueError("XOR key must not be empty")
        return bytes(byte ^ key[i % len(key)] for i, byte in enumerate(data))
    if operation == "hashes":
        return json.dumps({name: hashlib.new(name, data).hexdigest()
                           for name in ("md5", "sha1", "sha256")}, indent=2).encode()
    if operation == "jwt-inspect":
        parts = data.decode("ascii").strip().split(".")
        if len(parts) != 3:
            raise ValueError("expected three JWT segments (JWS), not encrypted JWE")
        result = {
            "warning": "DECODED ONLY: signature, issuer, audience and time claims NOT verified",
            "header": json.loads(b64url_decode(parts[0])),
            "payload": json.loads(b64url_decode(parts[1])),
            "signature_hex": b64url_decode(parts[2]).hex(),
        }
        return json.dumps(result, indent=2, ensure_ascii=True).encode()
    raise ValueError("unknown operation")


def sign_hs256(header, payload, key):
    """Construct a token with a KNOWN key; not a key recovery function."""
    if not isinstance(header, dict) or not isinstance(payload, dict):
        raise ValueError("JWT header and payload must be JSON objects")
    if header.get("alg") != "HS256":
        raise ValueError("header alg must be HS256")
    segments = [b64url_encode(json.dumps(item, separators=(",", ":")).encode())
                for item in (header, payload)]
    message = ".".join(segments).encode("ascii")
    return message.decode() + "." + b64url_encode(hmac.new(key, message, hashlib.sha256).digest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=(
        "hex-encode", "hex-decode", "b64-encode", "b64-decode",
        "b64url-encode", "b64url-decode", "url-encode", "url-decode",
        "form-decode", "xor", "hashes", "jwt-inspect", "jwt-sign-hs256"))
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", help="exact UTF-8 input, without an added newline")
    source.add_argument("--file", help="binary input file; default is stdin")
    parser.add_argument("--key-hex", help="XOR key bytes written as hex")
    parser.add_argument("--key-file", help="exact raw HMAC key file for known-key signing")
    parser.add_argument("--output", help="write raw output to file instead of stdout")
    args = parser.parse_args()
    try:
        data = read_input(args)
        if args.operation == "jwt-sign-hs256":
            if not args.key_file:
                raise ValueError("known-key signing requires --key-file")
            spec = json.loads(data)
            output = sign_hs256(spec["header"], spec["payload"],
                                Path(args.key_file).read_bytes()).encode()
        else:
            output = transform(args.operation, data, args.key_hex)
        if args.output:
            Path(args.output).write_bytes(output)
        else:
            sys.stdout.buffer.write(output)
    except (ValueError, KeyError, TypeError, OSError, UnicodeError, binascii.Error) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
