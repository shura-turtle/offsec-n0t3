---
title: "jq"
weight: 21
bookToc: true
---

**Use for:** reading JSON API responses, filtering records and decoding log structure.  
**Run in:** WSL.

## Inspect structure

```bash
jq . response.json                    # Pretty print
jq 'keys' response.json               # Top-level object keys
jq 'type' response.json               # Object, array, string, etc.
jq '.items | length' response.json    # Count records
```

## Extract fields

```bash
jq -r '.flag' response.json           # String without JSON quotes
jq -r '.items[].name' response.json   # Names inside an array
jq '.items[] | select(.id == 7)' response.json
jq -r '.items[] | [.id, .name] | @tsv' response.json
```

## CTF: search nested text values

```bash
# Unknown schema: inspect all string values for a clue
jq -r '.. | strings | select(test("flag|secret"; "i"))' response.json

# Missing field fallback
jq -r '.flag // .message // "no matching field"' response.json
```

## Handle JSON Lines and encoded JSON

```bash
# One JSON object per line
jq 'select(.status == 200)' events.jsonl

# A field that itself contains JSON text
jq '.payload | fromjson' response.json

# Supply a string without shell interpolation inside the filter
jq --arg name 'alice' '.items[] | select(.name == $name)' response.json
```

## Gotchas

- Bash single quotes protect jq’s `$variables` from shell expansion.
- `-r` emits text and can lose JSON type/quoting information.
- jq parses JSON; HTML error responses will fail.

## Flags and filter operators explained

| Syntax | Meaning |
| --- | --- |
| `-r` | Emit string results without JSON quotes |
| `-c` | Compact each JSON result onto one line |
| `-s` | Read all input JSON values into one array |
| `-R` | Read each input line as a raw string rather than parsing JSON |
| `-n` | Run without consuming JSON input |
| `--arg NAME VALUE` | Define a jq string variable safely |
| `--argjson NAME JSON` | Define a variable containing parsed JSON |
| `.items[]` | Emit each element/value from items |
| `select(CONDITION)` | Keep values satisfying a condition |
| `//` | Fallback for null/false values |
| `..` | Recursively visit values |
| `@tsv` / `@csv` | Format an array as one TSV/CSV record |

The `|` inside a quoted jq filter is jq’s pipeline. An unquoted shell `|` connects separate processes.

## CTF: find a key when the schema is unknown

```bash
jq 'paths(scalars) as $p | {path: $p, value: getpath($p)}' response.json
```

This keeps field locations with their values. A plain `.. | strings` search loses that context.

## CTF: find duplicate and unique identifiers

```bash
jq '[.items[].id] | unique' response.json
jq '.items | group_by(.owner) | map({owner: .[0].owner, count: length})' response.json
```

Useful for understanding ownership or repeated records before testing a web authorization hypothesis.

## CTF: select a numeric ID safely

```bash
jq --argjson wanted 7 '.items[] | select(.id == $wanted)' response.json
```

`--arg wanted 7` defines a string `"7"`; `--argjson wanted 7` defines the number `7`. JSON type differences can explain an empty result.

## CTF: handle keys containing dots

```bash
jq -r '.["id.orig_h"]' zeek_record.json
```

`.id.orig_h` instead traverses nested objects and is a different lookup.

## CTF: turn raw lines into JSON strings

```bash
jq -R . candidate_strings.txt > candidate_strings.jsonl
jq -Rs . multiline_text.txt > one_json_string.json
```

`-R` reads raw lines; `-Rs` slurps the raw input as one string. These preserve quoting for later scripts without using `eval` or shell interpolation.

## Troubleshoot empty or invalid output

| Result | Check |
| --- | --- |
| `null` | Wrong/missing field path |
| No records | Filter condition or wrong JSON types |
| Parse error | HTML error, truncated JSON or non-JSON prefix |
| Cannot iterate over null | Missing array; inspect structure first |
| Many unexpected values | Recursive filter too broad; keep paths/context |

Reference: [jq manual](https://jqlang.org/manual/).
