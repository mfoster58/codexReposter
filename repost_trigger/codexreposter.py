import azure.functions as func
import logging
import requests
import os

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# SoundCloud API credentials
CLIENT_ID = 'CLIENT_ID'
CLIENT_SECRET = 'CLIENT_SECRET'
REDIRECT_URI = 'REDIRECT_URI'

# SoundCloud URLs
AUTH_URL = 'https://soundcloud.com/connect'
TOKEN_URL = 'https://api.soundcloud.com/oauth2/token'
SEARCH_URL = 'https://api.soundcloud.com/tracks'
REPOST_URL = 'https://api.soundcloud.com/me/track_reposts'

# Global access token
access_token = None

def authorize():
    global access_token
    response = requests.post(TOKEN_URL, data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }).json()
    access_token = response['access_token']

def repost_tracks():
    global access_token
    if access_token is None:
        authorize()

    search_response = requests.get(SEARCH_URL, params={
        'client_id': CLIENT_ID,
        'q': '#codex-collective',
        'limit': 5
    }).json()

    for track in search_response:
        track_id = track['id']
        repost_response = requests.post(f"{REPOST_URL}/{track_id}", params={
            'oauth_token': access_token
        })

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