---
title: "OpenSSH-Session-Key-Recovery"
weight: 32
bookToc: true
---

**Use for:** recovering SSH cipher keys and IVs from a Linux memory image.  
**Run in:** the supplied Volatility 3 installation in WSL. This entry is a plugin, not an independent CLI.

## Required inputs

- Linux memory containing the relevant OpenSSH process/session state.
- Matching Linux kernel symbols for Volatility.
- Plugin `openssh_sessionkeys.py` and its `openssh32`/`openssh64` symbol files.
- A matching PCAP if the challenge also requires traffic decryption.

## Discover the installed plugin

```bash
# From the supplied Volatility directory
python3 vol.py -h | grep -i ssh
python3 vol.py -f /path/to/linux.raw linux.pslist
```

## Recover keys from sshd

```bash
# For a plugin integrated under the linux namespace
python3 vol.py -f /path/to/linux.raw \
  linux.openssh_sessionkeys.SSHKeys --name sshd --out /tmp/ssh_keys.jsonl
```

Use the exact name listed in `-h`. An externally loaded plugin may appear as `openssh_sessionkeys.SSHKeys` instead.

## External plugin/symbol directories

```bash
# Discover names using the organizer's actual plugin and symbol paths
python3 vol.py -p /path/to/plugins -s /path/to/symbols -h

# Then use the reported name and the same -p/-s global options
```

`--pid 1234` can select a specific process instead of `--name sshd`. The upstream plugin writes one JSON object per line with `--out`.

## Interpret the result

Record the cipher name, key, IV, PID and session context. These are session encryption values, not the user’s login password. Recovering keys is only one stage; traffic decryption also needs correct direction, cipher/framing and capture context. Standard TLS key-log settings do not decrypt SSH.

Compatibility depends on the supplied plugin, Volatility API and OpenSSH structures.

## Flags explained

| Flag | Meaning |
| --- | --- |
| `-f IMAGE` | Volatility input memory image |
| `-p DIR` | Additional Volatility plugin search path |
| `-s DIR` | Additional symbol search path |
| `--name sshd` | This plugin's process-name selector |
| `--pid N` | This plugin's PID selector |
| `--out FILE` | This plugin's JSON Lines output file |
| `-h` | Discover framework/plugin options |

`--out` belongs to this plugin. Volatility’s global `-o DIR` selects a directory for plugins that use its file-output interface; it is not interchangeable with this plugin’s filename argument.

## CTF: establish that the prerequisites are satisfied

1. Identify the memory image and Linux kernel banner.
2. Run `linux.pslist` successfully with matching kernel symbols.
3. Find the relevant `sshd` process/PID.
4. Confirm the SSH plugin appears in Volatility help.
5. Confirm the required OpenSSH structure symbols are available.
6. Run the plugin against a selected process and preserve complete output.

Do not treat a plugin import failure as evidence that no session keys remain in memory.

## CTF: inspect a selected process

```bash
python3 vol.py -f /path/to/linux.raw linux.pslist
python3 vol.py linux.openssh_sessionkeys.SSHKeys -h
python3 vol.py -f /path/to/linux.raw \
  linux.openssh_sessionkeys.SSHKeys --pid 1234 --out /tmp/pid1234_keys.jsonl
```

Replace the name with the installed plugin identifier and PID with the image’s relevant process. Upstream filtering expects a PID/name selection to choose processes; use an explicit selector.

## CTF: inspect recovered records with jq

```bash
jq -c '{task_name, cipher_name, key, iv}' /tmp/pid1234_keys.jsonl
jq -r '[.cipher_name, .key, .iv] | @tsv' /tmp/pid1234_keys.jsonl
```

The key and IV values are hex text representing bytes. Count decoded bytes with Python if needed; the correct size depends on the negotiated cipher.

## Correlate keys with the captured SSH session

Use the process/time context, endpoint pair and negotiated algorithm from the PCAP. A host can have multiple SSH sessions and keys for different directions or rekey intervals. A candidate structure is useful only when it matches the session being reconstructed.

## Why a recovered key may not directly decode the PCAP

SSH has packet framing, authentication, sequence numbers and potentially rekeying. Cipher suites have different key/nonce/state requirements. This repository’s recovery plugin is not a universal PCAP decryption command. Use an organizer-supplied compatible decryptor if provided, or implement the documented session format with the exact captured context.

## Failure categories

| Failure | Meaning to investigate |
| --- | --- |
| Plugin absent from help | Search path/import or compatibility |
| Kernel requirement unsatisfied | Memory/symbol layer setup |
| OpenSSH symbol lookup fails | Plugin-specific symbols/path |
| No selected tasks | Wrong PID/name or process no longer present |
| No keys in a valid selected task | Missing pages, freed state or unsupported structures |
| Keys found but bytes remain wrong | Session/direction/cipher/framing/rekey context |

References: [project setup](https://github.com/fox-it/OpenSSH-Session-Key-Recovery), [plugin options and output](https://github.com/fox-it/OpenSSH-Session-Key-Recovery/blob/main/volatility3/openssh_sessionkeys.py).
