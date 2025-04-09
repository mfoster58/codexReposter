import azure.functions as func
import logging
import requests
import time
import base64

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# SoundCloud API credentials
CLIENT_ID = 'OqynoaIXM2tKMHXUDf060UZRk7KnmxV4'
CLIENT_SECRET = 'nPv5MkEB0wet4flSOVRbb85tMjDF18cB'
REDIRECT_URI = 'https://codexreposter.azurewebsites.net'

# SoundCloud URLs
# AUTH_URL = 'https://soundcloud.com/connect'
TOKEN_URL = 'https://secure.soundcloud.com/oauth/token'
SEARCH_URL = 'https://api.soundcloud.com/tracks'
REPOST_URL = 'https://api.soundcloud.com/reposts/tracks'

# Global access token
access_token = None
token_expiry = None

def authorize():
    """
    Obtain an access token using the Client Credentials Flow with Basic Authentication.
    Refresh the token if it has expired.
    """
    global access_token, token_expiry
    if not CLIENT_ID or not CLIENT_SECRET:
        logging.error("CLIENT_ID or CLIENT_SECRET is not set.")
        return

    # Check if the token is still valid, if yes return
    if access_token and token_expiry and time.time() < token_expiry:
        logging.info("Using cached access token.")
        return

    try:
        # Encode client_id and client_secret in Base64 for Basic Authentication
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
         # Make the POST request to obtain the access token
        response = requests.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
                "accept": "application/json; charset=utf-8"
            },
            data={
                "grant_type": "client_credentials"
            }
        )
        response.raise_for_status()

         # Parse the response
        data = response.json()
        access_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)
        token_expiry = time.time() + expires_in
        logging.info("Authorization successful. Token expires in %s seconds.", expires_in)
    except requests.exceptions.RequestException as e:
        logging.error(f"Authorization failed: {e}")

def repost_tracks():
    global access_token
    if access_token is None:
        authorize()
        if access_token is None:
            logging.error("Failed to obtain access token.")
            return

    headers = {
        'Authorization': f'OAuth {access_token}'
    }

    try:
        search_response = requests.get(SEARCH_URL, headers=headers, params={
            'tags': 'codex-collective',
            'limit': 5
        })
        search_response.raise_for_status()
        tracks = search_response.json()
        logging.info("Search response received successfully.")
        logging.info(f"Raw search response: {search_response.text}")
        logging.info(f"Search response JSON: {tracks}")
        logging.info(f"Found {len(tracks)} tracks to repost.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Search request failed: {e}")
        return

    for track in tracks:
        track_id = track['id']
        try:
            repost_response = requests.post(f"{REPOST_URL}/{track_id}", headers=headers)
            repost_response.raise_for_status()
            logging.info(f"Reposted track {track_id} successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to repost track {track_id}: {e}")

def register_functions(app):
    @app.route(route="codexReposter")
    def codexReposter(req: func.HttpRequest) -> func.HttpResponse:
        logging.info('Python HTTP trigger function processed a request.')

        # Perform SC auth and reposting
        repost_tracks()
        return func.HttpResponse("Reposting tracks...", status_code=200)
    
@app.function_name(name="TimerTrigger")
@app.schedule(schedule="0 0 * * * *", arg_name="mytimer", run_on_startup=True, use_monitor=True)
def timer_trigger(mytimer: func.TimerRequest) -> None:
    logging.info('Timer trigger function executed at %s', mytimer.past_due)
    repost_tracks()
