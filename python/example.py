# Install Python packages using pip
# python3 -m pip install requests
# python3 -m pip install flask

import requests
import time
from flask import Flask, request, redirect, render_template_string, session
import json
import webbrowser
import logging
import threading
import sys

app = Flask(__name__)


# OAuth2 configuration
authorize_url = "https://auth-secure.auth.ap-southeast-2.amazoncognito.com/oauth2/authorize"
token_url = "https://auth-secure.auth.ap-southeast-2.amazoncognito.com/oauth2/token"
logout_url = "https://auth-secure.auth.ap-southeast-2.amazoncognito.com/logout"

client_id = "" # Replace this with your_public_clientid
app.secret_key = 'your_secret_key'  # Replace with yoursecret key - Not required for Public Client (Client-side Application)
redirect_uri = "http://localhost:8080/callback"  # Replace with your redirect URI
home_uri = "http://localhost:8080"
logout_endpoint = "http://localhost:8080/callback"  # Replace with your redirect URI

# Flag to track if the authentication tab has been opened
authentication_tab_opened = False

# Configure logging
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

# Function to refresh the access token using the refresh token
def refresh_access_token(refresh_token):
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
    }
    response = requests.post(token_url, data=data, headers={'Accept': 'application/json'})
    if response.status_code == 200:
        auth_response = response.json()
        new_access_token = auth_response['access_token']
        new_refresh_token = auth_response.get('refresh_token', 'N/A')
        new_expires_in = auth_response.get('expires_in', 'N/A')
        return new_access_token, new_refresh_token, new_expires_in
    else:
        return None, None, None

# Function to check if the access token is expired
def is_access_token_expired():
    expires_at = session.get('access_token_expires_at')
    return expires_at is None or time.time() > expires_at

def open_authentication_tab():
    global authentication_tab_opened
    auth_url = f"{authorize_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=openid profile email ala/attrs ala/roles"
    logger.info('Opening browser for authentication')
    webbrowser.open_new(home_uri)
    logger.info('Enter your ALA credentials in the browser')
    authentication_tab_opened = True

@app.route('/')
def home():
    global authentication_tab_opened
    if is_access_token_expired():
        # If the access token is expired, refresh it using the refresh token
        new_access_token, new_refresh_token, new_expires_in = refresh_access_token(session.get('refresh_token'))
        if new_access_token:
            session['access_token'] = new_access_token
            session['refresh_token'] = new_refresh_token
            session['access_token_expires_at'] = time.time() + new_expires_in

    # Step 1: Redirect the user to the authorization server for approval
    auth_url = f"{authorize_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=openid profile email ala/attrs ala/roles"
    # Get the browser instance and open the URI
    if not authentication_tab_opened:
        # Open the authentication tab
        threading.Thread(target=open_authentication_tab).start()
    # Logging messages for user guidance
    logger.info(f'******Home URL: {home_uri}**************')
    logger.info(f'******Auth URL: {auth_url}**************')
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
        logger.info('**********Authentication in progress**************')
        response = requests.post(token_url, data=data, headers={'Accept': 'application/json'})
        logger.info(f'***************Response.status_code: {response.status_code}')

        if response.status_code == 200:
            auth_response = response.json()
            access_token = auth_response['access_token']
            refresh_token = auth_response.get('refresh_token', 'N/A')
            expires_in = auth_response.get('expires_in', 'N/A')

            # Step 4: Use the access token to make API requests
            api_url = "https://api.test.ala.org.au/occurrences/occurrences/offline/status"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }
            logger.info(f'************Request Restricted API Webservice: {api_url}***********')
            api_response = requests.get(api_url, headers=headers)
            logger.info(f'************API Response code: {api_response.status_code}')

            if api_response.status_code == 200:
                api_data = auth_response
                # Include a success message in the response
                success_message = "✅ Authentication successful."
                info = "Your python app can now access the protected resource using the access token."

                # Define the HTML template as a string
                template_string = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to ALA example Python app</title>
    <!-- Include Bootstrap CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        /* Add your custom CSS styles here for additional customization */
        body {
            background-color: #f5f5f5;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
            position: relative;
        }

        h1,
        h3 {
            color: #9c3d29;
        }

        pre {
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            background-color: #f8f8f8;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: auto;
            word-wrap: break-word;
        }

        .logout-button {
            position: absolute;
            top: 20px;
            right: 20px;
        }
    </style>
</head>

<body>
    <div class="container">
        <form action="/logout" method="post" class="logout-button">
            <button type="submit" class="btn btn-danger">Logout</button>
        </form>
        <h1>{{ message }}</h1>
        <h3>{{ info }}</h3>
        <hr>
        <h5>ⓘ Use the following cURL command to access the secure ALA API and check the status of the Download Queue.:</h5>
        <pre>
curl -X GET "https://api.test.ala.org.au/occurrences/occurrences/offline/status/all" \
-H "Accept: application/json" \
-H "Authorization: Bearer {{ access_token }}"
        </pre>

        <h5>ⓘ  cURL command to refresh an access token using a refresh token</h5>
        <pre>
curl -X POST \
-H "Content-Type: application/x-www-form-urlencoded" \
--data-urlencode "grant_type=refresh_token" \
--data-urlencode "client_id={{client_id}}" \
--data-urlencode "refresh_token={{refresh_token}}" \
--data-urlencode "scope=openid profile email ala/attrs ala/roles" \
--data-urlencode "client_secret=" \
"{{token_url}}"
        </pre>

       
        <h4>ⓘ JSON Response:</h4>
        <pre>{{ json_data }}</pre>
    </div>

    <!-- Include Bootstrap JS and jQuery -->
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</body>

</html>

                """

                # Render the HTML template using render_template_string
                rendered_template = render_template_string(
                    template_string,
                    message=success_message,
                    info=info,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=expires_in,
                    client_id=client_id,
                    token_url=token_url,
                    json_data=json.dumps(api_data, indent=4)
                )

                # Return the rendered HTML as the response
                return rendered_template

    return "Authorization failed."

@app.route('/logout', methods=['POST'])
def logout():
    # Implement the logout functionality here, e.g., by revoking the access token
    logout = f"{logout_url}?client_id={client_id}&redirect_uri={logout_endpoint}&response_type=code"
    logger.info('Opening browser for authentication')
    webbrowser.open_new(logout)
    return "Logged out successfully."

def countdown(seconds):
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\rOpening browser in {i} seconds...")
        sys.stdout.flush()
        time.sleep(1)
    print("\rOpening browser now!")

if __name__ == '__main__':
    logger.info(f'*********************************')
    logger.info("ⓘ Welcome to ALA example Python app")
    logger.info("ⓘ Demonstrates how to use OAuth2 for authentication and API authorization")
    logger.info("ⓘ Supports Native ALA login with / without MFA, as well as AAF, Google, Apple, and IdP MFA authentication")
    logger.info(f'*********************************')
    countdown(3)  # Display the countdown for 5 seconds
    threading.Thread(target=open_authentication_tab).start()  # Start the browser thread
    app.run(port=8080)
  
