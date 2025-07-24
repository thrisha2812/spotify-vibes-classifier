# backend/app.py
from flask import Flask, redirect, request, session, jsonify, render_template
import requests, os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'super_secret'  # Replace in production

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = "user-read-private playlist-read-private playlist-read-collaborative user-library-read"


def get_track_ids(playlist_id, headers):
    res = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=headers)

    if res.status_code != 200:
        print(f"❌ Failed to fetch tracks for playlist {playlist_id}: {res.status_code} {res.text}")
        return []

    data = res.json()
    track_ids = []

    for item in data.get("items", []):
        track = item.get("track")
        if not track:
            print("⚠️ Skipping null track entry.")
            continue

        track_id = track.get("id")
        if not track_id:
            print("⚠️ Skipping item without track ID:", track.get("name", "Unknown"))
            continue

        track_ids.append(track_id)

    print(f"✅ Found {len(track_ids)} valid track IDs in playlist {playlist_id}")
    return track_ids

def get_liked_song_ids(headers):
    url = "https://api.spotify.com/v1/me/tracks?limit=50"
    res = requests.get(url, headers=headers)
    data = res.json()
    track_ids = []
    for item in data.get("items", []):
        track = item.get("track")
        if track and track.get("id"):
            track_ids.append(track["id"])
    return track_ids


@app.route("/login")
def login():
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=playlist-read-private playlist-read-collaborative user-library-read user-read-private"
    )
    return redirect(auth_url)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


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
    print("DEBUG: Token Response", token_data)

    if "access_token" not in token_data:
        return jsonify({"error": "Failed to fetch token"}), 400

    # Save token in Flask session
    session["access_token"] = token_data["access_token"]
    return redirect("/playlists")

@app.route("/playlists")
def playlists():
    token = session.get("access_token")
    if not token:
        return redirect("/login")

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get("https://api.spotify.com/v1/me/playlists", headers=headers)
    if res.status_code != 200:
        return jsonify({"error": "Failed to fetch playlists"}), 400

    data = res.json()
    playlists = []

    for p in data["items"]:
        track_ids = get_track_ids(p["id"], headers)  # ✅ Use the safe version
        playlists.append({
            "id": p["id"],
            "name": p["name"],
            "image": p["images"][0]["url"] if p["images"] else "",
            "tracks": p["tracks"]["total"],
            "track_ids": track_ids  # ✅ pass cleaned track IDs
        })

    return render_template("playlists.html", playlists=playlists)



@app.route("/analyze", methods=["POST"])
def analyze():
    token = session.get("access_token")
    if not token:
        return redirect("/")
    print("DEBUG: Access Token being used:", token)

    try:
        data = request.get_json()
        track_ids = data.get("track_ids", [])
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400

    print("Track IDs received:", track_ids)
    if not track_ids:
        return jsonify({"error": "No track IDs received"}), 400

    headers = {"Authorization": f"Bearer {token}"}
    features = []

    for i in range(0, len(track_ids), 100):
        chunk = track_ids[i:i + 100]
        res = requests.get(
            "https://api.spotify.com/v1/audio-features",
            headers=headers,
            params={"ids": ",".join(chunk)}
        )

        if res.status_code != 200:
            print("❌ Spotify API error:", res.status_code, res.text)
            return jsonify({"error": "Spotify API error fetching audio features"}), 400

        data = res.json()
        chunk_features = [f for f in data.get("audio_features", []) if f]
        features.extend(chunk_features)

    if not features:
        print("⚠️ No audio features found for tracks:", track_ids)
        return jsonify({"error": "No audio features found for selected tracks."}), 400

    # Compute averages
    avg_valence = sum(f["valence"] for f in features) / len(features)
    avg_energy = sum(f["energy"] for f in features) / len(features)
    avg_dance = sum(f["danceability"] for f in features) / len(features)
    avg_acoustic = sum(f["acousticness"] for f in features) / len(features)
    avg_tempo = sum(f["tempo"] for f in features) / len(features)

    vibe = classify_vibe(avg_valence, avg_energy, avg_dance, avg_acoustic, avg_tempo)

    return jsonify({
        "vibe": vibe,
        "average_features": {
            "valence": avg_valence,
            "energy": avg_energy,
            "danceability": avg_dance,
            "acousticness": avg_acoustic,
            "tempo": avg_tempo
        }
    })

def classify_vibe(avg_valence, avg_energy, avg_danceability, avg_acousticness, avg_tempo):
    if avg_valence > 0.7 and avg_energy > 0.6:
        return "Happy Vibes 😄"
    elif avg_energy < 0.4 and avg_acousticness > 0.5:
        return "Chill Zone 😌"
    elif avg_danceability > 0.7 and avg_energy > 0.7:
        return "Party Mode 🎉"
    elif avg_valence < 0.4 and avg_acousticness > 0.6:
        return "Sad & Soft 😢"
    elif avg_tempo > 140:
        return "Fast Paced 🏃‍♀️"
    else:
        return "Mixed Vibes 🎧"


if __name__ == "__main__":
    app.run(debug=True)
