#!/usr/bin/env python3
"""
YouTube Downloader · Premium v4 (Updated)
"""

import subprocess, sys, os

def _pip(pkg):
    subprocess.check_call([sys.executable,"-m","pip","install",pkg,"-q"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

for _p,_i in [("yt-dlp","yt_dlp"),("static-ffmpeg","static_ffmpeg")]:
    try: __import__(_i)
    except: print(f"  Installing {_p}…"); _pip(_p)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, re, json, hashlib, datetime, time
import yt_dlp, static_ffmpeg, shutil, requests

static_ffmpeg.add_paths()
FFMPEG = shutil.which("ffmpeg") or ""

APP_DIR   = os.path.join(os.path.expanduser("~"), ".ytdl_app")
ACCS_FILE = os.path.join(APP_DIR, "accounts.json")
HIST_FILE = os.path.join(APP_DIR, "history.json")
SESS_FILE = os.path.join(APP_DIR, "session.json")
os.makedirs(APP_DIR, exist_ok=True)

# ... (keep all your helper functions: jload, jsave, hashpw, colors, btn, card, etc.)

# Updated History Row with Thumbnail
def _hist_row(self, item):
    row = tk.Frame(self._hinn, bg=C["card"], highlightbackground=C["bdr"], highlightthickness=1)
    row.pack(fill="x", pady=(0,6))

    # Thumbnail
    thumb_url = item.get("thumbnail")
    if thumb_url:
        try:
            img_data = requests.get(thumb_url, timeout=5).content
            from PIL import Image, ImageTk
            img = Image.open(io.BytesIO(img_data)).resize((120, 68))
            photo = ImageTk.PhotoImage(img)
            thumb_lbl = tk.Label(row, image=photo, bg=C["card"])
            thumb_lbl.image = photo
            thumb_lbl.pack(side="left", padx=(12,8), pady=8)
        except:
            pass

    # Status dot + Info
    dot_color = C["grn"] if item.get("status")=="done" else C["red"]
    dk = tk.Canvas(row, width=8, height=8, bg=C["card"], highlightthickness=0)
    dk.pack(side="left", padx=(0,8))
    dk.create_oval(0,0,8,8, fill=dot_color, outline="")

    info = tk.Frame(row, bg=C["card"])
    info.pack(side="left", fill="x", expand=True, pady=9)

    title = (item.get("title") or item.get("url","?"))[:60]
    tk.Label(info, text=title, font=FB, bg=C["card"], fg=C["fg"], anchor="w").pack(fill="x")

    meta = "  ·  ".join(p for p in [
        item.get("mode",""), item.get("quality",""),
        item.get("format","").upper(), item.get("date","")
    ] if p)
    tk.Label(info, text=meta, font=FS, bg=C["card"], fg=C["fg3"], anchor="w").pack(fill="x")

    # Re-download button
    u = item.get("url","")
    btn(row, "↺ Download Again", 
        lambda url=u: (self.url_v.set(url), self._tab("download")),
        side="right", px=16, py=10)

# In _build_opts() add thumbnail saving
# Inside _dl() after successful download:
self._hist.append({
    "user":self._email,
    "url":url,
    "title":title,
    "thumbnail": info.get("thumbnail") if 'info' in locals() else None,  # add this
    ...
})
