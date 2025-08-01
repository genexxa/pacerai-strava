from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from datetime import datetime

app = Flask(__name__)

# PostgreSQL config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Strava app config
CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REDIRECT_URI = "https://pacerai-strava.onrender.com/callback"

# Database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    strava_id = db.Column(db.Integer, unique=True, nullable=False)
    firstname = db.Column(db.String(64))
    lastname = db.Column(db.String(64))
    access_token = db.Column(db.String(255))
    refresh_token = db.Column(db.String(255))
    token_expires_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<User {self.strava_id} - {self.firstname}>'

# Home route
@app.route("/")
def home():
    return "👋 Welcome to Pacer Strava! Visit /auth to connect your account."

# Start OAuth flow
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

# Handle OAuth callback
@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "❌ No code returned from Strava", 400

    response = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    })

    if response.status_code != 200:
        return f"❌ Failed to exchange code: {response.text}", 400

    data = response.json()
    athlete = data['athlete']
    expires_at = datetime.utcfromtimestamp(data['expires_at'])

    # Store or update user
    user = User.query.filter_by(strava_id=athlete['id']).first()
    if not user:
        user = User(strava_id=athlete['id'])

    user.firstname = athlete.get('firstname', '')
    user.lastname = athlete.get('lastname', '')
    user.access_token = data['access_token']
    user.refresh_token = data['refresh_token']
    user.token_expires_at = expires_at

    db.session.add(user)
    db.session.commit()

    return (
        f"✅ Connected as {user.firstname}!<br>"
        f"Access token saved. Expires at {expires_at} UTC.<br>"
        f"You can now close this window and return to the Pacer GPT."
    )

# Create DB tables and run app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
