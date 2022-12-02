## Protected API Usage with Token Generation and Refresh
A simple example script showing JWT token usage and refresh based on a provided JSON file containing the response from an initial JWT token creation. 

The script will attempt to make a request to a protected ALA API. If the token in the JSON file is not expired, it will send the token with the request. If the token has expired,

1. New token will be generated against the tokenUrl using the `refresh_token` and `scope` from the JSON file along with  `clientId`, `clientSecret` supplied in the CLI.
2. New token will be kept in memory and used for subsequent request and will again if updated upon expiry.

The token refresh operation described can be successfully run regardless of whether the initial token was generated using just the simple Client Credentials or Client Credential AND User credentials e.g. Authorization Code Flow, Implicit Flow, Password Credentials etc. In both cases, no user credentials is required for token refresh  - only the `clientId`, `clientSecret` is required.

### Python
Use command token_refresh -h for help. 
Example usage: `python3 generate_token.py --file ./keys.json --tokenUrl https://auth-test.ala.org.au/cas/oidc/oidcAccessToken --clientId replaceMe --clientSecret replaceMe`
