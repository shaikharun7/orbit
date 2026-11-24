# 3D Satellite Tracking Dashboard (N2YO)

A local Flask + Globe.gl dashboard that displays an interactive 3D Earth and satellite positions from the N2YO REST API.

## Important accuracy note

The dashboard displays **calculated near-real-time positions**, not continuous direct measurements from a radar or from the spacecraft. N2YO's positions endpoint returns a current-time calculation followed by up to 300 seconds of calculated positions (one position per second). The dashboard animates the satellite marker through that short prediction window and asks for a refreshed window about every 235 seconds.

This is suitable for a student visualization/demo. N2YO positions alone are not enough to calculate validated collision probability or make operational manoeuvre decisions. Use CDM state and covariance information, object size, validated propagation and appropriate screening for those tasks.

## 1. Get a free N2YO API key

1. Visit https://www.n2yo.com/api/ .
2. Create an account and sign in.
3. Generate your REST API key from your profile page.
4. The N2YO API is free within its published transaction limits. Current documentation lists 1,000 requests/hour for the `positions` operation. Limits can change; check the official page.

## 2. Install and configure

You need Python 3.10 or newer.

### Windows

1. Extract this ZIP file into a folder.
2. Double-click `run_windows.bat` once. It creates a virtual environment and installs the required packages. It also creates `.env` from `.env.example` if needed.
3. Open the `.env` file in Notepad.
4. Replace `PASTE_YOUR_N2YO_API_KEY_HERE` with your real API key. Save the file.
5. Double-click `run_windows_after_setup.bat`.
6. Open http://127.0.0.1:5000 in Chrome or Edge.

### macOS / Linux

From this folder, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add your N2YO API key, then run:

```bash
python app.py
```

Open http://127.0.0.1:5000.

## 3. Satellites included

- ISS — NORAD catalog ID 25544
- Hubble Space Telescope — NORAD catalog ID 20580

You can add another satellite by entering its NORAD catalog ID in the dashboard. The name is retrieved from N2YO.

## 4. How the refresh works

- The server requests a 300-second position window for each selected satellite.
- The browser animates the marker along those returned positions, using their UTC timestamps.
- The server caches each response for about 235 seconds to reduce API calls and preserve a small overlap between windows.
- The “Refresh now” button requests a new position window immediately.

The API requires observer latitude, longitude and altitude in its URL. This demo supplies `0/0/0`; the dashboard uses the returned global sub-satellite latitude, longitude and altitude. Observer-relative azimuth/elevation are not displayed.

## 5. Security

- Your API key is read by the local Python server from `.env`; it is not embedded in the browser HTML.
- Do not share your `.env` file or publish it to GitHub.
- The included Flask server is for local demonstration. For a public deployment, use a production WSGI server, HTTPS, server-side secret storage, authentication, rate limiting and proper monitoring.

## 6. External resources

The page loads Globe.gl, Three.js dependencies and an Earth texture from public CDNs. It therefore needs an internet connection while the dashboard is open.

- N2YO API: https://www.n2yo.com/api/
- Globe.gl: https://globe.gl/
