This package contains python scripts for generating OIDC access tokens using Authorization Code method or client credentials
method and refreshing them.

### Prerequisites:
Fill the configs in config.json file.


### Usage

There are four example scenarios:
1. Example of using `Authorization_code` grant type -  See `token_generation_using_auth_code.py`
2. Example of using `Client_credentials` grant type - See `token_generation_using_client_credentials.py`
3. Example of refreshing the existing access token - See `token_refresh.py`
4. Example of generating a JWT and use it to invoke an API - See `example_app.py`