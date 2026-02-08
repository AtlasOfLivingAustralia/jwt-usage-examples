#!/usr/bin/env python3
import json
import argparse
import requests
import time
from pathlib import Path

CONFIG_PATH = Path("config.json")

def main():
    # read config JSON file
    cfg = read_token_file(CONFIG_PATH)

    # usage example of access token with a protected ala api
    api_example_request(cfg)

# read the JSON file
def read_token_file(filepath):
    if not CONFIG_PATH.exists():
            raise FileNotFoundError(f"Auth config file not found: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg

def get_token(cfg):

    access_token = regenerate_token(cfg)
    return access_token

# regenerate token, return new token
def regenerate_token(cfg):
    payload = {'refresh_token': cfg["refresh_token"], 'grant_type': 'refresh_token', 'scope': cfg["scopes"],
    'client_id':cfg["client_id"], 'client_secret':cfg["client_secret"]}

    r = requests.post(cfg["token_url"], data=payload)

    if r.ok:
        data = r.json()
        print("Token refreshed")
        return data["access_token"]

    else:
        print("Unable to refresh access token. ", r.status_code, r.content)


def api_example_request(cfg):
    url = "https://api.ala.org.au/occurrences/config"
    # get the JWT
    access_token = get_token(cfg)
    headers = {'user-agent': 'token-refresh/0.1.1', 'Authorization': 'Bearer {0}'.format(access_token)}
    r = requests.get(url, headers=headers)
    if r.ok:
        print(r.status_code, r.text)
    else:
        print("Error encountered during request ", r.status_code)


if __name__ == '__main__':
    main()
