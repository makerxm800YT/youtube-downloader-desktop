#!/usr/bin/env python3
"""
YouTube Downloader Desktop v4 - Updated
"""

import subprocess, sys, os

def _pip(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

for _p, _i in [("yt-dlp", "yt_dlp"), ("static-ffmpeg", "static_ffmpeg"), ("pillow", "PIL")]:
    try:
        __import__(_i)
    except:
        print(f"Installing {_p}...")
        _pip(_p)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, re, json, hashlib, datetime, time
import yt_dlp, static_ffmpeg, shutil
from PIL import Image, ImageTk
import requests
import io

static_ffmpeg.add_paths()
FFMPEG = shutil.which("ffmpeg") or ""

APP_DIR = os.path.join(os.path.expanduser("~"), ".ytdl_app")
ACCS_FILE = os.path.join(APP_DIR, "accounts.json")
HIST_FILE = os.path.join(APP_DIR, "history.json")
SESS_FILE = os.path.join(APP_DIR, "session.json")
os.makedirs(APP_DIR, exist_ok=True)

def jload(p, d):
    try:
        with open(p) as f: return json.load(f)
    except: return d

def jsave(p, d):
    with open(p, "w") as f: json.dump(d, f, indent=2)

def hashpw(pw): return hashlib.sha256(pw.encode()).hexdigest()

# Colors
C = {
    "bg": "#0b0b0b", "bg2": "#111111", "card": "#161616", "s3": "#242424",
    "red": "#e63232", "redh": "#ff4f4f", "grn": "#22c55e", "fg": "#f2f2f2",
    "fg2": "#888", "fg3": "#444"
}

# ================== MAIN APP ==================
class MainApp(tk.Tk):
    def __init__(self, email, name):
        super().__init__()
        self.title("YouTube Downloader")
        self.geometry("820x680")
        self.configure(bg=C["bg"])
        self._email = email
        self._name = name
        self.savepath = os.path.join(os.path.expanduser("~"), "Downloads")

        self.url_v = tk.StringVar()
        self.mode_v = tk.StringVar(value="Video")
        self.qual_v = tk.StringVar(value="Best (Max Quality)")
        self.fmt_v = tk.StringVar(value="mp4")

        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=C["bg2"], height=60)
        hdr.pack(fill="x")
        tk.Label(hdr, text="YouTube Downloader", bg=C["bg2"], fg="white", font=("Syne", 16, "bold")).pack(side="left", padx=20, pady=15)

        # User info
        user_frame = tk.Frame(hdr, bg=C["bg2"])
        user_frame.pack(side="right", padx=20)
        tk.Label(user_frame, text=self._name, bg=C["bg2"], fg=C["fg"], font=("bold", 12)).pack(anchor="e")
        tk.Label(user_frame, text=self._email, bg=C["bg2"], fg=C["fg3"], font=("small", 9)).pack(anchor="e")

        # Download Page (Main)
        main_frame = tk.Frame(self, bg=C["bg"], padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)

        # URL
        tk.Label(main_frame, text="YouTube URL", bg=C["bg"], fg=C["fg2"], font=("bold", 10)).pack(anchor="w")
        url_entry = tk.Entry(main_frame, textvariable=self.url_v, font=("DM Mono", 11), bg=C["s3"], fg=C["fg"], relief="flat", bd=0)
        url_entry.pack(fill="x", ipady=12, pady=(5,15))

        # Options
        opt_frame = tk.Frame(main_frame, bg=C["bg"])
        opt_frame.pack(fill="x", pady=10)
        
        for text, var, options in [
            ("Mode", self.mode_v, ["Video", "Audio Only"]),
            ("Quality", self.qual_v, ["Best (Max Quality)", "1080p", "720p", "480p"]),
            ("Format", self.fmt_v, ["mp4", "mp3"])
        ]:
            f = tk.Frame(opt_frame, bg=C["bg"])
            f.pack(side="left", padx=15)
            tk.Label(f, text=text, bg=C["bg"], fg=C["fg2"]).pack(anchor="w")
            ttk.OptionMenu(f, var, options[0], *options).pack()

        # Download Button
        dl_btn = tk.Button(main_frame, text="⬇ DOWNLOAD NOW", bg=C["red"], fg="white",
                           font=("bold", 14), height=2, command=self.start_download)
        dl_btn.pack(fill="x", pady=20)

        # Log
        self.log = tk.Text(main_frame, height=12, bg="#0a0a0a", fg=C["fg3"], font=("DM Mono", 10))
        self.log.pack(fill="both", expand=True)

    def start_download(self):
        url = self.url_v.get().strip()
        if not url:
            messagebox.showwarning("Error", "Please paste a URL")
            return

        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, f"Starting download: {url}\n")

        def run():
            try:
                ydl_opts = {
                    'outtmpl': os.path.join(self.savepath, '%(title)s.%(ext)s'),
                    'progress_hooks': [self._progress_hook],
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                self.log.insert(tk.END, "✅ Download Complete!\n")
            except Exception as e:
                self.log.insert(tk.END, f"❌ Error: {e}\n")

        threading.Thread(target=run, daemon=True).start()

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            self.log.insert(tk.END, f"Downloading... {d.get('_percent_str', '')}\n")
            self.log.see(tk.END)

# ================== START APP ==================
if __name__ == "__main__":
    try:
        sess = jload(SESS_FILE, {})
        if sess.get("email"):
            MainApp(sess["email"], sess.get("name", "User")).mainloop()
        else:
            # Simple login can be added later
            MainApp("user@example.com", "User").mainloop()
    except Exception as e:
        print("Error:", e)
        input("Press Enter to exit...")
