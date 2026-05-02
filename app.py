#!/usr/bin/env python3
"""
YouTube Downloader Desktop — Backend
"""

import subprocess, sys, os, json, hashlib, datetime, threading, uuid, re, time, shutil, platform
from pathlib import Path

def pip(pkg):
    subprocess.check_call([sys.executable,"-m","pip","install",pkg,"-q"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

for p,i in [("flask","flask"),("yt-dlp","yt_dlp"),("static-ffmpeg","static_ffmpeg")]:
    try: __import__(i)
    except: print(f"Installing {p}..."); pip(p)

from flask import Flask, request, jsonify, Response, send_from_directory
import yt_dlp, static_ffmpeg

# Add ffmpeg to path
static_ffmpeg.add_paths()
FFMPEG = shutil.which("ffmpeg") or ""

# Desktop-specific paths
if platform.system() == "Windows":
    APP_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser("~")), "YouTubeDownloader")
else:
    APP_DIR = os.path.join(os.path.expanduser("~"), ".youtube_downloader")

ACCS_FILE = os.path.join(APP_DIR, "accounts.json")
HIST_FILE = os.path.join(APP_DIR, "history.json")
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")

os.makedirs(APP_DIR, exist_ok=True)

def jload(p, d):
    try:
        with open(p, 'r', encoding='utf-8') as f: return json.load(f)
    except: return d

def jsave(p, d):
    with open(p, 'w', encoding='utf-8') as f: json.dump(d, f, indent=2)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

app = Flask(__name__, static_folder="static", template_folder="templates")
_jobs = {}
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load desktop settings
def get_download_path():
    settings = jload(SETTINGS_FILE, {})
    default = os.path.join(os.path.expanduser("~"), "Downloads")
    return settings.get("download_path", default)

@app.route("/")
def index():
    return send_from_directory(SCRIPT_DIR, "index.html")

@app.route("/favicon.svg")
def favicon():
    return send_from_directory(SCRIPT_DIR, "favicon.svg")

# ── Auth Routes ──
@app.route("/api/register", methods=["POST"])
def register():
    d = request.json
    accs = jload(ACCS_FILE, {})
    email = d.get("email","").strip().lower()
    pw = d.get("password","")
    name = d.get("name","").strip()
    
    if not email or "@" not in email:
        return jsonify(error="Invalid email address"), 400
    if not pw or len(pw) < 6:
        return jsonify(error="Password must be at least 6 characters"), 400
    if not name:
        return jsonify(error="Name is required"), 400
    if email in accs:
        return jsonify(error="Account already exists"), 409
    
    accs[email] = {
        "name": name,
        "pw_hash": hash_pw(pw),
        "joined": datetime.date.today().isoformat(),
        "method": "email"
    }
    jsave(ACCS_FILE, accs)
    return jsonify(ok=True, name=name, email=email, method="email")

@app.route("/api/login", methods=["POST"])
def login():
    d = request.json
    accs = jload(ACCS_FILE, {})
    email = d.get("email","").strip().lower()
    pw = d.get("password","")
    
    if email not in accs:
        return jsonify(error="No account found"), 404
    if accs[email].get("pw_hash") != hash_pw(pw):
        return jsonify(error="Incorrect password"), 401
    
    u = accs[email]
    return jsonify(ok=True, name=u["name"], email=email, method=u.get("method","email"))

@app.route("/api/google-login", methods=["POST"])
def google_login():
    d = request.json
    accs = jload(ACCS_FILE, {})
    email = d.get("email","").strip().lower()
    
    if not email or "@" not in email:
        return jsonify(error="Valid email required"), 400
    
    if email not in accs:
        gname = email.split("@")[0].replace(".", " ").title()
        accs[email] = {
            "name": gname,
            "pw_hash": "",
            "joined": datetime.date.today().isoformat(),
            "method": "google"
        }
        jsave(ACCS_FILE, accs)
    
    u = accs[email]
    return jsonify(ok=True, name=u["name"], email=email, method=u.get("method","google"))

# ── History Routes ──
@app.route("/api/history")
def get_history():
    email = request.args.get("user","")
    hist = jload(HIST_FILE, [])
    mine = [h for h in hist if h.get("user") == email]
    return jsonify(mine[-100:])

@app.route("/api/history/clear", methods=["DELETE"])
def clear_history():
    email = request.args.get("user","")
    hist = jload(HIST_FILE, [])
    hist = [h for h in hist if h.get("user") != email]
    jsave(HIST_FILE, hist)
    return jsonify(ok=True)

