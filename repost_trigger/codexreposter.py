import azure.functions as func
import logging
import requests
import os

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# SoundCloud API credentials
CLIENT_ID = 'OqynoaIXM2tKMHXUDf060UZRk7KnmxV4'
CLIENT_SECRET = 'nPv5MkEB0wet4flSOVRbb85tMjDF18cB'
REDIRECT_URI = 'https://codexreposter.azurewebsites.net'

# SoundCloud URLs
AUTH_URL = 'https://soundcloud.com/connect'
TOKEN_URL = 'https://api.soundcloud.com/oauth2/token'
SEARCH_URL = 'https://api.soundcloud.com/tracks'
REPOST_URL = 'https://api.soundcloud.com/reposts/tracks'

# Global access token
access_token = None

def authorize():
    global access_token
    if not CLIENT_ID or not CLIENT_SECRET:
        logging.error("CLIENT_ID or CLIENT_SECRET is not set.")
        return

    try:
        response = requests.post(TOKEN_URL, data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'client_credentials'
        })
        response.raise_for_status()
        access_token = response.json().get('access_token')
        logging.info("Authorization successful.")
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
