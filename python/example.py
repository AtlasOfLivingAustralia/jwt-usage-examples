#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 11:35:44 2023

@author: das037
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This Python example shows how to generate a JWT and use it when invoking an API.
# Fill Client Id and Gateway API key.
# Change authorize and access endpoints according to the environment.


import requests
from flask import Flask, request, redirect
import json
import webbrowser
import logging
import threading

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a strong, secret key

# OAuth2 configuration
authorize_url = "https://auth-secure.auth.ap-southeast-2.amazoncognito.com/oauth2/authorize"
token_url = "https://auth-secure.auth.ap-southeast-2.amazoncognito.com/oauth2/token"
client_id = "51gads0veaglh0ksbikt3bom1m"
redirect_uri = "http://localhost:5000/callback"  # Update this to your redirect URI
home_uri="http://localhost:5000"


# Specify the browser name (e.g., "firefox", "chrome", "safari")
browser_name = "chrome"

# Flag to track if the authentication tab has been opened
authentication_tab_opened = False

logging.basicConfig(
    level=logging.DEBUG,  # Set the desired log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s [%(levelname)s]: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='my_script.log',  # Specify the log file name
    filemode='w'  # 'w' for write, 'a' for append
)


# Create a logger instance
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Set the desired log level

# Create a formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Create a stream handler (to display log messages on the console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(stream_handler)


def open_authentication_tab():
    global authentication_tab_opened
    auth_url = f"{authorize_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=openid profile email ala/attrs ala/roles"
    browser = webbrowser.get(browser_name)
    logger.info('Before opening authentication tab')
    browser.open_new(home_uri)
    logger.info('After opening authentication tab')
    authentication_tab_opened = True


@app.route('/')
def home():
    global authentication_tab_opened
    # Step 1: Redirect the user to the authorization server for approval
    auth_url = f"{authorize_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=openid profile email ala/attrs ala/roles"
    # Get the browser instance and open the URI
    if not authentication_tab_opened:
        # Open the authentication tab
        threading.Thread(target=open_authentication_tab).start()
    # Now you can use the logger to record log messages
    logger.info('************ALA Authentication**********')
    logger.info('**Please open a browser and Authticate**')
    logger.info(f'******Home URL:: {home_uri}**************')
    logger.info(f'******Auth URL:: {auth_url}**************')
    return redirect(auth_url)



@app.route('/callback')
def callback():
    # Step 2: Handle the callback from the authorization server
    code = request.args.get('code')
    if code:
        # Step 3: Exchange the authorization code for an access token
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': client_id,
            'redirect_uri': redirect_uri,
        }
        logger.info('**********Thank ou for Authntication**************')
        response = requests.post(token_url, data=data, headers={'Accept': 'application/json'})
        logger.info(f'***************Response.status_code value :: {response.status_code}')
        
        if response.status_code == 200:
            access_token = response.json()['access_token']
            logger.info(f'************Access token Value :: {access_token}***********')
            # Step 4: Use the access token to make API requests
            api_url = "https://api.test.ala.org.au/occurrences/occurrences/offline/status"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }
            logger.info(f'************Request API URL :: {api_url}***********')
            api_response = requests.get(api_url, headers=headers)
            # print("test3",api_response.status_code)
            logger.info(f'************API Response code  :: {api_response.status_code}')
            if api_response.status_code == 200:
                api_data = api_response.json()
                return json.dumps(api_data, indent=1, sort_keys=True)
            else:
                return f"Error: {api_response.status_code} - {api_response.text}"

    return "Authorization failed."

if __name__ == '__main__':
    app.run()
