# backend/app.py
from flask import Flask, redirect, request, session, jsonify , render_template
import requests, os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'super_secret'  # Replace in production

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = "playlist-read-private playlist-read-collaborative user-read-private"

@app.route("/")
def login():
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=playlist-read-private user-library-read"
    )
    return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_res = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token_data = token_res.json()
    session["access_token"] = token_data["access_token"]
    return redirect("/playlists")

@app.route("/playlists")
def playlists():
    token = session.get("access_token")
    if not token:
        return redirect("/")

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get("https://api.spotify.com/v1/me/playlists", headers=headers)
    data = res.json()

    playlists = []
    for item in data["items"]:
        playlists.append({
            "name": item["name"],
            "id": item["id"],
            "image": item["images"][0]["url"] if item["images"] else "",
            "tracks": item["tracks"]["total"]
        })
    # After fetching other playlists
    playlists.append({
    "name": "Liked Songs ❤️",
    "id": "liked-songs",
    "image": "https://misc.scdn.co/liked-songs/liked-songs-300.png",  # Spotify's own image
    "tracks": "dynamic"
    })

    return render_template("playlists.html", playlists=playlists)

@app.route("/analyze", methods=["POST"])
def analyze():
    token = session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    selected_ids = request.form.getlist("playlist_ids")
    all_tracks = []

    for pid in selected_ids:
        if pid == "liked-songs":
         liked_tracks_url = "https://api.spotify.com/v1/me/tracks?limit=50"
         res = requests.get(liked_tracks_url, headers=headers)
         data = res.json()

         for item in data.get("items", []):
          track = item.get("track")
          if track and track.get("id"):
            all_tracks.append(track["id"])

        else:
            # ✅ Handle normal playlist
            res = requests.get(f"https://api.spotify.com/v1/playlists/{pid}/tracks", headers=headers)
            data = res.json()
            for item in data["items"]:
                track = item["track"]
                if track:
                    all_tracks.append(track["id"])

    return jsonify({"total_tracks_collected": len(all_tracks), "track_ids": all_tracks})

if __name__ == "__main__":
    app.run(debug=True)
