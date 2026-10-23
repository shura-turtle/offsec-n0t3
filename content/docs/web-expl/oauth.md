---
title: "OAuth / Account Linking"
weight: 42
bookToc: true
---

# OAuth and Account Linking

**Map who issues each value and which browser/session it belongs to.** A `code`, access token, ID token, email claim, and application session cookie are different credentials.

## 1. Record the whole normal flow

```text
Browser → client /login
Client → provider /authorize
Provider → client callback?code=...&state=...
Client server → provider token endpoint
Client → authenticated application session
```

Typical authorization request:

```http
GET /authorize?response_type=code&client_id=client123&redirect_uri=https%3A%2F%2Fctf.invalid%2Fcallback&scope=openid%20profile&state=RANDOM_STATE&code_challenge=PKCE_CHALLENGE&code_challenge_method=S256 HTTP/1.1
Host: provider.ctf.invalid

```

Capture the actual URL. Note `state`, `nonce` for OpenID Connect, and PKCE challenge/verifier if present. Never infer which controls are enforced just because a parameter appears.

## 2. Test state binding

Using your own lab accounts and fresh authorization codes, test separately:

```text
callback with correct state
callback with missing state
callback with wrong state
callback state from a different browser session
```

| Result | Next question |
| --- | --- |
| Invalid/missing state rejected | State check exists; inspect session binding |
| Callback accepts wrong state | Potential login CSRF / link CSRF |
| Error after token exchange | Code may already be consumed; generate a fresh one |
| Same callback reused works without code validation | Investigate session/cache behavior separately |

Missing `state` alone is not a full exploit proof: other flow binding, including correct PKCE enforcement, may prevent the attack. Demonstrate the wrong account/session being linked or logged in.

## 3. Redirect URI validation

Start from the registered callback and change one component at a time:

```text
https://ctf.invalid/callback
https://ctf.invalid/callback/extra
https://ctf.invalid/callback?next=https://YOUR-LAB-HOST/
https://ctf.invalid.evil.invalid/callback
https://ctf.invalid@YOUR-LAB-HOST/callback
```

The last two hosts are different from `ctf.invalid`; they test naive string validation. `YOUR-LAB-HOST` must be replaced with a challenge-permitted endpoint if a real callback is needed.

Do not assume an accepted alternate URI leaks a credential. Follow the actual redirect, determine whether it contains code or token, and whether another binding prevents redemption.

An [open redirect](../open-redirect/) on an allowed callback origin may form a chain. The provider and client may normalize paths/queries differently, so capture the final URL and request.

## 4. Account linking

Check whether the application links a provider identity using:

```text
issuer + subject        stable provider identity
email only              risky if verification/issuer trust is absent
client-supplied email   directly tamperable if trusted
```

Test the linking endpoint while signed out and with the wrong local account. Confirm whether reauthentication is required. Using your two accounts, verify which account receives the provider link before calling the flow vulnerable.

## 5. Token and identity checks

| Token | What to inspect |
| --- | --- |
| Authorization code | One-time use, redirect URI/client binding, expiry, PKCE |
| Access token | Audience/resource, scopes, expiry; not necessarily a JWT |
| ID token | Signature, issuer, audience, nonce, expiry |
| Application session | Session rotation and actual local user identity |

Do not treat a decodable JWT as verified. See [JWT](../jwt/). Do not replace OAuth tokens with another user's tokens outside the authorized challenge accounts.

## Tools

[Burp](../../ajcbbc_allow_tools/burp_suite_community/) captures redirects and callbacks. [Chrome](../../ajcbbc_allow_tools/google_chrome/) gives separate browser profiles and storage inspection. [CyberChef](../../ajcbbc_allow_tools/cyberchef/) decodes URL/Base64URL layers.

References: [OAuth security best current practice RFC 9700](https://www.rfc-editor.org/rfc/rfc9700), [PKCE RFC 7636](https://www.rfc-editor.org/rfc/rfc7636), [PortSwigger OAuth](https://portswigger.net/web-security/oauth).
