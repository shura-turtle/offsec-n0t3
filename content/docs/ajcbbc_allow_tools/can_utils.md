---
title: "can-utils"
weight: 16
bookToc: true
---

**Use for:** CAN bus capture, payload inspection and replay in automotive CTFs.  
**Run in:** WSL with SocketCAN support. `can0` is a real interface; `vcan0` is a virtual interface.

## Prepare a virtual practice bus

```bash
# Requires kernel vcan support and permission to create interfaces
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set dev vcan0 up
ip -details link show vcan0
```

If `modprobe` or interface creation fails, the provided WSL kernel may lack support. Use the organizer’s supplied CAN setup.

## Read frames

```bash
# Terminal 1: watch timestamped frames
candump -tz vcan0

# Save frames in canplayer-compatible log format
candump -L vcan0 > capture.log

# Show only standard CAN ID 0x123
candump 'vcan0,123:7FF'
```

## Send one known frame

```bash
# Terminal 2: ID 0x123, four payload bytes
cansend vcan0 123#11223344
```

Classic CAN uses up to eight payload bytes. Decode the challenge protocol before assigning meaning to an ID or changing bytes.

## Replay a captured log

```bash
# For a log already recorded on vcan0
canplayer -I capture.log

# Map a log's can0 frames onto local vcan0
canplayer -I capture.log vcan0=can0
```

## CTF workflow

Capture a baseline → perform one action → compare IDs and changing payload bytes → replay the relevant frames → watch the challenge’s resulting state. A transmitted frame alone does not prove the objective completed.

## Flags explained by utility

| Command / option | Meaning |
| --- | --- |
| `candump -t z` or `-tz` | Show timestamps relative to the beginning of this capture |
| `candump -L` | Print canplayer-compatible log records to stdout |
| `candump -l` | Write an automatically named log file |
| `candump -n 100` | Stop after 100 received frames |
| `candump -x` | Print extra message information, including direction where available |
| `canplayer -I FILE` | Read replay data from a log file |
| `canplayer -g MS` | Configure its replay gap setting; check installed help for timing behavior |
| `cansend IFACE FRAME` | Send one encoded frame; interface/frame are positional arguments |

`-L` and `-l` are different. Options belong to the named utility, not the can-utils collection as a whole.

## Read a CAN frame

```text
vcan0  123   [4]  11 22 33 44
       │     │    └─ four data bytes
       │     └────── payload length
       └──────────── hexadecimal CAN identifier
```

The identifier can describe an arbitration ID rather than a command number. Application semantics must come from the challenge protocol, code or observed behavior.

## CTF: observe a controlled action

```bash
# Record a bounded sample before changing any challenge state
candump -L -n 100 vcan0 > baseline.log

# In a separate run, perform one known action while capturing
candump -L -n 100 vcan0 > action.log
```

Compare message rates and changed bytes. A periodic counter/checksum can change independently of the action.

## CTF: compare values for one CAN ID

```bash
# Filter standard ID 0x123; mask 0x7FF covers its 11 ID bits
candump -L -n 50 'vcan0,123:7FF' > id123.log
```

For extended IDs and exact frame-flag filtering, inspect candump’s filter syntax rather than reusing an 11-bit mask blindly.

## CTF: decode a possible little-endian sensor value

```python
payload = bytes.fromhex("34120000")
raw = int.from_bytes(payload[:2], "little")
print(raw)                 # 4660
print(raw * 0.1)           # Example scale only
```

The `0.1` scaling factor is an example, not an inferred protocol rule. Confirm signedness, scaling, counters and checksums against known states.

## CTF: replay only after understanding the state

If a supplied log is known to solve the challenge, replay that unchanged first. Otherwise identify required mode/session/setup actions and preserve their order. Continue watching status frames after transmission until the objective is confirmed.

## Diagnose an empty capture

```bash
ip -details -statistics link show vcan0
candump -h
canplayer -h
```

Check interface existence/up state, tunnel routing, chosen ID filter and whether the remote actually emits traffic. A CAN interface can be up while a tunnel is disconnected.

References: [can-utils](https://github.com/linux-can/can-utils), [candump options](https://github.com/linux-can/can-utils/blob/master/candump.c), [canplayer options](https://github.com/linux-can/can-utils/blob/master/canplayer.c).

## Related playbooks

- [CAN bus state and replay](../../network-expl/can-bus/)
