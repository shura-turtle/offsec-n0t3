---
title: "cannelloni"
weight: 17
bookToc: true
---

**Use for:** tunneling CAN frames over an IP network into a local SocketCAN interface.  
**Run in:** WSL with a working CAN/vcan interface. Use with [can-utils](../can_utils/).

## Check the supplied build

```bash
cannelloni -h
ip -details link show vcan0
```

## Connect to a challenge CAN endpoint

```bash
# Example values only: replace IP and both ports with organizer values
cannelloni -I vcan0 -R 192.0.2.10 -r 20000 -l 20001
```

| Option | Purpose |
| --- | --- |
| `-I vcan0` | Local CAN interface |
| `-R ADDRESS` | Remote IP address |
| `-r PORT` | Remote destination port |
| `-l PORT` | Local listening port |
| `-d cut` | CAN, UDP and timer debugging |

The remote endpoint must send back to your chosen local port. Match the supplied transport and addressing.

## Observe the tunneled traffic

```bash
# Second terminal; keep cannelloni running
candump -tz vcan0
candump -L vcan0 > challenge_can.log
```

## TCP mode when explicitly supplied

```bash
# Build must support this option; use the challenge's remote port
cannelloni -I vcan0 -C c -R 192.0.2.10 -r 20000
```

## Gotchas

- UDP can lose or reorder frames.
- VPN routes, firewall rules and WSL networking can prevent return traffic.
- No frames? Check the CAN interface, protocol and ports before editing payloads.
- Cannelloni carries frames; it does not decode application command meanings.

## Additional options explained

| Option | Meaning |
| --- | --- |
| `-I IFACE` | Use this local SocketCAN interface |
| `-R IP` | Set the remote peer address |
| `-r PORT` | Send to the peer’s listening port |
| `-l PORT` | Bind the local receiving port |
| `-C c` / `-C s` | TCP client / server mode, if supported |
| `-S c` / `-S s` | SCTP client / server mode, if supported |
| `-d cut` | Debug categories: CAN, UDP and timers |
| `-t N` | Aggregation timeout in microseconds for supported transports |

Uppercase `-I` is the interface; lowercase `-l` is the local port. TCP/SCTP support and switches depend on the supplied build.

## CTF: reason about two endpoints

```text
Your WSL side: local port 20001, remote port 20000
Challenge side: local port 20000, remote port 20001
```

Each peer’s destination must match the other peer’s actual reachable listening port. NAT/VPN/WSL forwarding can change what the remote can reach; use the organizer’s addressing instructions.

## CTF: bring up and inspect a local tunnel

```bash
# Terminal 1: keep running for the full challenge session
cannelloni -I vcan0 -R 192.0.2.10 -r 20000 -l 20001 -d cut

# Terminal 2: observe CAN messages delivered through that tunnel
candump -tz vcan0
```

Do not stop the tunnel after the first frame or ACK. Stateful devices can emit success/status messages later.

## Capture only after the tunnel is ready

```bash
candump -L vcan0 > tunneled_capture.log
```

Keep the capture running during one known interaction. Note its start time and the exact action, then examine changes in the relevant IDs.

## Failure decision table

| Observation | Likely area to investigate |
| --- | --- |
| No vcan0 | Kernel/interface setup |
| Peer connection cannot be established | VPN route, transport and endpoint |
| Outgoing traffic, no return frames | Return address/port, NAT or remote state |
| Local CAN frames but no objective change | Application semantics/setup/checksum |
| Intermittent missing responses | UDP loss, timing or rate mismatch |
| TCP option rejected | Different version/build capabilities |

## Preserve the protocol sequence

Record the command’s documented meaning, required mode/state, payload format and expected reply. Transport success means frames moved; challenge success must be established by its own state/output.

Reference: [upstream usage and transports](https://github.com/mguentner/cannelloni). The tournament list points to a fork; use the installed build’s help if options differ.
