import azure.functions as func
import logging
import requests
import os

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# SoundCloud API credentials
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'https://codexreposter.azurewebsites.net'

# SoundCloud URLs
AUTH_URL = 'https://soundcloud.com/connect'
TOKEN_URL = 'https://api.soundcloud.com/oauth2/token'
SEARCH_URL = 'https://api.soundcloud.com/tracks'
REPOST_URL = 'https://api.soundcloud.com/me/track_reposts'

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

    try:
        search_response = requests.get(SEARCH_URL, params={
            'client_id': CLIENT_ID,
            'q': '#codex-collective',
            'limit': 5
        })
        search_response.raise_for_status()
        tracks = search_response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Search request failed: {e}")
        return

    for track in tracks:
        track_id = track['id']
        try:
            repost_response = requests.post(f"{REPOST_URL}/{track_id}", params={
                'oauth_token': access_token
            })
            repost_response.raise_for_status()
            logging.info(f"Reposted track {track_id} successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to repost track {track_id}: {e}")

@app.route(route="codexReposter")
def codexReposter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )