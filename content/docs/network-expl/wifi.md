---
title: "06 · Wi-Fi Capture Analysis"
weight: 6
bookToc: true
---

# Wi-Fi Captures with the Approved Tools

**Flow:** verify link-layer capture → identify AP/station → inspect security/handshake → use supplied key material → inspect decrypted traffic.

**Tools:** [Wireshark](../../ajcbbc_allow_tools/wireshark/), [TShark](../../ajcbbc_allow_tools/tshark/), [Python](../../ajcbbc_allow_tools/python3/), [CyberChef](../../ajcbbc_allow_tools/cyberchef/). No aircrack installation is assumed.

## 1. Check what was captured

```text
wlan
radiotap
eapol
```

A normal Ethernet capture from a Wi-Fi-connected computer may contain only already-decapsulated traffic. It will not necessarily contain 802.11 management frames, channel information, or the wireless handshake.

Use **Statistics → Protocol Hierarchy** and inspect the link-layer tree of a frame. Note whether the file contains radiotap + 802.11, Ethernet, Linux cooked capture, or another encapsulation.

## 2. Identify the access point and station

```text
wlan.fc.type == 0
wlan.fc.type_subtype == 0x08
wlan.ssid
wlan.bssid == 02:00:00:00:00:01
wlan.addr == 02:00:00:00:00:02
```

The beacon subtype filter helps locate advertised networks. Inspect SSID and BSSID in the decoded tree. An SSID can be empty/hidden; correlate association/probe traffic rather than inventing a name.

```bash
tshark -r wireless.pcapng -Y 'wlan.ssid' -T fields \
  -E header=y -E separator=/t \
  -e frame.number -e wlan.bssid -e wlan.ssid
```

For each candidate, record:

| Field | Why it matters |
| --- | --- |
| SSID bytes | Passphrase-to-key derivation depends on the SSID |
| BSSID | Distinguishes APs with the same SSID |
| Station MAC | Identifies which handshake/session to inspect |
| Security advertisement | WEP, WPA/WPA2, WPA3, enterprise context differ |
| Channel / capture span | Missing channel/time can explain absent handshake |

MAC addresses can be randomized or spoofed; treat them as capture identifiers, not proof of a person's identity.

## 3. Inspect authentication and key exchange

```text
eapol
wlan.fc.type_subtype == 0x0b
wlan.fc.type_subtype == 0x00
```

Look at the AP/station pair and ordering. Retransmitted handshake frames are not automatically different sessions. If a challenge supplies a password, a usable WPA/WPA2-Personal handshake and relevant traffic are still needed to derive/decode the session correctly.

Different Wi-Fi modes require different secrets and capture context. A WPA3-SAE session is not passively decrypted by applying the same WPA2 password-only assumption. Use the installed Wireshark guidance for the actual mode.

## 4. Use a supplied WPA/WPA2-Personal password

In Wireshark:

```text
Edit -> Preferences -> Protocols -> IEEE 802.11
Enable decryption
Decryption Keys -> Edit -> Add
Key type: wpa-pwd
Key: supplied_password:ExactSSID
```

Wireshark's key syntax permits URI-style escapes for problematic characters; a literal colon in a password/SSID needs the documented escaping. Do not split it at the wrong separator.

Reload/revisit the matching session and inspect whether IP/application protocol fields appear. “Key added” is not proof decryption worked.

## 5. Derive a WPA2-Personal PMK offline

This calculates a known passphrase's derived key; it does not crack a handshake or recover a password.

```python
import hashlib
passphrase = 'provided-passphrase'.encode('utf-8')
ssid = b'ExactSSID'
pmk = hashlib.pbkdf2_hmac('sha1', passphrase, ssid, 4096, 32)
print(pmk.hex())
```

Use the exact passphrase encoding and SSID bytes. A 64-hex-digit WPA PSK is already key material; it is not a passphrase to run through this derivation again. PMK knowledge alone does not resolve every missing-handshake or unsupported-mode problem.

## 6. Distinguish wireless from application encryption

```text
802.11 protection removed
  -> IP visible
     -> TLS still encrypted
        -> HTTP content still unavailable without TLS secrets
```

Decrypting the Wi-Fi layer does not decrypt HTTPS. After IP protocols appear, continue to [TLS/SSH](../tls-ssh/) or [HTTP](../http-streams/) as appropriate.

## 7. When the password does not help

| Observation | Check |
| --- | --- |
| No 802.11 frames | Capture may already be Ethernet/decapsulated |
| Many SSIDs | Select exact BSSID/station/session |
| Handshake absent | Capture may start too late or miss a channel |
| Key accepted but no plaintext | Mode, password/SSID bytes, handshake, supported cipher |
| Frames marked malformed | Capture encapsulation/FCS assumptions; inspect actual bytes |
| IP visible but no web content | Application encryption or non-HTTP protocol |

Do not change “Ignore Protection bit” or FCS options at random. These settings are for particular capture-driver representations; compare the link-layer structure and documented capture method.

## 8. Other wireless evidence

Probe names, SSIDs, vendor-specific information elements, and EAP identity fields can contain challenge clues. Preserve raw bytes and identify the exact management frame/field before decoding. Apparent readable content may be an unrelated neighboring network.

## Completion checkpoint

Record input capture, AP/station pair, security mode, key source, handshake frame references, and a verified decrypted packet. Export any resulting application object with the matching protocol's workflow.

Reference: [Wireshark wireless decryption guidance](https://wiki.wireshark.org/HowToDecrypt802.11) for supported modes, key syntax, and capture prerequisites.
