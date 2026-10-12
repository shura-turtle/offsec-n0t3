---
title: "Dmp Hunt4c2"
weight: 1
# bookFlatSection: false
# bookToc: true
# bookHidden: false
# bookCollapseSection: false
# bookComments: false
# bookSearchExclude: false
# bookHref: ''
# bookIcon: ''
---

# DMP Hunt4C2 — .NET Memory Dump Analysis

This walkthrough follows a .NET application from its call stack to its heap objects, then recovers an encrypted message from a Google Calendar event stored in memory.

The workflow:

```text
Identify the .NET runtime
  → Find application objects and crypto fields
  → Recover the application assembly
  → Decompile the message-handling code
  → Read a Calendar event description from the heap
  → Decrypt the recovered message
```

The addresses below come from this dump. For another dump, use the addresses returned by your own commands. Names such as `CRYPTO_OBJECT_ADDRESS` and `BASE_ADDRESS` are placeholders to replace before running a command.

## 1. Set up WinDbg and SOS

Open the dump in WinDbg. Run these commands in the command box, one at a time:

```text
.symfix
.reload
!eeversion
!clrstack
```

| Command | Purpose |
| --- | --- |
| `.symfix` | Configure the Microsoft symbol server. |
| `.reload` | Reload symbols using the configured symbol path. |
| `!eeversion` | Display runtime and SOS version information; a successful response also confirms that SOS is responding. |
| `!clrstack` | Display the current thread's managed call stack. |

If WinDbg cannot find the SOS commands, try loading SOS beside CoreCLR:

```text
.loadby sos coreclr
!eeversion
!clrstack
```

This loading method requires `sos.dll` to be available beside `coreclr.dll`. If it fails, load your installed SOS extension using its actual path:

```text
.load C:\path\to\sos.dll
```

The stack contains `coreclr` and `System.Private.CoreLib`, which identify a modern .NET runtime. We use SOS to inspect managed memory and ILSpy or dnSpy to inspect the application code.

## 2. Find application objects

Start with a summary of the managed heap:

```text
!dumpheap -stat
```

Look for application-specific types among the framework types. In this dump, two useful leads are:

```text
CSG2025_RC_Crypto
CSG2025_RC_Com
```

Search for objects whose type names contain `CSG`:

```text
!dumpheap -type CSG
```

The object rows include an **Address** column and an **MT** column. Use the object address with `!do`:

```text
!do CRYPTO_OBJECT_ADDRESS
```

**Use the Address column here.** MT is the MethodTable address, which identifies the object's type; it is not the address of that object instance.

### Read the crypto fields

Inspecting the Crypto object revealed these fields:

```text
key
iv
xorKey
```

Follow each field's reference from the **Value** column. For a byte-array field, inspect its elements with:

```text
!dumparray ARRAY_OBJECT_ADDRESS
```

For a string field, use:

```text
!do STRING_OBJECT_ADDRESS
```

The heap contains the values present at the time of capture. We can recover those runtime values before understanding how the application originally encoded or decoded them.

For the final AES decryption in this walkthrough, the recovered values are:

```python
key = b"rA8fT6YzX2pQ4eM9vW1kLdB3"
iv = b"uJ7nP0xR3aH5bG2q"
```

The supplied notes do not include an `xorKey` value. It is not needed by the final decryption script shown below.

## 3. Locate the application method

Inspect the native stack and the managed stack:

```text
k
!clrstack
```

The relevant native stack excerpt is:

```text
 # Child-SP          RetAddr               Call Site
03 00000088`3979e8f0 00007ffd`a216580a     ws2_32!recv+0xc1
04 00000088`3979e990 00007ffd`a21651f0     System_Net_Sockets!Interop.Winsock.recv+0xca
05 00000088`3979ea60 00007ffd`a2164def     System_Net_Sockets!System.Net.Sockets.Socket.Receive+0x180
06 00000088`3979eae0 00007ffd`a2164b63     System_Net_Sockets!System.Net.Sockets.NetworkStream.Read+0x9f
07 00000088`3979eb60 00007ffe`01309864     System_Private_CoreLib!System.IO.StreamReader.ReadBuffer+0x63
08 00000088`3979ebb0 00007ffd`a2161d74     System_Private_CoreLib!System.IO.StreamReader.ReadLine+0x64
09 00000088`3979ec60 00007ffd`a2161949     CSG2025_Reversing_Challenge!CSG2025_Reversing_Challenge.CSG2025_RC_Srv.RemoteShell+0x404
```

`RemoteShell` is calling `ReadLine`, which reaches the socket receive path. This suggests the thread was waiting for input when the dump was captured.

The **RetAddr** on the `ReadLine` row is `00007ffda2161d74`. That is the return location in its caller, `RemoteShell`, so it gives us an address inside the application's JIT-compiled method.

Resolve that code address with:

```text
!ip2md 00007ffda2161d74
```

