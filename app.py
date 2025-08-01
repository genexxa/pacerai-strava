from flask import Flask, request, redirect
import requests
import os

app = Flask(__name__)

# ✅ Hardcoded for production — replace with your actual domain
REDIRECT_URI = "https://pacerai-strava.onrender.com/callback"
CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")

@app.route("/")
def home():
    return "👋 Welcome to Pacer's Strava Connector! Visit /auth to connect your Strava account."

@app.route("/auth")
def auth():
    print("➡️ Using redirect_uri in /auth:", REDIRECT_URI)
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

    print("🔄 Exchanging token using redirect_uri:", REDIRECT_URI)
    
    # Exchange code for access token
    token_response = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI  # 🔐 must match EXACTLY
    })

    if token_response.status_code != 200:
        print("❌ Token exchange failed:", token_response.text)
        return f"❌ Failed to exchange code: {token_response.text}", 400

    tokens = token_response.json()
    access_token = tokens.get("access_token")
    athlete = tokens.get("athlete", {})

    print("✅ Successfully connected athlete:", athlete.get("username", "unknown"))

    return (
        f"✅ Connected as {athlete.get('firstname', 'Unknown')}!<br>"
        f"Access Token (first 10 chars): {access_token[:10]}...<br><br>"
        f"You can now close this window and return to the Pacer GPT."
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Flask app on port {port} with host 0.0.0.0")
    app.run(host="0.0.0.0", port=port)
