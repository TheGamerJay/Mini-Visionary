"""
test_api.py — basic tests for Mini Dream Poster API

Run with:
    pytest test_api.py
or
    python test_api.py
"""

import os
import json
import requests

BASE_URL = os.getenv("API_BASE", "http://localhost:8080")

def test_health():
    r = requests.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200
    data = r.json()
    print("Health:", data)
    assert data.get("ok") is True
    assert data.get("service") == "mini-dream-poster"

def test_generate_text_poster():
    fd = {
        "prompt": "Epic fantasy warrior standing on a cosmic cliff",
        "style": "cinematic vivid fantasy key art",
        "title": "WARRIOR OF THE COSMOS",
        "tagline": "Where stars bow to steel."
    }
    r = requests.post(f"{BASE_URL}/api/poster/generate", data=fd)
    assert r.status_code == 200
    data = r.json()
    print("Text Poster:", json.dumps(data, indent=2))
    assert data.get("ok") is True
    assert "url" in data

def test_generate_with_image():
    # Needs a sample image in repo/tests
    sample_path = os.path.join(os.path.dirname(__file__), "sample.jpg")
    if not os.path.exists(sample_path):
        print("Skipping image test (no sample.jpg found)")
        return

    fd = {
        "prompt": "Turn this into a cinematic poster",
        "style": "sci-fi movie poster"
    }
    files = {"image": open(sample_path, "rb")}
    r = requests.post(f"{BASE_URL}/api/poster/generate", data=fd, files=files)
    files["image"].close()

    assert r.status_code == 200
    data = r.json()
    print("Image Poster:", json.dumps(data, indent=2))
    assert data.get("ok") is True
    assert "url" in data

def test_add_text_overlay():
    # First generate a poster
    fd = {"prompt": "A lone tree in a mystical valley"}
    r = requests.post(f"{BASE_URL}/api/poster/generate", data=fd)
    assert r.status_code == 200
    poster = r.json()
    assert poster.get("ok") is True

    # Now add overlay
    body = {
        "url": poster["url"],
        "title": "THE LONE TREE",
        "tagline": "Whispers in the valley"
    }
    r2 = requests.post(f"{BASE_URL}/api/poster/add-text", json=body)
    assert r2.status_code == 200
    data = r2.json()
    print("Overlay Poster:", json.dumps(data, indent=2))
    assert data.get("ok") is True
    assert "url" in data

if __name__ == "__main__":
    # Allow running directly
    test_health()
    test_generate_text_poster()
    test_generate_with_image()
    test_add_text_overlay()
    print("✅ All Mini Dream Poster tests passed")