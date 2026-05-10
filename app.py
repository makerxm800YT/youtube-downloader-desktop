#!/usr/bin/env python3
"""
YouTube Downloader Desktop v4
Clean & Reliable Version
"""

import subprocess, sys, os

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Install required packages
for pkg, imp in [("yt-dlp", "yt_dlp"), ("static-ffmpeg", "static_ffmpeg"), ("pillow", "PIL")]:
    try:
        __import__(imp)
    except:
        print(f"Installing {pkg}...")
        install(pkg)

import tkinter as tk
from tkinter import filedialog, messagebox
import threading, re, json, hashlib, datetime
import yt_dlp, static_ffmpeg, shutil
from PIL import Image, ImageTk
import requests, io

static_ffmpeg.add_paths()

# ===================== CONFIG =====================
APP_DIR = os.path.join(os.path.expanduser("~"), ".ytdl_app")
ACCS_FILE = os.path.join(APP_DIR, "accounts.json")
HIST_FILE = os.path.join(APP_DIR, "history.json")
SESS_FILE = os.path.join(APP_DIR, "session.json")
os.makedirs(APP_DIR, exist_ok=True)

def jload(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return default

def jsave(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ===================== MAIN APP =====================
class YouTubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader Desktop v4")
        self.geometry("860x720")
        self.configure(bg="#0b0b0b")
        self.resizable(True, True)

        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.current_user = {"name": "User", "email": "user@example.com"}

        self.build_ui()

    def build_ui(self):
        # Header
        header = tk.Frame(self, bg="#111111", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="YouTube Downloader", font=("Syne", 18, "bold"), 
                 bg="#111111", fg="#ff4f4f").pack(side="left", padx=25, pady=20)

        # User info
        user_frame = tk.Frame(header, bg="#111111")
        user_frame.pack(side="right", padx=25)
        tk.Label(user_frame, text=self.current_user["name"], fg="white", bg="#111111", 
                 font=("bold", 12)).pack(anchor="e")
        tk.Label(user_frame, text=self.current_user["email"], fg="#888", bg="#111111", 
                 font=("small", 9)).pack(anchor="e")

        # Main Content
        main = tk.Frame(self, bg="#0b0b0b", padx=30, pady=20)
        main.pack(fill="both", expand=True)

        # URL Input
        tk.Label(main, text="YouTube URL or Shorts Link", bg="#0b0b0b", fg="#ccc", 
                 font=("bold", 11)).pack(anchor="w")
        self.url_entry = tk.Entry(main, font=("DM Mono", 11), bg="#1f1f1f", fg="white", 
                                  relief="flat", bd=0, insertbackground="#ff4f4f")
        self.url_entry.pack(fill="x", ipady=14, pady=(8, 20))

        # Options
        options = tk.Frame(main, bg="#0b0b0b")
        options.pack(fill="x", pady=10)

        # Mode
        tk.Label(options, text="Mode", bg="#0b0b0b", fg="#aaa").grid(row=0, column=0, sticky="w", padx=10)
        self.mode_var = tk.StringVar(value="Video")
        tk.OptionMenu(options, self.mode_var, "Video", "Audio Only", "Playlist").grid(row=1, column=0, padx=10, sticky="w")

        # Quality
        tk.Label(options, text="Quality", bg="#0b0b0b", fg="#aaa").grid(row=0, column=1, sticky="w", padx=10)
        self.qual_var = tk.StringVar(value="Best (Max Quality)")
        tk.OptionMenu(options, self.qual_var, "Best (Max Quality)", "1080p", "720p", "480p", "360p").grid(row=1, column=1, padx=10, sticky="w")

        # Format
        tk.Label(options, text="Format", bg="#0b0b0b", fg="#aaa").grid(row=0, column=2, sticky="w", padx=10)
        self.format_var = tk.StringVar(value="mp4")
        tk.OptionMenu(options, self.format_var, "mp4", "mp3", "m4a").grid(row=1, column=2, padx=10, sticky="w")

        # Download Button
        self.dl_btn = tk.Button(main, text="⬇ DOWNLOAD NOW", font=("bold", 16), 
                                bg="#e63232", fg="white", height=2, command=self.start_download)
        self.dl_btn.pack(fill="x", pady=25)

        # Log Console
        tk.Label(main, text="Log", bg="#0b0b0b", fg="#ccc").pack(anchor="w")
        self.log_text = tk.Text(main, bg="#111111", fg="#0f0", font=("DM Mono", 10), height=18)
        self.log_text.pack(fill="both", expand=True, pady=(8,0))

    def log(self, text):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Error", "Please enter a YouTube URL")
            return

        self.dl_btn.config(state="disabled")
        self.log("▶ Starting download...")
        self.log(f"URL: {url}")

        def download_thread():
            try:
                opts = {
                    'outtmpl': os.path.join(self.save_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.progress_hook],
                    'quiet': False,
                }

                if self.mode_var.get() == "Audio Only":
                    opts['format'] = 'bestaudio/best'
                    opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]

                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])

                self.log("✅ Download Completed Successfully!")
                messagebox.showinfo("Success", "Download finished!")
            except Exception as e:
                self.log(f"❌ Error: {e}")
            finally:
                self.dl_btn.config(state="normal")

        threading.Thread(target=download_thread, daemon=True).start()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%')
            speed = d.get('_speed_str', '')
            self.log(f"Downloading... {percent} {speed}")

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
