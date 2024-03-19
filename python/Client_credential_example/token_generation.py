import json
import argparse
import requests
import jwt
import time

# global to store current token info
token_config = {}

def main():
    filepath = parse_input()

    # read token JSON file
    read_token_file(filepath)

    api_example_request()

def parse_input():

    parser = argparse.ArgumentParser(description="This script uses (and re-generated if needed) a JSON Web Token (JWT) for requests to protected ALA services. A a JSON file containing the initially generated token, regeneration and expiry details is expected as an argument", add_help=True, allow_abbrev=True,)

    # required non-positional arguments for filepath
    parser.add_argument('--file', type=str, help="Path to the JSON file containing the jwt access token, expiry and re-generation details", required=True, nargs='?')

    args = parser.parse_args()

    return args.file

# read the JSON file and save to global token_config
def read_token_file(filepath):
    with open(filepath) as f:
        file_obj = json.load(f)
        # add just required values from JSON file to global token_config
        token_config["client_id"] = file_obj["client_id"]
        token_config["client_secret"] = file_obj["client_secret"]
        token_config["grant_type"] = file_obj["grant_type"]
        token_config["scope"] = file_obj["scope"]
        token_config["token_url"] = file_obj["token_url"]

def get_token():
    payload = {'client_id': token_config["client_id"], 'client_secret': token_config["client_secret"], 'grant_type': token_config["grant_type"], 'scope': token_config["scope"]}
    r = requests.post(token_config["token_url"], data=payload, auth=(token_config["client_id"], token_config["client_secret"]))
	
    if r.ok:
        data = r.json()
        token_config["access_token"] = data["access_token"]
        print("Token was generated")
    else:
        print("Unable to refresh access token. ", r.status_code, r.content)


def api_example_request():
    # get the JWT
    get_token()
    print(token_config["access_token"])


if __name__ == '__main__':
    main()
