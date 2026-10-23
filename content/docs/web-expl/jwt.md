---
title: "JWT · Claims, Algorithms & Keys"
weight: 41
bookToc: true
---

# JWT attacks

**Decode → identify consumer → test signature enforcement → inspect key selection → check claims.** Base64url decoding reveals data; it does not recover the signing key.

## 1. Recognize the format

A common signed compact token has three dot-separated parts:

```text
BASE64URL(header).BASE64URL(payload).BASE64URL(signature)
```

A five-part token may be encrypted JWE; do not apply three-part JWS edits blindly. Opaque random session strings are a different format.

Example decoded data:

```json
{"alg":"HS256","typ":"JWT"}
```

```json
{"sub":"12","role":"user","iss":"ctf-app","aud":"web","exp":1900000000}
```

Use an available offline Base64url/JWT inspector. Ordinary base64 uses `+/` while base64url uses `-_`; padding is commonly omitted. JSON formatting changes signed bytes. Do not upload live challenge tokens to public decoding websites.

## 2. Baseline and first controlled edit

```http
GET /api/me HTTP/1.1
Host: ctf.invalid
Authorization: Bearer ORIGINAL_TOKEN
```

Edit **one claim** (for example `role`) without recomputing the signature, then send the same request and a protected admin route. If accepted as admin, the consumer may decode without verification. Check a signature-bit-flipped token too. A frontend displaying the changed role is not enough.

| Result | Next move |
| --- | --- |
| Modified payload accepted | Verify backend resource and identify which consumer fails validation |
| Invalid signature rejected | Expected; inspect key/algorithm selection |
| All tokens return same data | Session cookie may override bearer token; remove conflicting credentials |
| Token rejected before signature | Bad Base64url, JSON, expiry, issuer or audience |

## 3. Unsigned `alg: none`

Decoded header candidate:

```json
{"alg":"none","typ":"JWT"}
```

Encoded header:

```text
eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0
```

Token shape after editing your payload:

```text
eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.EDITED_PAYLOAD_BASE64URL.
```

The trailing dot denotes an empty signature segment. This tests an implementation that accepts unsecured tokens. Correctly configured verifiers reject it. Trying case variations is only relevant to a demonstrably inconsistent parser; it is not an expected library feature.

## 4. HS256 weak or exposed secret

HMAC uses the same secret for signing and verification. Inspect challenge source, environment examples, backups, framework defaults and provided config for the **actual** secret. A public RSA key is not an HMAC secret unless algorithm confusion exists.

Signing input is exactly the ASCII bytes:

```text
BASE64URL(header) + "." + BASE64URL(payload)
```

Signature is `BASE64URL(HMAC-SHA256(secret, signing_input))`. Use a permitted offline token editor's signing feature when available. Do not guess hundreds of secrets manually without a hint. Weak-secret recovery is an offline attack, distinct from the server accepting unsigned tokens.

## 5. RSA → HMAC algorithm confusion

Prerequisites:

1. Original token uses an asymmetric algorithm such as RS256.
2. Its verification public key is available (often a published JWKS).
3. The verifier accepts HS256 while reusing that public-key material as an HMAC key.
4. Your signing tool can sign HS256 using the **exact expected key bytes**.

Candidate decoded header:

```json
{"alg":"HS256","typ":"JWT","kid":"current-key"}
```

Sign the edited payload with public-key bytes as HMAC secret. PEM headers, line endings and a trailing newline affect the bytes. A JWK object, DER key and PEM key are different representations. Modern libraries usually separate key types and allowed algorithms; a published public key by itself is normal and not a vulnerability.

## 6. `kid`: untrusted key lookup

```json
{"alg":"HS256","kid":"test-key"}
{"alg":"HS256","kid":"../../dev/null"}
{"alg":"HS256","kid":"known-empty-file"}
```

The traversal candidate requires a file-based lookup that concatenates `kid` into a path and reads it as secret bytes. A nonexistent file usually causes rejection. `/dev/null` only helps if the implementation accepts the resulting empty key; many libraries reject it.

If source shows SQL lookup by concatenation, `kid` may be SQLi; use the actual query context from [SQLi](../sqli/). If it selects from an in-memory map, path traversal and SQLi do not apply. Observe a controlled lookup difference before constructing a forged token.

## 7. Embedded/remote key headers

Header examples to inspect, not complete tokens:

```json
{"alg":"RS256","jku":"https://YOUR-LAB-HOST/jwks.json","kid":"ctf-key"}
```

```json
{"alg":"RS256","jwk":{"kty":"RSA","kid":"ctf-key","n":"YOUR_MODULUS","e":"AQAB"}}
```

A verifier that trusts an attacker-supplied `jwk` can verify a token signed by your corresponding private key. A verifier fetching an arbitrary `jku` may trust your hosted JWKS or introduce SSRF. Neither works simply by adding the header; key selection must consume it. Certificates through `x5c` have similar trust requirements.

JWT header `jku` is not automatically used by ordinary middleware. A fixed issuer/JWKS configuration may ignore it completely. Any callback host must be allowed by the challenge.

## 8. Claim validation, token confusion and revocation

| Claim/condition | Manual check |
| --- | --- |
| `exp` | An actually expired signed token should be rejected after allowed clock skew |
| `nbf` | A valid signed future token should not work before its activation time |
| `iss` | A token from your second test issuer should not be accepted accidentally |
| `aud` | Token for a different service should not authorize this API |
| `sub` | Role/identity must bind to server state as intended |
| Token type | Password-reset / email-verification token should not work as an API token |
| Logout/password change | Replay your own old token; distinguish expected stateless behavior |

You cannot test arbitrary `exp` changes with an invalid signature and conclude time validation works or fails. A different valid token or signing capability is needed. Unix timestamps are usually seconds, not milliseconds.

## 9. Completion evidence

Record original algorithm, verification behavior, key source, edited claims and the protected resource returned. A decoded token, a new UI badge or a `200` error envelope does not prove privilege. Avoid storing real account tokens in shared notes.

## Tool workflow

Use [Burp Community Repeater](../../ajcbbc_allow_tools/burp_suite_community/) for paired manual requests. Keep the baseline in one tab and change one input in another. Browser-only behavior such as XSS, cookies and CORS still needs a real browser proof.

## References

[JWT best current practices — RFC 8725](https://www.rfc-editor.org/rfc/rfc8725), [JWS compact format — RFC 7515](https://www.rfc-editor.org/rfc/rfc7515), [PortSwigger JWT attacks](https://portswigger.net/web-security/jwt).
