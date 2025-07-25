Sure, Trisha! Here's a clean and professional `README.md` file for your **Spotify Playlist Vibes Classifier** project — excluding the download feature.

---

### 📄 `README.md`

````markdown
# 🎵 Spotify Playlist Vibes Classifier

This web application allows users to log in with their Spotify account, select their playlists, and analyze the musical "vibe" of each playlist using features like energy, danceability, valence, and tempo.

---

## 🚀 Features

- **Spotify Login with OAuth**
- **Fetch and Display User Playlists**
- **Select Multiple Playlists for Analysis**
- **Mocked Audio Feature Analysis** (Due to API restrictions)
- **Displays Mood Insights** such as:
  - Energy
  - Danceability
  - Valence
  - Acousticness
  - Tempo
  - Genre Trends
  - Popularity, Duration, Explicit Ratio, and Release Year

---

## 🧪 Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask (Python)
- **Authentication**: Spotify OAuth 2.0
- **Mocked Data**: Simulates audio features locally
- **Charting**: [Chart.js](https://www.chartjs.org/) for visual insights

---

## 🧰 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/spotify-vibes-classifier.git
cd spotify-vibes-classifier
````

### 2. Set Up a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:5000/callback
SECRET_KEY=any_random_secret_key
```

### 5. Run the App

```bash
cd backend
flask run
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.


## 📁 Project Structure

```
spotify-vibes-classifier/
│
├── backend/
│   ├── app.py
│   ├── mocked_data.py
│   ├── templates/
│   │   └── playlists.html
│   └── static/
│       └── analyze.js
│
├── requirements.txt
└── README.md


