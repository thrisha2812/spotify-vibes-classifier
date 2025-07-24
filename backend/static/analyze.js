document.addEventListener("DOMContentLoaded", function () {
  const analyzeBtn = document.getElementById("analyze-btn"); // ✅ Ensure your HTML uses this exact ID

  if (!analyzeBtn) {
    console.error("Analyze button not found");
    return;
  }

  analyzeBtn.addEventListener("click", function (e) {
    e.preventDefault(); // Prevent default form submission if inside a <form>

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

    fetch("/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ track_ids: allTrackIDs })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
          alert(data.error);
        } else {
          const resultBox = document.getElementById("vibe-result");
          if (resultBox) {
            resultBox.innerHTML = `
              <h3>${data.vibe}</h3>
              <p><strong>Energy:</strong> ${data.average_features.energy.toFixed(2)}</p>
              <p><strong>Valence:</strong> ${data.average_features.valence.toFixed(2)}</p>
              <p><strong>Danceability:</strong> ${data.average_features.danceability.toFixed(2)}</p>
              <p><strong>Acousticness:</strong> ${data.average_features.acousticness.toFixed(2)}</p>
              <p><strong>Tempo:</strong> ${data.average_features.tempo.toFixed(1)} BPM</p>
            `;
          }
        }
      })
      .catch(err => {
        console.error("Error during /analyze fetch:", err);
        alert("Something went wrong. Please try again.");
      });
  });
});

