# offsec-n0t3

## Run locally

Install Hugo extended, then run from the repository root:

```sh
git submodule update --init --recursive
hugo server -D --disableFastRender
```

Open http://localhost:1313/. The theme lives in the `themes/hugo-book`
Git submodule; an empty theme directory causes missing HTML layout warnings
and prevents Hugo from rendering your notes.

Notes under `content/docs/` appear in the sidebar. Expand the arrows beside
Scripts and picoCTF → Web to see their child pages.

## Build

```sh
hugo
```

This generates the site in `public/`.

## Field reference collections

The source notes live under `content/docs/`:

| Directory | Content |
| --- | --- |
| `web-expl/` | Ordered web probes, engine fingerprints, payloads, extraction and troubleshooting |
| `network-expl/` | Packet/stream triage, DNS, TLS/SSH, Wi-Fi, CAN and protocol sessions |
| `steganograph-expl/` | Images/LSB, archives, audio, PDF/document and Unicode workflows |
| `reversing-expl/` | Native/.NET analysis, Ghidra cheatsheet/extensions, debugger and byte transforms |
| `tools-cheatsheet/` | CyberChef visual recipes, the 39-tool workflow map and snippet library |
| `ajcbbc_allow_tools/` | Existing per-tool command references |

Prepared Python helpers are in `static/snippets/`; Hugo copies them to
`/snippets/` as downloadable files. Their linked notes explain assumptions,
examples and optional dependencies. Most helpers use only the standard library;
image pixel extraction requires Pillow.

The custom layout, CSS, scripts and original pixel artwork live in `layouts/`,
`assets/` and `static/images/`. The theme submodule remains separate. Search,
navigation and code-copy controls use local assets; reference links are optional
further reading. For offline use, run the local Hugo server and keep the theme,
notes, images and snippets available. A saved online tool tab does not replace
an offline installation of that tool.

To check a build without replacing existing `public/` files:

```sh
hugo --destination /tmp/offsec-preview --cacheDir /tmp/offsec-hugo-cache
```
