## Protected API Usage with Token Generation and Refresh
### OIDC tokens
OpenID Connect (OIDC) is a standard way for an application to prove “who is calling” when accessing a protected API. Instead of sending a username/password to every API, the application first gets a token from an Identity Provider (the login system). The API then accepts requests only when a valid token is included.

A token is like a short-lived digital pass. Tokens usually expire (often in minutes), so systems either:
* Get a new token again, or
* Refresh the token using a “refresh token” (when allowed).

### The main token types
1) Access Token (most important for API calls)

This is what you send to the API (usually in an Authorization: Bearer ... header).
   It is short-lived for safety.
   If it’s expired, the API will reject the call (e.g., 401 Unauthorized).
2) Refresh Token (used to renew access without asking the user again)

This is a longer-lived “renewal pass”.

### Common ways to get an initial access token
1) Client Credentials Flow (machine-to-machine)

This is used when a system/service is calling an API without a user involved. So, no details about the user is provided.

2) Authorization Code Flow (with user login)

This is used when a real person is logging in (web apps, native apps). The user is redirected to the login page and signs in.

This flow often returns: access_token and refresh_token.

PKCE Method(for public apps): Some apps can’t safely store a client secret (e.g., mobile apps). PKCE is an extra protection layer used with Authorization Code Flow so the app can securely exchange the code without needing a client secret.

### Refreshing tokens

When an access token expires, the application can request a new one from the token endpoint (tokenUrl) without asking the user to log in again, as long as it has a valid refresh token.

What is required to refresh a token:
* `grant_type=refresh_token`
* refresh_token (from the initial token response)
* scope
* client_id
* client_secret (only if your client has one)

This project provides examples of generating and refreshing tokens, along with API usage samples in multiple languages including R, Python, and Groovy. These examples are intended to help you understand how token creation and refresh work in practice.
