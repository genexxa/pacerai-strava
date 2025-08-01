from flask import Flask, request, redirect
import requests
import os

app = Flask(__name__)

# Load environment variables (Render will inject them directly)
CLIENT_ID = os.getenv("STRAVA_CLIENT")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REDIRECT_URI = os.getenv("STRAVA_REDIRECT_URI")  # e.g., https://pacer-strava.onrender.com/callback

@app.route("/")
def home():
    return "👋 Welcome to Pacer's Strava Connector! Visit /auth to connect your Strava account."

@app.route("/auth")
def auth():
    strava_auth_url = (
        f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=activity:read_all"
        f"&approval_prompt=force"
    )
    return redirect(strava_auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    error = request.args.get("error")
    
    if error:
        return f"❌ Authorization failed: {error}", 400
    if not code:
        return "❌ No code provided by Strava.", 400

    # Exchange code for access token
    token_response = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    })

    if token_response.status_code != 200:
        return f"❌ Failed to exchange code: {token_response.text}", 400

    tokens = token_response.json()
    access_token = tokens.get("access_token")
    athlete = tokens.get("athlete", {})

    return (
        f"✅ Connected as {athlete.get('firstname', 'Unknown')}!<br>"
        f"Access Token (first 10 chars): {access_token[:10]}...<br><br>"
        f"You can now close this window and return to the Pacer GPT."
    )
