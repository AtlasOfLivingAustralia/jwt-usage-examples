#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This Python example shows how to generate a JWT and use it when invoking an API.
# Fill Client Id and Gateway API key.
# Change authorize and access endpoints according to the environment.



import requests
from flask import Flask, request, redirect, session, url_for
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a strong, secret key

# OAuth2 configuration
authorize_url = "https://auth-secure.auth.ap-southeast-2.amazoncognito.com/oauth2/authorize"
token_url = "https://auth-secure.auth.ap-southeast-2.amazoncognito.com/oauth2/token"
client_id = "<<Client Id>>"
redirect_uri = "http://localhost:5000/callback"  # Update this to your redirect URI

@app.route('/')
def home():
    # Step 1: Redirect the user to the authorization server for approval
    auth_url = f"{authorize_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=openid profile email ala/attrs ala/roles"
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
        print("test1")
        
        response = requests.post(token_url, data=data, headers={'Accept': 'application/json'})
        print("test2",response.status_code) 
        
        if response.status_code == 200:
            access_token = response.json()['access_token']
            print("test 2 access token",access_token)
            
            # Step 4: Use the access token to make API requests
            api_url = "https://api.test.ala.org.au/common/lists/speciesList"
            headers = {
                'x-api-key': '<<Gateway API key>>',  # Replace with your actual Gateway API key
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }
            
            api_response = requests.get(api_url, headers=headers)
            print("test3",api_response.status_code)
            if api_response.status_code == 200:
                api_data = api_response.json()
                return json.dumps(api_data, indent=2)
            else:
                return f"Error: {api_response.status_code} - {api_response.text}"

    return "Authorization failed."

if __name__ == '__main__':
    app.run()
