#!/usr/bin/env python3
"""Invert a documented toy byte-check; replace the model with recovered instructions.

Forward: y[i] = ROL8(((x[i] XOR key) + i) modulo 256, rotation).
Stdlib default inverse; optional --z3 requires separately permitted z3-solver.
"""
import argparse


def rol8(value, count):
    count %= 8
    return ((value << count) | (value >> ((8-count) % 8))) & 255


def forward(data, key, rotation):
    return bytes(rol8(((b ^ key) + i) & 255, rotation) for i,b in enumerate(data))


def inverse(target, key, rotation):
    return bytes(((rol8(b, -rotation) - i) & 255) ^ key for i,b in enumerate(target))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target-hex', help='expected transformed bytes; default built-in demo')
    p.add_argument('--key', type=lambda s:int(s,0), default=0x23)
    p.add_argument('--rotation', type=int, default=3)
    p.add_argument('--encode-text', help='forward-transform this UTF-8 string instead')
    p.add_argument('--z3', action='store_true', help='solve same model with optional z3-solver')
    ns = p.parse_args()
    try:
        if not 0 <= ns.key <= 255:
            raise ValueError('key must fit one byte')
        if ns.encode_text is not None:
            print(forward(ns.encode_text.encode(), ns.key, ns.rotation).hex())
            return
        target = bytes.fromhex(ns.target_hex) if ns.target_hex is not None else forward(b'flag{demo}', ns.key, ns.rotation)
        if ns.z3:
            try:
                import z3
            except ImportError:
                p.exit(2, 'error: --z3 requires separately installed/permitted z3-solver\n')
            values = [z3.BitVec(f'x{i}',8) for i in range(len(target))]
            solver = z3.Solver()
            for i, (x, y) in enumerate(zip(values,target)):
                solver.add(z3.RotateLeft((x ^ ns.key) + (i & 255), ns.rotation % 8) == y)
            if solver.check() != z3.sat:
                p.exit(1, 'unsatisfiable model\n')
            model = solver.model()
            answer = bytes(model.eval(x,model_completion=True).as_long() for x in values)
        else:
            answer = inverse(target, ns.key, ns.rotation)
        if forward(answer, ns.key, ns.rotation) != target:
            raise ValueError('forward verification failed')
        print(answer.hex())
        print(repr(answer))
    except ValueError as exc:
        p.exit(2, f'error: {exc}\n')


if __name__ == '__main__':
    main()
