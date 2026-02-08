#!/usr/bin/env python3
import base64
import hashlib
import json
import os
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests
CONFIG_PATH = Path("config.json")

def _b64url_no_pad(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def make_pkce() -> tuple[str, str]:
    # code_verifier: 43-128 chars; use 32 bytes -> 43 chars b64url
    verifier = _b64url_no_pad(os.urandom(32))
    challenge = _b64url_no_pad(hashlib.sha256(verifier.encode("utf-8")).digest())
    return verifier, challenge


class CallbackHandler(BaseHTTPRequestHandler):
    # shared state
    auth_code = None
    auth_error = None
    query_params = None

    def log_message(self, format, *args):
        # silence default logging
        return

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        qs = urllib.parse.parse_qs(parsed.query)
        CallbackHandler.query_params = qs

        if "error" in qs:
            CallbackHandler.auth_error = qs.get("error", ["unknown_error"])[0]
        if "code" in qs:
            CallbackHandler.auth_code = qs.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if CallbackHandler.auth_code:
            self.wfile.write(
                b"<html><body><h3>Login complete.</h3><p>You can close this tab now.</p></body></html>"
            )
        else:
            self.wfile.write(
                b"<html><body><h3>Login failed.</h3><p>You can close this tab now.</p></body></html>"
            )


def get_auth_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Auth config file not found: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg

def exchange_code_for_token(token_url: str, client_id: str, code: str, code_verifier: str, redirect_uri: str) -> dict:
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code": code,
        "code_verifier": code_verifier,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(token_url, data=data, headers=headers, timeout=30)
    # If it fails, print helpful detail:
    if r.status_code >= 400:
        raise RuntimeError(f"Token request failed ({r.status_code}): {r.text}")
    return r.json()


def run_local_server(httpd: HTTPServer):
    # Serve until we get a code or error; handle_request() blocks for 1 request at a time.
    while CallbackHandler.auth_code is None and CallbackHandler.auth_error is None:
        httpd.handle_request()


def main():
    cfg = get_auth_config()
    client_id = cfg["client_id"]
    authorize_url = cfg["authorize_url"]
    token_url = cfg["token_url"]
    scopes = cfg["scopes"]
    redirect_uri = cfg["redirect_uri"]

    # PKCE + state
    code_verifier, code_challenge = make_pkce()
    state = _b64url_no_pad(os.urandom(16))

    # Start callback server
    httpd = HTTPServer(("localhost", 8080), CallbackHandler)
    server_thread = threading.Thread(target=run_local_server, args=(httpd,), daemon=True)
    server_thread.start()

    params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scopes,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
    }

    auth_url = authorize_url + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

    print("1) Opening browser for login...\n")
    print("If your browser doesn't open, copy/paste this URL:\n")
    print(auth_url)
    print(f"\n2) Waiting for redirect back to: {redirect_uri}\n")

    webbrowser.open(auth_url)

    # Wait for callback
    start = time.time()
    while CallbackHandler.auth_code is None and CallbackHandler.auth_error is None:
        if time.time() - start > 180:
            raise TimeoutError(f"Timed out after 180s waiting for login redirect.")
        time.sleep(0.2)

    if CallbackHandler.auth_error:
        raise SystemExit(f"Authorization error: {CallbackHandler.auth_error} (details: {CallbackHandler.query_params})")

    # Validate state if present
    returned_state = None
    if CallbackHandler.query_params and "state" in CallbackHandler.query_params:
        returned_state = CallbackHandler.query_params["state"][0]
    if returned_state is not None and returned_state != state:
        raise SystemExit("State mismatch — possible CSRF or wrong callback. Aborting.")

    code = CallbackHandler.auth_code
    token = exchange_code_for_token(token_url, client_id, code, code_verifier, redirect_uri)

    print("\n✅ Token response:\n")
    print(json.dumps(token, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")