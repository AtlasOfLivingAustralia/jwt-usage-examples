## Protected API Usage with Token Generation and Refresh
Example scripts showing JWT token usage and refresh based on a user provided JSON file containing the response from an initial JWT token creation e.g. `keys_example.json`.

The script will attempt to make a request to a protected ALA API. If the token in the JSON file is not expired, it will send the token with the request. If the token has expired,

1. New token will be generated against the tokenUrl using the `refresh_token` and `scope` from the JSON file along with  `clientId`, `clientSecret` supplied in the CLI. If the Client App was registered without `clientSecret`, it is not required. 

2. New token will be kept in memory and used for subsequent request and will again if updated upon expiry.

The token refresh operation described can be successfully run regardless of whether the initial token was generated using just the simple Client Credentials or Client Credential AND User credentials e.g. Authorization Code Flow, Implicit Flow, Password Credentials etc. In both cases, no user credentials is required for token refresh  - only the `clientId`, and optionally `clientSecret` is required. If the Client App was registered without `clientSecret`, it is not required. 

### Python
Use command token_refresh -h for help. 
Example usage CAS Prod: `python3 python/token_refresh.py --file ./keys_example.json --tokenUrl https://auth.ala.org.au/cas/oidc/oidcAccessToken --clientId replaceMe --clientSecret replaceMe`
Example usage CAS Test: `python3 python/token_refresh.py --file ./keys_example.json --tokenUrl https://auth-test.ala.org.au/cas/oidc/oidcAccessToken --clientId replaceMe --clientSecret replaceMe`
Example usage Cognito Test: `python3 python/token_refresh.py --file ./keys_example.json --tokenUrl https://auth-secure.auth.ap-southeast-2.amazoncognito.com/oauth2/token --clientId replaceMe --clientSecret replaceMe`
Example usage Cognito Test without client secret: `python3 python/token_refresh.py --file ./keys_example.json --tokenUrl https://auth-secure.auth.ap-southeast-2.amazoncognito.com/oauth2/token --clientId replaceMe`

### Groovy