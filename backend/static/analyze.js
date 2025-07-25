document.addEventListener("DOMContentLoaded", function () {
  const analyzeBtn = document.getElementById("analyze-btn");

  if (!analyzeBtn) {
    console.error("Analyze button not found");
    return;
  }

  analyzeBtn.addEventListener("click", function (e) {
    e.preventDefault();

    const checkboxes = document.querySelectorAll('input[name="playlist_ids"]:checked');
    if (checkboxes.length === 0) {
      alert("Please select at least one playlist!");
      return;
    }

    let allTrackIDs = [];
    checkboxes.forEach(cb => {
      const trackData = cb.getAttribute("data-track-ids");
      if (trackData) {
        try {
          const ids = JSON.parse(trackData);
          allTrackIDs.push(...ids);
        } catch (err) {
          console.error("⚠️ Failed to parse track IDs:", err);
        }
      }
    });

    if (allTrackIDs.length === 0) {
      alert("No track IDs found for selected playlists.");
      return;
    }

    console.log("All selected track IDs:", allTrackIDs);
    console.log("Sending to /analyze:", JSON.stringify({ track_ids: allTrackIDs }));

    // Show loading state
    const resultBox = document.getElementById("vibe-result");
    if (resultBox) {
      resultBox.innerHTML = "<p>Analyzing your music taste... 🎵</p>";
    }

    fetch("/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ track_ids: allTrackIDs })
    })
    .then(res => res.json())
    .then(data => {
        console.log("Response data:", data); // Debug log
        if (data.error) {
          alert(data.error);
        } else {
          if (resultBox) {
            // Use the correct property names from your Flask response
            resultBox.innerHTML = `
              <h3>${data.vibe}</h3>
              <div style="margin-top: 15px;">
                <p><strong>Average Popularity:</strong> ${data.analysis.avg_popularity}/100</p>
                <p><strong>Average Duration:</strong> ${data.analysis.avg_duration_minutes} minutes</p>
                <p><strong>Explicit Content:</strong> ${data.analysis.explicit_ratio}%</p>
                <p><strong>Average Release Year:</strong> ${data.analysis.avg_release_year}</p>
                <p><strong>Tracks Analyzed:</strong> ${data.analysis.tracks_analyzed}</p>
                ${data.analysis.top_genres.length > 0 ? `
                  <p><strong>Top Genres:</strong></p>
                  <ul>
                    ${data.analysis.top_genres.map(genre => `<li>${genre[0]} (${genre[1]} songs)</li>`).join('')}
                  </ul>
                ` : ''}
              </div>
            `;
          }
        }
      })
      .catch(err => {
        console.error("Error during /analyze fetch:", err);
        alert("Something went wrong. Please try again.");
        if (resultBox) {
  const report = `
Vibe: ${data.vibe}
Energy: ${data.average_features.energy.toFixed(2)}
Valence: ${data.average_features.valence.toFixed(2)}
Danceability: ${data.average_features.danceability.toFixed(2)}
Acousticness: ${data.average_features.acousticness.toFixed(2)}
Tempo: ${data.average_features.tempo.toFixed(1)} BPM
`;

  resultBox.innerHTML = `
    <h3>${data.vibe}</h3>
    <p><strong>Energy:</strong> ${data.average_features.energy.toFixed(2)}</p>
    <p><strong>Valence:</strong> ${data.average_features.valence.toFixed(2)}</p>
    <p><strong>Danceability:</strong> ${data.average_features.danceability.toFixed(2)}</p>
    <p><strong>Acousticness:</strong> ${data.average_features.acousticness.toFixed(2)}</p>
    <p><strong>Tempo:</strong> ${data.average_features.tempo.toFixed(1)} BPM</p>
  `;

  // Enable download
  const downloadBtn = document.getElementById("download-btn");
  if (downloadBtn) {
    downloadBtn.onclick = function () {
      const blob = new Blob([report], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "vibe_report.txt";
      a.click();
    };
  }
}

      });
  });
});
