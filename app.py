#!/usr/bin/env python3
"""
YouTube Downloader Desktop v4 - Professional Version
"""

import subprocess, sys, os

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

for pkg, imp in [("yt-dlp", "yt_dlp"), ("static-ffmpeg", "static_ffmpeg"), ("pillow", "PIL")]:
    try: __import__(imp)
    except: 
        print(f"Installing {pkg}...")
        install(pkg)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, json, hashlib, datetime, shutil
import yt_dlp, static_ffmpeg, requests
from PIL import Image, ImageTk
import io

static_ffmpeg.add_paths()

# ===================== CONFIG =====================
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

# ===================== MAIN APP =====================
class YouTubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader")
        self.geometry("900x680")
        self.configure(bg="#0b0b0b")
        self.minsize(850, 620)

        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.current_user = {"name": "User", "email": "user@example.com", "method": "email"}

        self.build_ui()

    def build_ui(self):
        # Header
        header = tk.Frame(self, bg="#111111", height=68)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="YouTube Downloader", font=("Syne", 18, "bold"), 
                 bg="#111111", fg="#e63232").pack(side="left", padx=25, pady=18)

        # Profile Button (Clickable)
        profile = tk.Frame(header, bg="#111111", cursor="hand2")
        profile.pack(side="right", padx=25)
        profile.bind("<Button-1>", lambda e: self.show_settings())

        tk.Label(profile, text=self.current_user["name"], bg="#111111", fg="white", 
                 font=("bold", 12)).pack(anchor="e")
        tk.Label(profile, text=self.current_user["email"], bg="#111111", fg="#888", 
                 font=("", 9)).pack(anchor="e")

        # Tabs
        tab_frame = tk.Frame(self, bg="#111111")
        tab_frame.pack(fill="x")
        
        self.tabs = {}
        for text, page in [("⬇ Download", "download"), ("🕘 History", "history"), ("⚙ Settings", "settings")]:
            btn = tk.Label(tab_frame, text=text, bg="#111111", fg="#aaa", font=("bold", 11),
                           padx=20, pady=12, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, p=page: self.switch_tab(p))
            self.tabs[page] = btn

        # Pages
        self.pages = {}
        for p in ["download", "history", "settings"]:
            frame = tk.Frame(self, bg="#0b0b0b")
            self.pages[p] = frame

        self.switch_tab("download")

    def switch_tab(self, page):
        for p in self.pages.values():
            p.pack_forget()
        self.pages[page].pack(fill="both", expand=True, padx=25, pady=15)

        for btn in self.tabs.values():
            btn.config(fg="#aaa")
        self.tabs[page].config(fg="#e63232")

        if page == "history":
            self.load_history()

    # ===================== DOWNLOAD PAGE =====================
        download_page = self.pages["download"]
        tk.Label(download_page, text="YouTube URL", bg="#0b0b0b", fg="#ccc", font=("bold", 11)).pack(anchor="w")
        
        self.url_var = tk.StringVar()
        tk.Entry(download_page, textvariable=self.url_var, font=("DM Mono", 11), bg="#1f1f1f", fg="white", 
                 relief="flat", bd=0).pack(fill="x", ipady=12, pady=(6,15))

        # Options Frame
        opt = tk.Frame(download_page, bg="#0b0b0b")
        opt.pack(fill="x", pady=10)

        self.mode_var = tk.StringVar(value="Video")
        self.qual_var = tk.StringVar(value="Best (Max Quality)")
        self.format_var = tk.StringVar(value="mp4")

        for label, var, options in [
            ("Mode", self.mode_var, ["Video", "Audio Only"]),
            ("Quality", self.qual_var, ["Best (Max Quality)", "1080p", "720p", "480p"]),
            ("Format", self.format_var, ["mp4", "mp3"])
        ]:
            f = tk.Frame(opt, bg="#0b0b0b")
            f.pack(side="left", padx=15)
            tk.Label(f, text=label, bg="#0b0b0b", fg="#888").pack(anchor="w")
            ttk.OptionMenu(f, var, options[0], *options).pack()

        # Download Button (Tiny & Nice)
        self.dl_btn = tk.Button(download_page, text="⬇ DOWNLOAD NOW", font=("bold", 14), 
                                bg="#e63232", fg="white", height=2, command=self.start_download)
        self.dl_btn.pack(fill="x", pady=25)

        self.log_text = tk.Text(download_page, bg="#111111", fg="#0f0", font=("DM Mono", 10), height=12)
        self.log_text.pack(fill="both", expand=True)

    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Error", "Please enter URL")
            return

        self.dl_btn.config(state="disabled")
        self.log_text.delete(1.0, tk.END)
        self.log("▶ Starting download...")

        def run():
            try:
                opts = {
                    'outtmpl': os.path.join(self.save_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.log_progress],
                }
                if self.mode_var.get() == "Audio Only":
                    opts['format'] = 'bestaudio/best'
                    opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]

                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                self.log("✅ Download Completed Successfully!")
            except Exception as e:
                self.log(f"❌ Error: {e}")
            finally:
                self.dl_btn.config(state="normal")

        threading.Thread(target=run, daemon=True).start()

    def log(self, text):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def log_progress(self, d):
        if d['status'] == 'downloading':
            self.log(f"Downloading... {d.get('_percent_str', '')} {d.get('_speed_str', '')}")

    # ===================== HISTORY PAGE =====================
    def load_history(self):
        # Will be implemented fully later if needed
        pass

    # ===================== SETTINGS PAGE =====================
    def show_settings(self):
        settings_win = tk.Toplevel(self)
        settings_win.title("Account & Settings")
        settings_win.geometry("500x600")
        settings_win.configure(bg="#0b0b0b")

        tk.Label(settings_win, text="Account", font=("bold", 14), bg="#0b0b0b", fg="white").pack(pady=15)

        tk.Label(settings_win, text=f"Name: {self.current_user['name']}", bg="#0b0b0b", fg="#ccc").pack(anchor="w", padx=30)
        tk.Label(settings_win, text=f"Email: {self.current_user['email']}", bg="#0b0b0b", fg="#ccc").pack(anchor="w", padx=30)

        tk.Button(settings_win, text="Change Save Folder", command=self.change_save_folder, 
                  bg="#333", fg="white").pack(pady=20, fill="x", padx=30)

        tk.Button(settings_win, text="🔄 Update yt-dlp to Latest", command=self.update_ytdlp,
                  bg="#e63232", fg="white").pack(pady=10, fill="x", padx=30)

        tk.Button(settings_win, text="Sign Out", command=lambda: self.destroy(), 
                  bg="#444", fg="white").pack(pady=30, fill="x", padx=30)

    def change_save_folder(self):
        folder = filedialog.askdirectory(initialdir=self.save_path)
        if folder:
            self.save_path = folder
            messagebox.showinfo("Success", f"Save folder changed to:\n{folder}")

    def update_ytdlp(self):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp", "-q"])
            messagebox.showinfo("Success", "yt-dlp updated successfully!")
        except:
            messagebox.showerror("Error", "Failed to update yt-dlp")

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