# ── Download Routes ──
@app.route("/api/download", methods=["POST"])
def start_download():
    d = request.json
    url = d.get("url","").strip()
    mode = d.get("mode","Video")
    quality = d.get("quality","Best (Max Quality)")
    fmt = d.get("format","mp4")
    user = d.get("user","")
    
    # Use desktop settings or default
    download_path = get_download_path()
    
    if not url:
        return jsonify(error="No URL provided"), 400

    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "status": "starting",
        "progress": 0,
        "speed": "—",
        "eta": "—",
        "log": [],
        "title": "",
        "error": None,
        "done": False
    }

    def run():
        job = _jobs[job_id]
        q_map = {
            "Best (Max Quality)": "bestvideo+bestaudio/best",
            "4K": "bestvideo[height<=2160]+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best",
            "720p": "bestvideo[height<=720]+bestaudio/best",
            "480p": "bestvideo[height<=480]+bestaudio/best",
            "360p": "bestvideo[height<=360]+bestaudio/best",
        }
        
        is_audio = "Audio" in mode
        is_playlist = "Playlist" in mode
        out_tmpl = os.path.join(download_path, "%(title)s.%(ext)s")

        opts = {
            "outtmpl": out_tmpl,
            "noplaylist": not is_playlist,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "progress_hooks": [lambda d: _hook(job, d)],
        }
        
        if FFMPEG:
            opts["ffmpeg_location"] = os.path.dirname(FFMPEG)

        if is_audio:
            ext = fmt if fmt in ("mp3","m4a") else "mp3"
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": ext,
                "preferredquality": "320"
            }]
        else:
            opts["format"] = q_map.get(quality, "bestvideo+bestaudio/best")
            opts["merge_output_format"] = fmt if fmt in ("mp4","mkv","webm") else "mp4"

        title = url
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as y:
                try:
                    info = y.extract_info(url, download=False)
                    title = info.get("title", url)[:80]
                    job["title"] = title
                    job["log"].append({"text": title, "type": "dim"})
                except:
                    pass

            job["status"] = "downloading"
            with yt_dlp.YoutubeDL(opts) as y:
                y.download([url])

            job["status"] = "done"
            job["progress"] = 100
            job["done"] = True
            job["log"].append({"text": f"✔ Complete! Saved to: {download_path}", "type": "success"})

            hist = jload(HIST_FILE, [])
            hist.append({
                "user": user,
                "url": url,
                "title": title,
                "mode": mode,
                "quality": quality,
                "format": fmt,
                "status": "done",
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            jsave(HIST_FILE, hist)

        except Exception as e:
            job["status"] = "error"
            job["error"] = str(e)
            job["done"] = True
            job["log"].append({"text": f"✖ Error: {e}", "type": "error"})

    threading.Thread(target=run, daemon=True).start()
    return jsonify(job_id=job_id)

def _hook(job, d):
    if d["status"] == "downloading":
        raw = d.get("_percent_str", "0%").strip()
        pct = float(re.sub(r"[^\d.]", "", raw) or 0)
        job["progress"] = pct
        job["speed"] = d.get("_speed_str", "—").strip()
        job["eta"] = d.get("_eta_str", "—").strip()
        job["status"] = "downloading"
    elif d["status"] == "finished":
        job["status"] = "merging"
        job["log"].append({"text": "Merging audio/video...", "type": "dim"})

@app.route("/api/progress/<job_id>")
def progress(job_id):
    def stream():
        last_log = 0
        while True:
            job = _jobs.get(job_id)
            if not job:
                yield f"data: {json.dumps({'error':'not found'})}\n\n"
                break
            logs_new = job["log"][last_log:]
            last_log = len(job["log"])
            payload = {
                "status": job["status"],
                "progress": job["progress"],
                "speed": job["speed"],
                "eta": job["eta"],
                "title": job["title"],
                "new_logs": logs_new,
                "done": job["done"],
                "error": job["error"],
            }
            yield f"data: {json.dumps(payload)}\n\n"
            if job["done"]:
                break
            time.sleep(0.4)
    return Response(stream(), mimetype="text/event-stream")

@app.route("/api/ytdlp-version")
def ytdlp_version():
    return jsonify(version=yt_dlp.version.__version__)

@app.route("/api/update-ytdlp", methods=["POST"])
def update_ytdlp():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        return jsonify(ok=True, message="yt-dlp updated! Restart app to apply.")
    except Exception as e:
        return jsonify(ok=False, message=str(e))

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  🎬 YouTube Downloader Desktop")
    print("="*50)
    print(f"  📁 Save folder: {get_download_path()}")
    print(f"  🎵 FFmpeg: {'✓ Ready' if FFMPEG else '✗ Not found'}")
    print("  🌐 Starting server at: http://localhost:5000")
    print("="*50 + "\n")
    app.run(port=5000, debug=False, threaded=True)
