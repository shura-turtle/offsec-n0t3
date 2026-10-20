---
title: "Eric Zimmerman's Tools"
weight: 39
bookToc: true
---

**Use for:** Windows artifact parsing and forensic timelines.  
**Run in:** Windows PowerShell, from the directory containing the supplied executables. Available tools/builds depend on the organizer’s installation.

## Choose a parser

| Artifact | Tool | What it helps answer |
| --- | --- | --- |
| Prefetch `.pf` | PECmd | Program execution traces |
| Event logs `.evtx` | EvtxECmd | Logons, process/service events |
| NTFS `$MFT` / `$J` | MFTECmd | File records and filesystem changes |
| Shortcut `.lnk` | LECmd | Target path and link metadata |
| Jump Lists | JLECmd | Recently accessed application items |
| Registry hives | RECmd / Registry Explorer | Configuration and user activity |
| Generated CSV | Timeline Explorer | Sort/filter parsed results |

## Parse execution and event artifacts

```powershell
# Replace C:\CTF\evidence with your extracted artifact folder
.\PECmd.exe -d 'C:\CTF\evidence\Prefetch' --csv 'C:\CTF\out\prefetch'
.\EvtxECmd.exe -d 'C:\CTF\evidence\evtx' --csv 'C:\CTF\out\events'
```

## Parse filesystem and recent-file traces

```powershell
# Single quotes preserve the literal $MFT name in PowerShell
.\MFTECmd.exe -f 'C:\CTF\evidence\$MFT' --csv 'C:\CTF\out\mft'
.\LECmd.exe -d 'C:\CTF\evidence\Recent' --csv 'C:\CTF\out\lnk'
.\JLECmd.exe -d 'C:\CTF\evidence\AutomaticDestinations' --csv 'C:\CTF\out\jumplists'
```

## CTF walkthrough

1. Identify the supplied artifact, then select its parser.
2. Run `TOOL.exe -h` for the installed build’s options.
3. Export CSV into a separate output folder.
4. Open it in Timeline Explorer if supplied, or inspect it with PowerShell:

```powershell
Get-ChildItem 'C:\CTF\out' -Recurse -Filter *.csv
Import-Csv 'C:\CTF\out\events\chosen-output.csv' | Select-Object -First 5
```

Correlate timestamps, paths, users and IDs across artifacts. Prefetch presence supports execution analysis but does not alone establish who ran a program or its intent.

## Flags explained by parser

| Option | Meaning |
| --- | --- |
| `-f FILE` | Parse one supplied artifact file |
| `-d DIR` | Parse an artifact directory where the selected parser supports it |
| `--csv DIR` | Write CSV output into a directory |
| `--csvf NAME` | Override the CSV filename where supported |
| `--json DIR` | Write JSON output where supported; verify format with help |
| `-h` | Show the selected executable's options |
| `RECmd --bn FILE` | Use a Registry batch-definition file |

These are separate programs. A switch supported by PECmd is not automatically supported by another parser. `--csv` normally takes a directory, not the desired complete CSV filename.

## CTF: program execution from Prefetch

```powershell
.\PECmd.exe -d 'C:\CTF\evidence\Prefetch' `
  --csv 'C:\CTF\out\prefetch' --csvf prefetch.csv

Import-Csv 'C:\CTF\out\prefetch\prefetch.csv' | Select-Object -First 5
```

Inspect executable name/path clues, run count and available run times. Prefetch is one execution artifact; corroborate with event/process activity and file traces.

## CTF: filter Windows event results

```powershell
.\EvtxECmd.exe -d 'C:\CTF\evidence\evtx' `
  --csv 'C:\CTF\out\events' --csvf events.csv

$Events = Import-Csv 'C:\CTF\out\events\events.csv'
$Events | Select-Object -First 1 | Format-List *
$Events | Where-Object { $_.EventId -in '4624','4688','7045' }
```

Confirm exported column names on your installed build. Event meaning depends on provider/channel: 4624 is a Security logon event, 4688 is Security process creation when audited, and 7045 is a Service Control Manager service-install event. Missing events can reflect logging policy or incomplete collection.

## CTF: search parsed records by a clue

```powershell
Get-ChildItem 'C:\CTF\out' -Recurse -Filter *.csv |
  Select-String -Pattern 'flag\{|secret|powershell' -CaseSensitive:$false
```

`-Recurse` searches child folders, `-Filter` restricts filenames, and `Select-String -Pattern` searches text. A match inside CSV text is a lead; parse the corresponding record and inspect its fields.

## CTF: registry batch processing

```powershell
# Use a supplied batch definition that exists on the PC
.\RECmd.exe -d 'C:\CTF\evidence\hives' `
  --bn 'C:\Tools\RECmd\BatchExamples\RECmd_Batch_MC.reb' `
  --csv 'C:\CTF\out\registry'
```

PowerShell uses a backtick for multiline continuation. Do not add whitespace after it.

Choose an existing approved batch file and actual installation path. Batch output reports artifacts defined by that file; it is not a complete interpretation of every registry key.

## CTF: join recent-file traces

Compare LNK targets, Jump List paths, MFT entries and Prefetch execution traces around the relevant time. Several artifacts mentioning a path can support a sequence, but timestamp types and update behavior differ.

## Timeline interpretation checklist

Keep the exported timestamp field name, timezone, source artifact and record ID. Sort a copy in Timeline Explorer; do not overwrite original exports. State which artifact directly shows an action and which only provides supporting context.

References: [tool catalog](https://ericzimmerman.github.io/), [PECmd](https://github.com/EricZimmerman/PECmd), [EvtxECmd](https://github.com/EricZimmerman/evtx), [MFTECmd](https://github.com/EricZimmerman/MFTECmd), [LECmd](https://github.com/EricZimmerman/LECmd), [JLECmd](https://github.com/EricZimmerman/JLECmd), [RECmd](https://github.com/EricZimmerman/RECmd).
