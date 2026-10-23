#!/usr/bin/env python3
"""Run a byte-exact TCP conversation from a JSON plan; Python standard library."""
import argparse
import json
import socket
import sys
import time
from pathlib import Path


class TCPReader:
    """Preserve bytes received beyond a delimiter for the next protocol read."""

    def __init__(self, sock):
        self.sock = sock
        self.buffer = bytearray()
        self.eof = False

    def read_until(self, delimiter, timeout, max_bytes):
        if not delimiter:
            raise ValueError('delimiter cannot be empty')
        deadline = time.monotonic() + timeout
        while True:
            index = self.buffer.find(delimiter)
            if index >= 0:
                end = index + len(delimiter)
                data = bytes(self.buffer[:end])
                del self.buffer[:end]
                return 'delimiter', data
            if len(self.buffer) >= max_bytes:
                return 'limit', bytes(self.buffer)
            if self.eof:
                data = bytes(self.buffer)
                self.buffer.clear()
                return 'eof', data
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return 'timeout', bytes(self.buffer)
            self.sock.settimeout(remaining)
            try:
                data = self.sock.recv(min(65536, max_bytes - len(self.buffer)))
            except socket.timeout:
                return 'timeout', bytes(self.buffer)
            if not data:
                self.eof = True
            else:
                self.buffer.extend(data)

    def read_for(self, seconds, max_bytes):
        """Collect bytes for a bounded interval. Consume partial data on timeout."""
        output = bytearray(self.buffer)
        self.buffer.clear()
        deadline = time.monotonic() + seconds
        while len(output) < max_bytes:
            if self.eof:
                return 'eof', bytes(output)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return 'deadline', bytes(output)
            self.sock.settimeout(remaining)
            try:
                data = self.sock.recv(min(65536, max_bytes - len(output)))
            except socket.timeout:
                return 'deadline', bytes(output)
            if not data:
                self.eof = True
            else:
                output.extend(data)
        return 'limit', bytes(output)


def positive(value):
    number = float(value)
    if not 0 < number < float('inf'):
        raise argparse.ArgumentTypeError('must be a positive finite number')
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host')
    parser.add_argument('port', type=int)
    parser.add_argument('plan', type=Path, help='JSON array of send/read operations')
    parser.add_argument('--timeout', type=positive, default=5)
    parser.add_argument('--max-bytes', type=int, default=8 * 1024 * 1024)
    parser.add_argument('--transcript', type=Path, help='also save exact bytes as JSONL hex')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or args.max_bytes < 1:
        parser.error('port must be 1..65535 and max-bytes must be positive')
    try:
        plan = json.loads(args.plan.read_text(encoding='utf-8'))
        if not isinstance(plan, list):
            raise ValueError('plan must be a JSON array')
        allowed = {'send_text', 'send_hex', 'send_file', 'read_until_hex', 'read_for', 'shutdown_write'}
        for action in plan:
            if not isinstance(action, dict) or len(allowed.intersection(action)) != 1:
                raise ValueError('each action must contain exactly one send/read operation')
            operation = next(iter(allowed.intersection(action)))
            if operation in {'send_text', 'send_hex', 'send_file', 'read_until_hex'} and not isinstance(action[operation], str):
                raise ValueError(f'{operation} must be a string')
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    try:
        transcript = args.transcript.open('w', encoding='utf-8') if args.transcript else None
    except OSError as exc:
        parser.error(str(exc))

    def emit(action, status, data=b'', **metadata):
        record = {'action': action, 'status': status, 'length': len(data),
                  'hex': data.hex(), 'text': data.decode('utf-8', errors='backslashreplace'), **metadata}
        line = json.dumps(record, ensure_ascii=True)
        print(line, flush=True)
        if transcript:
            transcript.write(line + '\n')
            transcript.flush()

    try:
        try:
            connection = socket.create_connection((args.host, args.port), timeout=args.timeout)
        except socket.timeout:
            emit('connect', 'timeout')
            return 2
        except OSError as exc:
            emit('connect', 'connection_error', detail=str(exc))
            return 2
        with connection:
            reader = TCPReader(connection)
            emit('connect', 'connected')
            for index, action in enumerate(plan):
                name = next(iter(allowed.intersection(action)))
                timeout = float(action.get('timeout', args.timeout))
                if not 0 < timeout < float('inf'):
                    raise ValueError('action timeout must be positive and finite')
                if name.startswith('send_'):
                    if name == 'send_text':
                        data = action[name].encode(action.get('encoding', 'utf-8'))
                    elif name == 'send_hex':
                        data = bytes.fromhex(action[name])
                    else:
                        path = Path(action[name])
                        if not path.is_absolute():
                            path = args.plan.parent / path
                        data = path.read_bytes()
                    connection.settimeout(timeout)
                    connection.sendall(data)
                    emit(name, 'sent', data, step=index)
                elif name == 'shutdown_write':
                    connection.shutdown(socket.SHUT_WR)
                    emit(name, 'write_closed', step=index)
                elif name == 'read_until_hex':
                    delimiter = bytes.fromhex(action[name])
                    status, data = reader.read_until(delimiter, timeout, args.max_bytes)
                    emit(name, status, data, step=index, buffered_preview=status in {'timeout', 'limit'})
                    if status == 'limit' or (status == 'timeout' and not action.get('allow_timeout', False)):
                        return 3
                    if status == 'eof':
                        return 4
                else:
                    seconds = float(action[name])
                    if not 0 < seconds < float('inf'):
                        raise ValueError('read_for duration must be positive and finite')
                    status, data = reader.read_for(seconds, args.max_bytes)
                    emit(name, status, data, step=index)
                    if status == 'limit':
                        return 3
                    if status == 'eof' and index != len(plan) - 1:
                        return 4
            return 0
    except (OSError, ValueError, TypeError, LookupError) as exc:
        emit('session', 'error', detail=str(exc))
        return 2
    finally:
        if transcript:
            transcript.close()


if __name__ == '__main__':
    sys.exit(main())
