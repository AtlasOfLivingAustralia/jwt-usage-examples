import json
import argparse
import requests
import time
from pathlib import Path

CONFIG_PATH = Path("config.json")

def main():
    # read config JSON file
    cfg = read_token_file(CONFIG_PATH)

    example(cfg)

# read the JSON file
def read_token_file(filepath):
    if not CONFIG_PATH.exists():
            raise FileNotFoundError(f"Auth config file not found: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg


def get_token(cfg):
    payload = {'refresh_token': cfg["refresh_token"], 'grant_type': 'client_credentials', 'scope': cfg["scopes"],
        'client_id':cfg["client_id"], 'client_secret':cfg["client_secret"]}

    r = requests.post(cfg["token_url"], data=payload)

    if r.ok:
        data = r.json()
        print("Token refreshed")
        return data["access_token"]

    else:
        print("Unable to refresh access token. ", r.status_code, r.content)



def example(cfg):
    # get the JWT
    token = get_token(cfg)
    print(token)


if __name__ == '__main__':
    main()
