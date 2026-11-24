from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from threading import Lock
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
API_KEY = os.getenv("N2YO_API_KEY", "").strip()
N2YO_BASE = "https://api.n2yo.com/rest/v1/satellite"
WINDOW_SECONDS = 300
# Request a new five-minute position window approximately every four minutes.
# This leaves a small overlap and avoids asking N2YO for a new window every second.
CACHE_TTL_SECONDS = 235
DEFAULT_SATELLITES = [
    {"norad_id": 25544, "label": "International Space Station"},
    {"norad_id": 20580, "label": "Hubble Space Telescope"},
]

_cache: dict[int, dict[str, Any]] = {}
_cache_lock = Lock()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/config")
def config():
    return jsonify({
        "api_configured": bool(API_KEY),
        "default_satellites": DEFAULT_SATELLITES,
        "window_seconds": WINDOW_SECONDS,
        "refresh_after_seconds": CACHE_TTL_SECONDS,
        "source": "N2YO REST API",
    })


def fetch_n2yo_positions(norad_id: int, force: bool = False) -> dict[str, Any]:
    if not API_KEY:
        raise RuntimeError("N2YO_API_KEY is not configured. Add your key to the .env file and restart the dashboard.")
    if norad_id <= 0 or norad_id > 999999:
        raise ValueError("Enter a valid positive NORAD catalog ID.")

    now = time.time()
    with _cache_lock:
        cached = _cache.get(norad_id)
        if cached and not force and now - cached["cached_at"] < CACHE_TTL_SECONDS:
            return cached["payload"]

    # Observer coordinates are required by this N2YO endpoint. They affect
    # observer-relative azimuth/elevation fields, not the global sub-satellite
    # latitude/longitude/altitude used by this 3D globe.
    url = f"{N2YO_BASE}/positions/{norad_id}/0/0/0/{WINDOW_SECONDS}"
    response = requests.get(url, params={"apiKey": API_KEY}, timeout=20)
    if response.status_code == 401 or response.status_code == 403:
        raise RuntimeError("N2YO rejected the API key. Check that your free API key is correct.")
    response.raise_for_status()
    data = response.json()

    info = data.get("info") or {}
    positions = data.get("positions") or []
    if not positions:
        raise RuntimeError("N2YO returned no position records for this satellite.")

    # Keep only the fields required by the dashboard.
    clean_positions = []
    for p in positions:
        try:
            clean_positions.append({
                "lat": float(p["satlatitude"]),
                "lng": float(p["satlongitude"]),
                "alt_km": float(p["sataltitude"]),
                "timestamp": int(p["timestamp"]),
            })
        except (KeyError, TypeError, ValueError):
            continue

    if not clean_positions:
        raise RuntimeError("N2YO returned position data in an unexpected format.")

    payload = {
        "norad_id": int(info.get("satid", norad_id)),
        "name": info.get("satname") or f"NORAD {norad_id}",
        "positions": clean_positions,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "window_seconds": WINDOW_SECONDS,
        "source": "N2YO calculated position API",
        "transaction_count": info.get("transactionscount"),
    }
    with _cache_lock:
        _cache[norad_id] = {"cached_at": time.time(), "payload": payload}
    return payload


@app.get("/api/positions/<int:norad_id>")
def positions(norad_id: int):
    force = request.args.get("refresh", "0") == "1"
    try:
        payload = fetch_n2yo_positions(norad_id, force=force)
        return jsonify(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except requests.RequestException as exc:
        return jsonify({"error": f"Could not reach N2YO: {exc}"}), 502
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:  # Defensive API boundary for a demo application.
        app.logger.exception("Unexpected satellite positions error")
        return jsonify({"error": f"Unexpected server error: {exc}"}), 500


if __name__ == "__main__":
    # Local development/demo server only. Use a production WSGI server if deployed.
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
