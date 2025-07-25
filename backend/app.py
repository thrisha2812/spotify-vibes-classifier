# backend/app.py
from flask import Flask, redirect, request, session, jsonify, render_template, url_for
import requests, os
from dotenv import load_dotenv
from collections import Counter
import time

load_dotenv()

app = Flask(__name__)
app.secret_key = 'super_secret'  # Replace in production

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = "user-read-private playlist-read-private playlist-read-collaborative user-library-read"


def validate_token(token):
    """Validate if the access token is still valid"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    return response.status_code == 200


def get_track_ids(playlist_id, headers):
    """Get track IDs from a playlist with pagination support"""
    track_ids = []
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    
    while url:
        res = requests.get(url, headers=headers)
        
        if res.status_code != 200:
            print(f"❌ Failed to fetch tracks for playlist {playlist_id}: {res.status_code} {res.text}")
            break

        data = res.json()
        
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
        
        # Handle pagination
        url = data.get("next")

    print(f"✅ Found {len(track_ids)} valid track IDs in playlist {playlist_id}")
    return track_ids


def get_liked_song_ids(headers):
    """Get user's liked songs with pagination support"""
    track_ids = []
    url = "https://api.spotify.com/v1/me/tracks?limit=50"
    
    while url:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            break
            
        data = res.json()
        for item in data.get("items", []):
            track = item.get("track")
            if track and track.get("id"):
                track_ids.append(track["id"])
        
        url = data.get("next")
    
    return track_ids


def get_track_and_artist_info(track_id, headers):
    """Get track and artist information from Spotify"""
    track_res = requests.get(f"https://api.spotify.com/v1/tracks/{track_id}", headers=headers)
    if track_res.status_code != 200:
        return None
    
    track = track_res.json()
    artist_id = track['artists'][0]['id']
    
    # Get artist info for genres
    artist_res = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
    if artist_res.status_code != 200:
        return {
            'track': track,
            'artist_genres': []
        }
    
    artist = artist_res.json()
    
    return {
        'track': track,
        'artist_genres': artist.get('genres', [])
    }


def analyze_tracks_simple(track_ids, headers):
    """Simple analysis using track and artist data"""
    tracks_data = []
    
    # Limit to 30 tracks to avoid rate limits and long processing times
    limited_track_ids = track_ids[:30]
    print(f"Analyzing {len(limited_track_ids)} tracks...")
    
    for i, track_id in enumerate(limited_track_ids):
        track_info = get_track_and_artist_info(track_id, headers)
        if track_info:
            tracks_data.append(track_info)
        
        # Progress indicator
        if (i + 1) % 5 == 0:
            print(f"Processed {i + 1}/{len(limited_track_ids)} tracks")
        
        # Small delay to respect rate limits
        time.sleep(0.1)
    
    if not tracks_data:
        return {"error": "No track data available"}
    
    return analyze_simple_features(tracks_data)


def analyze_simple_features(tracks_data):
    """Analyze using simple metrics"""
    total_popularity = 0
    total_duration = 0
    all_genres = []
    total_explicit = 0
    release_years = []
    
    for track_data in tracks_data:
        track = track_data['track']
        genres = track_data['artist_genres']
        
        total_popularity += track.get('popularity', 0)
        total_duration += track.get('duration_ms', 0)
        all_genres.extend(genres)
        total_explicit += 1 if track.get('explicit', False) else 0
        
        # Extract release year
        release_date = track.get('album', {}).get('release_date', '')
        if release_date and len(release_date) >= 4:
            try:
                release_years.append(int(release_date[:4]))
            except ValueError:
                pass
    
    num_tracks = len(tracks_data)
    
    # Calculate metrics
    avg_popularity = total_popularity / num_tracks
    avg_duration_min = (total_duration / num_tracks) / 60000
    explicit_ratio = total_explicit / num_tracks
    avg_year = sum(release_years) / len(release_years) if release_years else 2020
    
    # Genre analysis
    genre_counts = Counter(all_genres)
    top_genres = genre_counts.most_common(5)
    
    # Classify vibe
    vibe = classify_vibe_simple(top_genres, avg_popularity, avg_duration_min, explicit_ratio, avg_year)
    
    return {
        "vibe": vibe,
        "analysis": {
            "avg_popularity": round(avg_popularity, 1),
            "avg_duration_minutes": round(avg_duration_min, 1),
            "explicit_ratio": round(explicit_ratio * 100, 1),
            "avg_release_year": round(avg_year),
            "top_genres": top_genres,
            "tracks_analyzed": num_tracks
        },
        # Legacy format for frontend compatibility
        "average_features": {
            "popularity": round(avg_popularity, 1),
            "duration": round(avg_duration_min, 1),
            "explicit_ratio": round(explicit_ratio * 100, 1),
            "release_year": round(avg_year),
            "genre_count": len(top_genres)
        }
    }


