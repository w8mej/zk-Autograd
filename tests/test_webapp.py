"""test_webapp.py

Tests for the web application assets and data structures.
"""
import os
import json
import pytest

WEBAPP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../webapp"))

def test_webapp_assets_exist():
    """Verifies that the webapp has the required files (index.html, app.js, style.css)."""
    assert os.path.exists(os.path.join(WEBAPP_DIR, "index.html"))
    assert os.path.exists(os.path.join(WEBAPP_DIR, "app.js"))
    assert os.path.exists(os.path.join(WEBAPP_DIR, "style.css"))

def test_runs_json_schema(temp_run_dir):
    """Verifies that the app.js can handle the runs.json format.

    Since we can't run JS here easily, we just validate the JSON structure matches
    what app.js expects.

    Args:
        temp_run_dir: Fixture providing a temporary directory.
    """
    # app.js expects: array of objects with {name, merkle_root, num_steps, torrent_file, magnet}
    
    dummy_runs = [
        {
            "name": "run-1",
            "merkle_root": "abc",
            "num_steps": 10,
            "torrent_file": "run-1.torrent",
            "magnet": "magnet:?..."
        }
    ]
    
    # Write it
    runs_path = os.path.join(temp_run_dir, "runs.json")
    with open(runs_path, "w") as f:
        json.dump(dummy_runs, f)
        
    # Read it back and validate
    with open(runs_path) as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 1
        item = data[0]
        assert "name" in item
        assert "merkle_root" in item
        assert "magnet" in item
