---
title: "OpenVPN Client"
weight: 4
bookToc: true
---

**Use for:** connecting the competition PC to the challenge network.  
**Run in:** Windows OpenVPN client. These steps describe OpenVPN Connect.

## Connect

1. Get the organizer’s `.ovpn` profile and any supplied credentials.
2. Open OpenVPN Connect → import a profile from a file.
3. Select the `.ovpn`, enter required credentials and connect.
4. Confirm the client reports **Connected**.
5. Open a supplied challenge endpoint in Chrome.

## Check Windows connectivity

```powershell
ipconfig
route print

# Replace with the assigned challenge host and port
Test-NetConnection 192.0.2.10 -Port 443
```

## If Windows works but WSL does not

```bash
# WSL: inspect addresses and route selection
ip addr
ip route
ip route get 192.0.2.10
```

Check the same endpoint from Windows and WSL. VPN routing and DNS can differ between them. Share that distinction with competition support if the provided setup fails.

## Gotchas

- A failed ping does not prove the endpoint is down; ICMP may be blocked.
- Authentication failure, TLS/profile failure and a missing route are different problems.
- Keep the client connected while working on VPN endpoints.
- OpenVPN GUI and OpenVPN Connect have different menus; use the installed client’s import control.

## Supporting command parameters explained

| Command / parameter | Meaning |
| --- | --- |
| `Test-NetConnection HOST` | Diagnose connectivity to the selected host |
| `-Port N` | Test TCP connection to port N |
| `-InformationLevel Detailed` | Show additional diagnostic fields |
| `route print` | Display Windows routing tables |
| `ip route get HOST` in WSL | Show the route selected for that destination |

These commands diagnose the network. OpenVPN Connect itself is controlled through its imported profile and GUI in this workflow.

## CTF: diagnose a challenge endpoint in layers

1. Confirm the VPN client reports a connected tunnel.
2. Check the challenge IP/hostname is the latest assigned endpoint.
3. Inspect the Windows route and DNS result where relevant.
4. Test the actual TCP service port.
5. Repeat the same check inside WSL if the solver runs there.
6. Only debug the solver payload after endpoint availability is established.

```powershell
# Hostname lookup, then TCP reachability
Resolve-DnsName challenge.example
Test-NetConnection 192.0.2.10 -Port 8080 -InformationLevel Detailed
```

Replace both placeholders. A TLS/HTTP application can reject a request even after TCP succeeds; keep those outcomes separate.

## Read client errors by category

| Message category | Investigate |
| --- | --- |
| Authentication failure | Supplied username/password or profile credentials |
| Certificate/time validation | Correct profile, certificate validity and PC time |
| Tunnel connected but host unreachable | Route, endpoint availability or firewall |
| IP works, hostname fails | DNS configuration |
| Windows works, WSL fails | WSL routing/DNS interaction with the VPN |

## Keep stateful solves alive

Do not disconnect/reimport a working profile during an active protocol challenge without preserving session evidence. A VPN reconnect can close the underlying TCP/UDP state and invalidate a partially completed sequence.

## Endpoint rotation workflow

When a supplied solver receives no data, distinguish connection refusal, timeout and EOF. Do one minimal liveness check. If the instance expired, retry the unchanged solver on the refreshed endpoint before changing payload assumptions.

## Useful support record

```text
VPN client: <Connect/GUI and installed build>
tunnel status: <connected/error text>
assigned endpoint: <host:port>
Windows test: <TCP outcome>
WSL test: <TCP outcome>
time of test: <timezone included>
```

Reference: [OpenVPN Connect profile import](https://openvpn.net/connect-docs/import-profile.html).

## Related playbooks

- [Network starting workflow](../../network-expl/)
- [Persistent TCP/UDP sessions](../../network-expl/tcp-udp/)
