/**
 * Fetches and displays the list of training runs from runs.json.
 *
 * This function retrieves the run manifest, clears the loading state,
 * and renders a card for each run containing its metadata and download links.
 */
async function loadRuns() {
  const runsEl = document.getElementById("runs");
  runsEl.innerHTML = "<p>Loading runs…</p>";
  try {
    const resp = await fetch("runs.json");
    const runs = await resp.json();

    runsEl.innerHTML = "";
    for (const r of runs) {
      const card = document.createElement("div");
      card.className = "card";
      card.innerHTML = `
        <h2>${r.name}</h2>
        <p><strong>Merkle root:</strong> ${r.merkle_root}</p>
        <p><strong>Steps:</strong> ${r.num_steps}</p>
        <p><strong>Torrent:</strong> <a href="${r.torrent_file}">${r.torrent_file}</a></p>
        <p><strong>Magnet:</strong> <code>${r.magnet}</code></p>
        <details>
          <summary>Manifest</summary>
          <pre>${JSON.stringify(r, null, 2)}</pre>
        </details>
      `;
      runsEl.appendChild(card);
    }
  } catch (e) {
    runsEl.innerHTML = "<p>No runs.json found. Publish artifacts first.</p>";
  }
}
loadRuns();
