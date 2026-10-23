---
title: "07 · CAN / Cannelloni"
weight: 7
bookToc: true
---

# CAN Bus: Observe, Decode, Then Change State

**Flow:** verify interface → establish tunnel if supplied → record baseline → decode ID/data semantics → send one known frame → monitor the actual outcome.

**Tools:** [can-utils](../../ajcbbc_allow_tools/can_utils/), [cannelloni](../../ajcbbc_allow_tools/cannelloni/), [WSL](../../ajcbbc_allow_tools/wsl/), [Wireshark](../../ajcbbc_allow_tools/wireshark/), [Python](../../ajcbbc_allow_tools/python3/).

## 1. Identify the provided transport

| Input | Start |
| --- | --- |
| candump text log | Parse timestamp/interface/ID/data offline |
| CAN PCAP/PCAPNG | Inspect decoded CAN fields in Wireshark |
| SocketCAN interface | candump on the supplied interface |
| IP/port described as cannelloni | Match UDP/TCP mode and return addressing |
| Arbitrary custom TCP service | Read protocol before treating it as raw CAN |

Classic CAN and CAN FD have different payload limits. A CAN identifier is not automatically a sender ID; its interpretation comes from the application protocol.

| Frame family | Identifier | Maximum data |
| --- | --- | --- |
| Classic CAN | Standard 11-bit or extended 29-bit | 8 bytes |
| CAN FD | Standard 11-bit or extended 29-bit | 64 bytes; encoded lengths are discrete |

A CAN FD data-length code is not simply its byte length for larger payloads. Use the decoded frame length from the supplied tool/protocol rather than interpreting the code as an arbitrary count.

## 2. Check the local interface

```bash
ip -details link show vcan0
candump -h
cannelloni -h
```

WSL needs a kernel supporting the provided CAN workflow. Installed binaries alone do not create SocketCAN support.

For an organizer-provided virtual bus setup, the usual Linux commands are:

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set dev vcan0 up
```

Skip creation if the interface already exists. Do not change a supplied real CAN interface's bitrate or state without the challenge setup instructions.

## 3. Keep the tunnel alive

```bash
cannelloni -I vcan0 -R 192.0.2.10 -r 20000 -l 20001
```

| Option | Meaning |
| --- | --- |
| `-I` | Local SocketCAN interface |
| `-R` | Remote peer IP |
| `-r` | Remote destination port |
| `-l` | Local receiving port |

Use the exact transport/addressing supplied by the organizer. The receiving side must be reachable through the VPN/WSL/firewall path. UDP sending without receiving is not proof that the remote service processed a frame.

Keep cannelloni running while you observe and interact in another terminal. If a supplied build uses TCP mode, use its documented switches rather than sending TCP to a UDP endpoint.

## 4. Capture a baseline and one action

```bash
candump -tz vcan0
candump -L vcan0 > baseline.log
```

Stop the baseline capture after a useful interval, then record a separate known action into a separate log. Compare IDs, rates, lengths, and changing bytes. Keep logs separate so timing and sequence are clear.

```text
(1700000000.100000) vcan0 123#11223344
 timestamp          bus   ID  data bytes
```

`-L` writes replay-compatible text to stdout; `-l` has a different file-logging behavior. Inspect installed help before mixing flags.

## 5. Interpret bytes from evidence

Questions to answer before sending:

- Standard 11-bit ID or extended 29-bit ID?
- Classic CAN, CAN FD, or remote-request frame?
- Counter, checksum, sequence, command, sensor value, or bitfield?
- Little-endian or big-endian numeric field?
- Scaling/offset and signedness?
- Required mode, enable/arm step, heartbeat, or authenticated session?

```python
payload = bytes.fromhex('3412000000000000')
print(int.from_bytes(payload[:2], 'little'))  # 0x1234
print(int.from_bytes(payload[:2], 'big'))     # 0x3412
```

Neither interpretation is correct by appearance alone. Match a DBC, source, protocol description, or controlled known-action comparison.

## 6. Send one known frame

```bash
cansend vcan0 123#11223344
```

This is illustrative: ID `0x123`, four data bytes. Substitute a frame whose meaning and preconditions you have established. A visible echo on the local interface can be local loopback rather than remote success.

Keep candump running after transmission. Watch status/telemetry changes and the service's final result. An ACK does not prove the requested physical/logical state completed.

## 7. Replay only the relevant log

```bash
canplayer -I action.log
canplayer -I captured_can0.log vcan0=can0
```

The interface mapping is destination=source. Confirm timing and frame sequence against the challenge protocol. Replaying an entire capture can include resets or inverse actions that undo the desired state.

Counters/checksums/nonces can invalidate stale frames. A replay failing does not disprove the meaning of the command bytes; compare live protocol state.

## 8. Stateful binary protocol lesson

For MAVLink or any other dialect carried by a challenge, resolve message and command IDs against that dialect before assigning meaning. For example, MAVLink command 176 is `MAV_CMD_DO_SET_MODE`, not “mission start.” Mode selection, arming, and a later reposition/action can be separate steps; a flag may arrive asynchronously in a status message.

Do not treat MAVLink as CAN merely because both appear in a network challenge. The transport and application framing still determine how bytes must be sent and decoded.

## Failure decision table

| Symptom | Check next |
| --- | --- |
| Interface absent | Kernel/setup instructions |
| Tunnel running, no frames | Transport, remote/local ports, route, return path |
| Local echo only | Remote telemetry or state evidence |
| ACK but state unchanged | Preconditions, mode, enable/arm, asynchronous status |
| Replayed frame rejected | Counter, checksum, session, freshness |
| Garbage numeric values | Endianness, signedness, scaling, bitfields |

Completion means the service's objective or final status is verified while the session remains alive.

References: [can-utils upstream](https://github.com/linux-can/can-utils), [cannelloni upstream](https://github.com/mguentner/cannelloni), [MAVLink command definitions](https://mavlink.io/en/messages/common.html#MAV_CMD_DO_SET_MODE).