def classify_vibe_simple(top_genres, avg_popularity, avg_duration, explicit_ratio, avg_year):
    """Simple vibe classification"""
    genre_names = [genre[0].lower() for genre in top_genres]
    
    # High energy/party genres
    party_genres = ['dance', 'electronic', 'edm', 'house', 'techno', 'disco', 'funk', 'hip hop', 'rap']
    # Chill genres
    chill_genres = ['ambient', 'chill', 'lo-fi', 'acoustic', 'folk', 'indie folk', 'new age', 'jazz']
    # Sad/emotional genres
    sad_genres = ['blues', 'country', 'emo', 'post-rock', 'melancholy', 'indie rock']
    # Happy/upbeat genres
    happy_genres = ['pop', 'indie pop', 'reggae', 'ska', 'afrobeat', 'soul', 'r&b']
    # High energy but not party
    energetic_genres = ['rock', 'punk', 'metal', 'hardcore', 'grunge', 'alternative']
    
    # Score different vibes
    party_score = sum(1 for genre in genre_names if any(p in genre for p in party_genres))
    chill_score = sum(1 for genre in genre_names if any(c in genre for c in chill_genres))
    sad_score = sum(1 for genre in genre_names if any(s in genre for s in sad_genres))
    happy_score = sum(1 for genre in genre_names if any(h in genre for h in happy_genres))
    energetic_score = sum(1 for genre in genre_names if any(e in genre for e in energetic_genres))
    
    # Factor in other metrics
    is_recent = avg_year > 2015
    is_popular = avg_popularity > 60
    is_long = avg_duration > 4.5
    is_very_popular = avg_popularity > 80
    
    # Classification logic with priority order
    if party_score >= 1 and is_popular:
        return "Party Mode 🎉"
    elif chill_score >= 1 or (is_long and avg_popularity < 50):
        return "Chill Zone 😌"
    elif sad_score >= 1 or (avg_popularity < 30 and not is_recent):
        return "Sad & Soft 😢"
    elif happy_score >= 1 or is_very_popular:
        return "Happy Vibes 😄"
    elif energetic_score >= 1 or (avg_duration < 3.5 and is_recent):
        return "Fast Paced 🏃‍♀️"
    elif party_score >= 1:  # Lower threshold for party if not popular
        return "Party Mode 🎉"
    else:
        return "Mixed Vibes 🎧"


@app.route("/")
def home():
    """Home route - redirect based on login status"""
    token = session.get("access_token")
    if token and validate_token(token):
        return redirect("/playlists")
    else:
        return redirect("/login")


@app.route("/login")
def login():
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&show_dialog=true"
        f"&scope=playlist-read-private playlist-read-collaborative user-library-read user-read-private"
    )
    return redirect(auth_url)


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/login')


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No authorization code received"}), 400
        
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
    print("DEBUG: Token Response Status:", token_res.status_code)

    if "access_token" not in token_data:
        print("❌ Token Error:", token_data)
        return jsonify({"error": "Failed to fetch token", "details": token_data}), 400

    # Save token in Flask session
    session["access_token"] = token_data["access_token"]
    print("✅ Token saved successfully")
    return redirect("/playlists")


@app.route("/playlists")
def playlists():
    token = session.get("access_token")
    if not token:
        return redirect("/login")

    # Validate token before using it
    if not validate_token(token):
        session.clear()
        return redirect("/login")

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get("https://api.spotify.com/v1/me/playlists", headers=headers)
    if res.status_code != 200:
        print("❌ Failed to fetch playlists:", res.status_code, res.text)
        return jsonify({"error": "Failed to fetch playlists"}), 400

    data = res.json()
    playlists = []

    for p in data["items"]:
        track_ids = get_track_ids(p["id"], headers)
        playlists.append({
            "id": p["id"],
            "name": p["name"],
            "image": p["images"][0]["url"] if p["images"] else "",
            "tracks": p["tracks"]["total"],
            "track_ids": track_ids
        })

    return render_template("playlists.html", playlists=playlists)


@app.route("/analyze", methods=["POST"])
def analyze():
    token = session.get("access_token")
    if not token:
        return jsonify({"error": "No access token found"}), 401
    
    # Validate token first
    if not validate_token(token):
        session.clear()
        return jsonify({"error": "Token expired or invalid"}), 401
    
    print("DEBUG: Starting analysis...")

    try:
        data = request.get_json()
        track_ids = data.get("track_ids", [])
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400

    if not track_ids:
        return jsonify({"error": "No track IDs received"}), 400

    # Filter out any None or empty track IDs
    valid_track_ids = [tid for tid in track_ids if tid and isinstance(tid, str) and len(tid) == 22]
    
    if not valid_track_ids:
        return jsonify({"error": "No valid track IDs found"}), 400
    
    print(f"Valid track IDs: {len(valid_track_ids)}")

    headers = {"Authorization": f"Bearer {token}"}
    
    # Use simple analysis since Spotify Audio Features is deprecated
    try:
        result = analyze_tracks_simple(valid_track_ids, headers)
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500
    
    if "error" in result:
        return jsonify(result), 400
    
    print("✅ Analysis completed successfully")
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)