Relevant output:

```text
MethodDesc:   00007ffda2229398
Method Name:  CSG2025_Reversing_Challenge.CSG2025_RC_Srv.RemoteShell(Int32)
Class:        00007ffda2212528
MethodTable:  00007ffda22293d8
mdToken:      000000000600000C
Module:       00007ffda21ee0a0
IsJitted:     yes
Current CodeAddr: 00007ffda2161970
```

The field we need next is **Module**:

```text
00007ffda21ee0a0
```

## 4. Export and decompile the assembly

Inspect the module:

```text
!dumpmodule 00007ffda21ee0a0
```

Find its `BaseAddress`. Create `C:\Analysis` on your analysis machine if necessary, then replace `BASE_ADDRESS` below with the reported value:

```text
!savemodule BASE_ADDRESS C:\Analysis\recovered.dll
```

The Module address from `!ip2md` identifies the runtime module structure. `!savemodule` needs the loaded image's base address, which is reported by `!dumpmodule`.

Open `recovered.dll` in **ILSpy** or **dnSpy**, then trace:

| Method or class | What to inspect |
| --- | --- |
| `RemoteShell` | How commands are received and their results handled. |
| `CSG2025_RC_Crypto` | How crypto values are decoded and messages encrypted. |
| `CSG2025_RC_Com` | Where the message is stored and how it is sent. |

Microsoft documents the object, array, method, and module inspection commands in its [SOS command reference](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/sos-debugging-extension).

## 5. Trace the Google Calendar message storage

In the decompiler, open:

```text
CSG2025_RC_Com → AppendTextToEvent()
```

The method retrieves a Calendar event:

```csharp
Event @event = service.Events.Get(text, eventId).Execute();
```

The namespace import identifies the `Event` type:

```csharp
using Google.Apis.Calendar.v3.Data;
```

Its fully qualified name is:

```text
Google.Apis.Calendar.v3.Data.Event
```

The method appends the message to the event's description:

```csharp
@event.Description = @event.Description + textToAppend + "\n";
```

It then updates the Calendar event:

```csharp
service.Events.Update(@event, text, eventId).Execute();
```

`@event` is the local variable name. `Event` is its type. Searching the heap by the full type name lets us find event objects that may still contain the message.

These are decompiled code excerpts; we do not need to execute them or contact Google Calendar to read an event already present in the dump.

## 6. Recover the encrypted description

Search for Calendar event objects:

```text
!dumpheap -type Google.Apis.Calendar.v3.Data.Event
```

From the results, identify the MethodTable for the exact `Event` type. In this dump it is `00007ffda2480c38`.

List only the addresses of instances of that type:

```text
!dumpheap -mt 00007ffda2480c38 -short
```

Output:

```text
0210af14b758
0210af1bcba0
0210af25d740
```

Inspect the second event:

```text
!do 0210af1bcba0
```

Find the description's backing field:

```text
Value             Name
00000210af1cc1b8  <Description>k__BackingField
```

The **Value** is a reference to a string object. Follow it:

```text
!do 00000210af1cc1b8
```

The recovered description contains this Base64 ciphertext:

```text
xAYzbKdNTXbilYe1LgMrCwMvP0uu/6uhhT52MCnmzOTh2udnHKqJc/6iD+u9Bd3O
```

If one event has an empty or unrelated description, inspect the other event objects. A description can contain several appended lines; select the ciphertext line you intend to decrypt.

## 7. Decrypt the message

The supplied script uses AES-CBC with a 24-byte key and a 16-byte IV. The key length makes this AES-192.

Install the dependency in your Python environment:

```bash
python -m pip install pycryptodome
```

Save this as `decrypt.py`:

```python
import base64

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

ciphertext = (
    "xAYzbKdNTXbilYe1LgMrCwMvP0uu/6uhhT52MCnmzOTh2udnHKqJc/6iD+u9Bd3O"
)
key = b"rA8fT6YzX2pQ4eM9vW1kLdB3"
iv = b"uJ7nP0xR3aH5bG2q"

# Decode the ciphertext from Base64 into encrypted bytes.
encrypted_bytes = base64.b64decode(ciphertext)

# Decrypt with the recovered runtime key and IV.
cipher = AES.new(key, AES.MODE_CBC, iv)
padded_plaintext = cipher.decrypt(encrypted_bytes)

# Remove PKCS#7 padding and display the UTF-8 message.
plaintext = unpad(padded_plaintext, AES.block_size)
print(plaintext.decode("utf-8"))
```

Run it:

```bash
python decrypt.py
```

Verified output for the supplied ciphertext, key, and IV:

```text
!aB3@dE5#fG7^hI9&jK1*lM2(nO4)pQ6-rS8_tU0+vW
```

This verifies the decryption example. The dump extraction steps above are based on the recorded WinDbg output; the original dump was not re-examined while preparing this writeup.
