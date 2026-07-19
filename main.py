import os
import re
import subprocess
import json
import logging
import threading
import tempfile
import shutil
import time
import tkinter as tk
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import filedialog, messagebox

# إعدادات الواجهة (OLED Dark Mode + Neon Accents)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# إعداد نظام السجلات الاحترافي (Logging)
log_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = logging.FileHandler("phoenix_muxer.log", encoding='utf-8')
file_handler.setFormatter(log_formatter)

logger = logging.getLogger("PhoenixLogger")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

class PhoenixSubsMuxerFixer(TkinterDnD.Tk):
    def safe_after(self, ms, func):
        try:
            self.after(ms, func)
        except Exception:
            pass

    def __init__(self):
        super().__init__()

        self.title("Phoenix Subs Muxer - Ultimate Edition")
        self.geometry("900x860")
        self.resizable(False, False)
        # Professional Dark Tool Background
        self.configure(bg="#0A0A0B") 
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.tools_dir = os.path.join(self.base_dir, "tools")
        self.ffmpeg_path = os.path.join(self.tools_dir, "ffmpeg.exe")
        self.ffprobe_path = os.path.join(self.tools_dir, "ffprobe.exe")
        
        self.folder_queue = []
        self.tools_ready = False
        self.is_processing = False
        self.cancel_requested = False
        self.theme_mode = "dark"
        self.last_browse_dir = os.path.expanduser("~")
        
        self.setup_ui()
        self.load_settings()
        self.check_local_tools()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # Decorative top border
        top_border = ctk.CTkFrame(self, height=3, fg_color="#b4092c", corner_radius=0)
        top_border.pack(fill="x", padx=0, pady=0)

        # --- Main Frame ---
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=(10, 15))

        # --- Header ---
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 8))

        title_stack = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_stack.pack(side="left")
        
        title_label = ctk.CTkLabel(
            title_stack, 
            text="PHOENIX MUXER", 
            font=ctk.CTkFont(family="Consolas", size=30, weight="bold"),
            text_color="#b4092c"
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_stack,
            text="SUBTITLE STANDARDIZER & MUXER v2.0",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#3a3a3e"
        )
        subtitle_label.pack(anchor="w", pady=(0, 0))
        
        self.status_badge = ctk.CTkLabel(
            header_frame, text="[ STANDBY ]", font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color="#3a3a3e", fg_color="transparent", corner_radius=0, padx=10, pady=5
        )
        self.status_badge.pack(side="right", pady=5)

        self.theme_btn = ctk.CTkButton(
            header_frame, text="☀", width=36, height=36, corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=18),
            fg_color="transparent", hover_color="#1a1a1e", border_width=1, border_color="#2a2a2e",
            command=self.toggle_theme
        )
        self.theme_btn.pack(side="right", padx=(0, 10))

        # Horizontal divider below header
        header_divider = ctk.CTkFrame(main_frame, height=1, fg_color="#1e1e22")
        header_divider.pack(fill="x", pady=(0, 10))

        # --- Settings Card ---
        settings_frame = ctk.CTkFrame(main_frame, fg_color="#0e0e12", corner_radius=6, border_width=1, border_color="#1e1e26")
        settings_frame.pack(fill="x", ipadx=15, ipady=8, pady=(0, 6))
        
        ctk.CTkLabel(settings_frame, text="// DISPLAY RESOLUTION", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#b4092c").pack(anchor="w", pady=(0, 6))

        separator = ctk.CTkFrame(settings_frame, height=1, fg_color="#1e1e26")
        separator.pack(fill="x", pady=(0, 8))

        res_inner = ctk.CTkFrame(settings_frame, fg_color="transparent")
        res_inner.pack(fill="x", pady=(2, 0))

        ctk.CTkLabel(res_inner, text="PlayResX:", font=ctk.CTkFont(family="Consolas", size=12), text_color="#888890").grid(row=0, column=0, padx=(0, 10))
        self.res_x_entry = ctk.CTkEntry(res_inner, width=100, justify="center", font=ctk.CTkFont(family="Consolas", weight="bold"), fg_color="#06060a", border_color="#b4092c", border_width=1, text_color="#e0e0e0", corner_radius=4)
        self.res_x_entry.insert(0, "1920")
        self.res_x_entry.grid(row=0, column=1, padx=(0, 40))

        ctk.CTkLabel(res_inner, text="PlayResY:", font=ctk.CTkFont(family="Consolas", size=12), text_color="#888890").grid(row=0, column=2, padx=(0, 10))
        self.res_y_entry = ctk.CTkEntry(res_inner, width=100, justify="center", font=ctk.CTkFont(family="Consolas", weight="bold"), fg_color="#06060a", border_color="#b4092c", border_width=1, text_color="#e0e0e0", corner_radius=4)
        self.res_y_entry.insert(0, "1080")
        self.res_y_entry.grid(row=0, column=3)

        # --- Queue Card ---
        queue_frame = ctk.CTkFrame(main_frame, fg_color="#0e0e12", corner_radius=6, border_width=1, border_color="#1e1e26")
        queue_frame.pack(fill="both", expand=True, ipadx=15, ipady=12, pady=(0, 6))

        queue_header = ctk.CTkFrame(queue_frame, fg_color="transparent")
        queue_header.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(queue_header, text="// BATCH QUEUE", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#b4092c").pack(side="left")
        
        self.add_folder_btn = ctk.CTkButton(
            queue_header, text="+ ADD ANIME FOLDER", width=140, height=30,
            font=ctk.CTkFont(family="Consolas", size=12), fg_color="transparent", hover_color="#1a1a1e", text_color="#c0c0c8", border_width=1, border_color="#2a2a2e", corner_radius=4,
            command=self.add_folder_to_queue
        )
        self.add_folder_btn.pack(side="right")

        self.clear_queue_btn = ctk.CTkButton(
            queue_header, text="✕ CLEAR ALL", width=110, height=30,
            font=ctk.CTkFont(family="Consolas", size=12), fg_color="transparent", hover_color="#1a1a1e", text_color="#c0c0c8", border_width=1, border_color="#2a2a2e", corner_radius=4,
            command=self.clear_queue
        )
        self.clear_queue_btn.pack(side="right", padx=(0, 10))

        queue_separator = ctk.CTkFrame(queue_frame, height=1, fg_color="#1e1e26")
        queue_separator.pack(fill="x", pady=(5, 10))

        self.queue_listbox = ctk.CTkScrollableFrame(queue_frame, height=120, fg_color="#06060a", border_color="#1e1e26", border_width=1)
        self.queue_listbox.pack(fill="x")
        
        self.queue_listbox.drop_target_register(DND_FILES)
        self.queue_listbox.dnd_bind('<<Drop>>', self.on_drop)

        self.queue_hint_label = ctk.CTkLabel(
            self.queue_listbox, text="_ drop or add folders to queue", 
            font=ctk.CTkFont(family="Consolas", size=11), text_color="#2a2a2e"
        )
        self.queue_hint_label.pack(pady=40)

        # --- Action & Logs ---
        action_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_frame.pack(fill="x", pady=(8, 0))

        button_row = ctk.CTkFrame(action_frame, fg_color="transparent")
        button_row.pack(fill="x", pady=(0, 6))

        self.process_btn = ctk.CTkButton(
            button_row, text="INITIALIZE BATCH PROCESS", 
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"), height=48, corner_radius=4,
            fg_color="#0e0e12", hover_color="#8a0720", text_color="#2a2a2e", border_width=1, border_color="#1e1e26", state="disabled",
            command=self.start_processing_thread
        )
        self.process_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        def _cancel_command():
            self.cancel_requested = True
            self.cancel_btn.configure(state="disabled", text_color="#2a2a2e", border_color="#1e1e26")

        self.cancel_btn = ctk.CTkButton(
            button_row, text="[ CANCEL ]", width=120, height=48, corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            fg_color="transparent", hover_color="#1a0408", text_color="#b4092c", border_width=1, border_color="#b4092c", state="disabled",
            command=_cancel_command
        )
        self.cancel_btn.configure(text_color="#2a2a2e", border_color="#1e1e26") # Initially disabled state
        self.cancel_btn.pack(side="right")

        self.progress_label = ctk.CTkLabel(
            action_frame, text="", 
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#888890"
        )
        self.progress_label.pack(pady=(0, 3))

        self.eta_label = ctk.CTkLabel(
            action_frame, text="",
            font=ctk.CTkFont(family="Consolas", size=12), text_color="#b4092c"
        )
        self.eta_label.pack(pady=(0, 3))

        def _open_last_output():
            if hasattr(self, 'last_output_dir') and os.path.exists(self.last_output_dir):
                os.startfile(self.last_output_dir)

        self.open_output_btn = ctk.CTkButton(
            action_frame, text="[ OPEN OUTPUT FOLDER ]", height=32, corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=12), 
            fg_color="transparent", hover_color="#1a1a1e", text_color="#b4092c", border_width=1, border_color="#2a0810",
            command=_open_last_output
        )
        self.open_output_btn.pack_forget()

        ctk.CTkLabel(action_frame, text="// SYSTEM LOG", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#b4092c").pack(anchor="w", pady=(6, 3))

        self.log_box = ctk.CTkTextbox(action_frame, height=230, fg_color="#06060a", text_color="#606068", font=ctk.CTkFont(family="Consolas", size=11), border_color="#1e1e26", border_width=1)
        self.log_box.pack(fill="x", pady=0)

    def log(self, message, level="INFO"):
        def _append_log():
            self.log_box.insert("end", f"[{level}] {message}\n")
            self.log_box.see("end")
        self.after(0, _append_log)
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)

    def load_settings(self):
        config_path = os.path.join(self.base_dir, "config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if "playres_x" in data:
                    self.res_x_entry.delete(0, 'end')
                    self.res_x_entry.insert(0, str(data["playres_x"]))
                if "playres_y" in data:
                    self.res_y_entry.delete(0, 'end')
                    self.res_y_entry.insert(0, str(data["playres_y"]))
                if "theme_mode" in data:
                    self.theme_mode = data["theme_mode"]
                    ctk.set_appearance_mode(self.theme_mode)
                    if self.theme_mode == "light":
                        if hasattr(self, 'theme_btn'):
                            self.theme_btn.configure(text="🌙")
        except Exception:
            pass

    def on_closing(self):
        config_path = os.path.join(self.base_dir, "config.json")
        try:
            data = {
                "playres_x": self.res_x_entry.get().strip() or "1920",
                "playres_y": self.res_y_entry.get().strip() or "1080",
                "theme_mode": self.theme_mode
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass
        self.destroy()

    def toggle_theme(self):
        if self.theme_mode == "dark":
            ctk.set_appearance_mode("light")
            self.theme_mode = "light"
            self.theme_btn.configure(text="🌙")
        else:
            ctk.set_appearance_mode("dark")
            self.theme_mode = "dark"
            self.theme_btn.configure(text="☀")

    def check_local_tools(self):
        if os.path.exists(self.ffmpeg_path) and os.path.exists(self.ffprobe_path):
            self.tools_ready = True
            self.log("System tools validated successfully.", "INFO")
        else:
            self.tools_ready = False
            self.log("CRITICAL: FFmpeg toolkit not found in /tools directory.", "ERROR")
            messagebox.showerror("Error", "FFmpeg tools missing from the tools directory.")

    def on_drop(self, event):
        if self.is_processing:
            return
        if not self.tools_ready:
            self.log("Cannot add folders. Tools are missing.", "WARNING")
            return
            
        paths = self.tk.splitlist(event.data)
        added_any = False
        
        for path in paths:
            if not os.path.isdir(path):
                continue
                
            if path in self.folder_queue:
                self.log(f"Folder already in queue: {os.path.basename(path)}", "WARNING")
                continue
                
            subs_path = os.path.join(path, "subs")
            if not os.path.exists(subs_path):
                self.log(f"Rejected {os.path.basename(path)}: Missing 'subs' directory.", "ERROR")
                continue
                
            self.folder_queue.append(path)
            self.log(f"Added to queue: {path}")
            
            vid_count = len([f for f in os.listdir(path) if f.endswith(('.mkv', '.mp4'))])
            sub_count = len([f for f in os.listdir(subs_path) if f.endswith('.ass')])
            folder_name = os.path.basename(path)
            
            self.log(f"Preview: Found {vid_count} video(s) and {sub_count} subtitle(s) in '{folder_name}'")
            if vid_count != sub_count:
                self.log(f"WARNING: Video/subtitle count mismatch — {vid_count} videos vs {sub_count} subtitles", "WARNING")
                
            added_any = True
            
        if added_any:
            self.update_queue_ui()
            self.process_btn.configure(state="normal")

    def pick_multiple_folders(self, callback=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Select Anime Folders")
        dialog.geometry("600x500")
        dialog.resizable(False, False)
        dialog.configure(fg_color="#0A0A0B")
        dialog.transient(self)

        ctk.CTkLabel(dialog, text="// SELECT FOLDERS — Hold CTRL or SHIFT to select multiple", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#b4092c").pack(pady=(15, 10))

        list_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        folder_listbox = tk.Listbox(
            list_frame, selectmode=tk.EXTENDED, bg="#06060a", fg="#c0c0c8",
            selectbackground="#b4092c", selectforeground="#ffffff", font=("Consolas", 11),
            borderwidth=0, highlightthickness=1, highlightcolor="#1e1e26", activestyle="none",
            yscrollcommand=scrollbar.set
        )
        folder_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=folder_listbox.yview)

        current_dirs = []

        def populate_list():
            folder_listbox.delete(0, tk.END)
            current_dirs.clear()
            if os.path.exists(self.last_browse_dir):
                try:
                    for d in sorted(os.listdir(self.last_browse_dir)):
                        full_path = os.path.join(self.last_browse_dir, d)
                        if os.path.isdir(full_path):
                            current_dirs.append(full_path)
                            folder_listbox.insert(tk.END, f"  {d}")
                except Exception:
                    pass

        populate_list()

        def browse_root():
            chosen = filedialog.askdirectory(title="Select Root Directory", initialdir=self.last_browse_dir)
            if chosen:
                self.last_browse_dir = chosen
                populate_list()

        def confirm():
            indices = folder_listbox.curselection()
            paths = [current_dirs[idx] for idx in indices]
            dialog.destroy()
            if callback:
                callback(paths)

        def cancel():
            dialog.destroy()
            if callback:
                callback([])

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(btn_row, text="[ BROWSE LOCATION ]", font=ctk.CTkFont(family="Consolas", size=12), fg_color="transparent", hover_color="#1a1a1e", text_color="#c0c0c8", border_width=1, border_color="#2a2a2e", corner_radius=4, command=browse_root).pack(side="left")
        ctk.CTkButton(btn_row, text="[ CANCEL ]", width=100, font=ctk.CTkFont(family="Consolas", size=12), fg_color="transparent", hover_color="#1a1a1e", text_color="#c0c0c8", border_width=1, border_color="#2a2a2e", corner_radius=4, command=cancel).pack(side="right")
        ctk.CTkButton(btn_row, text="[ CONFIRM ]", width=100, font=ctk.CTkFont(family="Consolas", size=12), fg_color="transparent", hover_color="#1a1a1e", text_color="#c0c0c8", border_width=1, border_color="#2a2a2e", corner_radius=4, command=confirm).pack(side="right", padx=(0, 10))

    def add_folder_to_queue(self):
        if not self.tools_ready:
            self.log("Cannot add folders. Tools are missing.", "WARNING")
            return
        self.pick_multiple_folders(callback=self._on_folders_selected)

    def _on_folders_selected(self, folders):
        if not folders:
            return
        added_any = False
        for folder in folders:
            if folder in self.folder_queue:
                self.log(f"Folder already in queue: {os.path.basename(folder)}", "WARNING")
            else:
                subs_path = os.path.join(folder, "subs")
                if not os.path.exists(subs_path):
                    self.log(f"Rejected {os.path.basename(folder)}: Missing 'subs' directory.", "ERROR")
                else:
                    self.folder_queue.append(folder)
                    self.log(f"Added to queue: {folder}")
                    vid_count = len([f for f in os.listdir(folder) if f.endswith(('.mkv', '.mp4'))])
                    sub_count = len([f for f in os.listdir(subs_path) if f.endswith('.ass')])
                    folder_name = os.path.basename(folder)
                    self.log(f"Preview: Found {vid_count} video(s) and {sub_count} subtitle(s) in '{folder_name}'")
                    if vid_count != sub_count:
                        self.log(f"WARNING: Video/subtitle count mismatch — {vid_count} videos vs {sub_count} subtitles", "WARNING")
                    added_any = True
        if added_any:
            self.update_queue_ui()
            self.process_btn.configure(state="normal", fg_color="#b4092c", text_color="#ffffff", border_width=0)

    def update_queue_ui(self):
        def _update():
            for widget in self.queue_listbox.winfo_children():
                if widget != getattr(self, 'queue_hint_label', None):
                    widget.destroy()
            
            if len(self.folder_queue) == 0:
                if hasattr(self, 'queue_hint_label'):
                    self.queue_hint_label.pack(pady=40)
            else:
                if hasattr(self, 'queue_hint_label'):
                    self.queue_hint_label.pack_forget()
                
            for i, folder in enumerate(self.folder_queue):
                row = ctk.CTkFrame(self.queue_listbox, fg_color="#0e0e12", corner_radius=4, border_width=1, border_color="#1e1e26")
                row.pack(fill="x", pady=2, padx=2)
                
                ctk.CTkLabel(row, text=f"{i+1}. {os.path.basename(folder)}", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#c0c0c8").pack(side="left", padx=10, pady=5)
                
                remove_btn = ctk.CTkButton(row, text="[X]", width=30, height=24, font=ctk.CTkFont(family="Consolas", size=11), fg_color="transparent", hover_color="#2a0810", text_color="#b4092c", border_width=1, border_color="#2a0810", command=lambda f=folder: self.remove_from_queue(f))
                remove_btn.pack(side="right", padx=10)
        self.after(0, _update)

    def remove_from_queue(self, folder):
        if self.is_processing:
            return
        self.folder_queue.remove(folder)
        self.update_queue_ui()
        if not self.folder_queue:
            self.process_btn.configure(state="disabled", fg_color="#0e0e12", text_color="#2a2a2e", border_width=1, border_color="#1e1e26")
        self.log(f"Removed from queue: {os.path.basename(folder)}")

    def clear_queue(self):
        if self.is_processing:
            return
        self.folder_queue.clear()
        self.update_queue_ui()
        self.process_btn.configure(state="disabled", fg_color="#0e0e12", text_color="#2a2a2e", border_width=1, border_color="#1e1e26")

    def extract_episode_number(self, filename):
        name = os.path.splitext(filename)[0]
        # Strip known quality/codec tags to avoid false matches
        name = re.sub(
            r'\b(1080p|720p|2160p|4k|x265|x264|10bit|HEVC|BluRay|WEBRip|HDR)\b',
            '', name, flags=re.IGNORECASE
        )

        # Priority 1: Explicit episode markers — E01, EP01, Episode 01
        match = re.search(r'\b(?:E|EP|Episode)\s*0*(\d{1,4})\b', name, re.IGNORECASE)
        if match:
            return str(int(match.group(1)))  # normalize: remove leading zeros

        # Priority 2: "- 01" pattern common in fansub naming (not preceded by digit)
        match = re.search(r'(?<!\d)-\s*0*(\d{1,4})(?!\d)', name)
        if match:
            return str(int(match.group(1)))

        # Priority 3: Bracketed episode number at end of name e.g. [01]
        match = re.search(r'\[0*(\d{1,4})\]\s*$', name)
        if match:
            return str(int(match.group(1)))

        # NO blind fallback — avoids grabbing numbers from title (e.g. "9004-tai")
        return None

    def get_best_audio_stream(self, video_path):
        cmd = [self.ffprobe_path, '-v', 'error', '-show_entries', 'stream=index,codec_type,channels:stream_tags=language', '-of', 'json', video_path]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            data = json.loads(result.stdout)
            
            audio_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
            if not audio_streams: return None

            jp_streams = []
            for stream in audio_streams:
                lang = stream.get('tags', {}).get('language', '').lower()
                if lang in ['jpn', 'ja', 'japanese']:
                    jp_streams.append(stream)
                    
            if not jp_streams:
                return None
                
            for stream in jp_streams:
                if stream.get('channels', 0) == 2:
                    return {
                        'index': stream['index'], 
                        'language': stream.get('tags', {}).get('language', ''), 
                        'channels': 2
                    }
                    
            fallback = jp_streams[0]
            return {
                'index': fallback['index'], 
                'language': fallback.get('tags', {}).get('language', ''), 
                'channels': fallback.get('channels', 0)
            }
        except Exception as e:
            self.log(f"Audio probe failed: {e}", "ERROR")
            return None

    def get_video_duration(self, video_path):
        cmd = [
            self.ffprobe_path, '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            video_path
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return float(result.stdout.strip())
        except Exception as e:
            self.log(f"Failed to extract exact video duration: {e}", "ERROR")
            return None

    def clean_competitor_names(self, line):
        replacements = {
            r"http://www\.crunchyroll\.com/[^\s\]]*": "http://www.anime-phoenix.com/",
            r"http://www\.aegisub\.org/[^\s\]]*": "http://www.anime-phoenix.com/",
            r"cr_ar": "Anime Phoenix",
            r"Crunchyroll": "Anime Phoenix",
            r"AnimeSanka\.com": "Anime-Phoenix.com",
            r"AnimeSanka": "Anime Phoenix",
            r"Anime Time": "Anime Phoenix",
            r"Moozzi2": "Anime Phoenix"
        }
        for pattern, replacement in replacements.items():
            line = re.sub(pattern, replacement, line, flags=re.IGNORECASE)
        return line

    def standardize_ass_file(self, filepath, res_x, res_y, vid_duration=None):
        try:
            lines = None
            for enc in ['utf-8-sig', 'cp1256', 'latin-1']:
                try:
                    with open(filepath, 'r', encoding=enc) as f:
                        lines = f.readlines()
                    if enc != 'utf-8-sig':
                        self.log(f"WARNING: File '{os.path.basename(filepath)}' is not UTF-8, read using {enc}", "WARNING")
                    break
                except UnicodeDecodeError:
                    continue

            new_lines = []
            current_section = None
            required_header = [
                "[Script Info]\n", "; Script generated by anime phoenix\n", "; http://www.anime-phoenix.com/\n",
                "Title: Anime Phoenix Subtitles\n", "ScriptType: v4.00+\n", "PlayDepth: 0\n",
                "ScaledBorderAndShadow: Yes\n", f"PlayResX: {res_x}\n", f"PlayResY: {res_y}\n"
            ]

            for line in lines:
                stripped = line.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    current_section = stripped
                    if current_section == "[Script Info]":
                        new_lines.extend(required_header)
                        continue 

                if current_section == "[Script Info]":
                    if any(stripped.lower().startswith(x) for x in [";", "title:", "scripttype:", "playdepth:", "scaledborderandshadow:", "playresx:", "playresy:"]):
                        continue
                    elif stripped != "":
                        new_lines.append(self.clean_competitor_names(line))
                elif current_section == "[Aegisub Project Garbage]":
                    new_lines.append(self.clean_competitor_names(line))
                elif current_section == "[V4+ Styles]":
                    if line.startswith("Style:"):
                        parts = line.split(',')
                        if len(parts) >= 8:
                            style_name = parts[0].replace("Style:", "").strip().lower()
                            font_name = parts[1].strip()
                            if style_name == "default" or font_name == "Bahij Greta Arabic":
                                parts[7] = "-1"
                        line = ",".join(parts)
                    new_lines.append(line)
                else:
                    new_lines.append(line)

            # --- الخوارزمية الخاصة بإعدام وقص التوقيتات الوهمية ---
            time_pattern = re.compile(r'(\d+):(\d+):(\d+)\.(\d+)')
            
            def time_to_seconds(h, m, s, cs):
                return int(h)*3600 + int(m)*60 + int(s) + int(cs)/100.0
            
            def seconds_to_ass_time(seconds):
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                s = int(seconds % 60)
                cs = int(round((seconds % 1) * 100))
                return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

            final_lines = []
            for line in new_lines:
                if line.startswith("Dialogue:") and vid_duration:
                    parts = line.split(",", 9)
                    if len(parts) >= 9:
                        end_time_str = parts[2].strip()
                        end_match = time_pattern.match(end_time_str)
                        if end_match:
                            h, m, s, cs = end_match.groups()
                            end_sec = time_to_seconds(h, m, s, cs)
                            
                            if end_sec > (vid_duration + 5): # قص أي توقيت يعبر الفيديو
                                end_sec = vid_duration
                                parts[2] = seconds_to_ass_time(end_sec)
                                line = ",".join(parts)
                final_lines.append(line)

            fd, temp_path = tempfile.mkstemp(suffix=".ass", text=True)
            with os.fdopen(fd, 'w', encoding='utf-8-sig') as f:
                f.writelines(final_lines)
            return temp_path
        except Exception as e:
            self.log(f"Subtitle sanitation failed for {os.path.basename(filepath)}: {e}", "ERROR")
            return None

    def normalize_ep(self, ep_str):
        """Normalize episode string: strip leading zeros for fair comparison."""
        try:
            return str(int(ep_str))
        except (ValueError, TypeError):
            return ep_str

    def find_matching_sub(self, vid_ep, sub_files):
        """
        Two-pass subtitle matcher.
        Pass 1: exact normalized episode number match.
        Pass 2: zero-padding tolerant integer match.
        Returns matched filename string or None.
        """
        norm_vid = self.normalize_ep(vid_ep)

        # Pass 1: exact match after normalization
        exact = [s for s in sub_files if self.normalize_ep(self.extract_episode_number(s)) == norm_vid]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            self.log(f"Multiple subtitle matches for episode {vid_ep}, using first: {exact[0]}", "WARNING")
            return exact[0]

        # Pass 2: integer comparison (handles "1" vs "01" edge cases)
        try:
            vid_ep_int = int(norm_vid)
            int_matches = []
            for s in sub_files:
                ep = self.extract_episode_number(s)
                try:
                    if int(ep) == vid_ep_int:
                        int_matches.append(s)
                except (ValueError, TypeError):
                    pass
            if len(int_matches) == 1:
                return int_matches[0]
            if len(int_matches) > 1:
                self.log(f"Multiple integer matches for episode {vid_ep}, using first: {int_matches[0]}", "WARNING")
                return int_matches[0]
        except (ValueError, TypeError):
            pass

        return None

    def start_processing_thread(self):
        if not self.folder_queue: return
        self.is_processing = True
        self.cancel_requested = False
        self.process_btn.configure(state="disabled", fg_color="#1a0408", text_color="#b4092c", border_width=1, border_color="#b4092c", text="// PROCESSING...")
        self.add_folder_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal", text_color="#b4092c", border_color="#b4092c")
        self.status_badge.configure(text="[ ACTIVE ]", text_color="#b4092c", fg_color="transparent")
        if hasattr(self, 'open_output_btn'):
            self.open_output_btn.pack_forget()
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        def _finalize_ui():
            self.is_processing = False
            self.process_btn.configure(state="disabled", fg_color="#b4092c", text_color="#ffffff", border_width=0, text="INITIALIZE BATCH PROCESS")
            self.add_folder_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled", text_color="#2a2a2e", border_color="#1e1e26")
            self.status_badge.configure(text="[ STANDBY ]", text_color="#3a3a3e", fg_color="transparent")
            self.progress_label.configure(text="")
            self.eta_label.configure(text="")
            if hasattr(self, 'last_output_dir') and self.last_output_dir:
                self.open_output_btn.pack(fill="x", pady=(5, 0))

        res_x = self.res_x_entry.get().strip()
        res_y = self.res_y_entry.get().strip()

        if not (res_x and res_y and res_x.isdigit() and res_y.isdigit()):
            def _show_err():
                messagebox.showerror("Validation Error", "Invalid resolution values. PlayResX and PlayResY must be positive integers.")
            self.safe_after(0, _show_err)
            self.safe_after(0, _finalize_ui)
            return

        count_attempted = 0
        count_succeeded = 0
        count_no_sub = 0
        count_no_audio = 0
        count_ffmpeg_err = 0

        for folder in list(self.folder_queue):
            if self.cancel_requested:
                break
            self.log(f"--- STARTING BATCH: {os.path.basename(folder)} ---", "INFO")
            subs_folder = os.path.join(folder, "subs")
            output_dir = os.path.join(folder, "Phoenix_Output")
            self.last_output_dir = output_dir
            os.makedirs(output_dir, exist_ok=True)

            video_files = [f for f in os.listdir(folder) if f.endswith(('.mkv', '.mp4'))]
            
            total_size = sum(os.path.getsize(os.path.join(folder, f)) for f in video_files)
            required_space = total_size * 1.1
            free_space = shutil.disk_usage(output_dir).free
            
            if free_space < required_space:
                req_gb = required_space / (1024**3)
                free_gb = free_space / (1024**3)
                self.log(f"Skipping batch {os.path.basename(folder)}: Insufficient disk space. Required: {req_gb:.2f} GB, Available: {free_gb:.2f} GB", "ERROR")
                
                def _remove_skipped(f=folder):
                    if f in self.folder_queue:
                        self.folder_queue.remove(f)
                        self.update_queue_ui()
                self.safe_after(0, _remove_skipped)
                continue
            
            def sort_key(f):
                ep = self.extract_episode_number(f)
                if ep is not None:
                    try:
                        return (0, float(ep))
                    except ValueError:
                        return (1, ep)
                return (2, f)
                
            video_files.sort(key=sort_key)
            
            sub_files = [f for f in os.listdir(subs_folder) if f.endswith('.ass')]

            total_episodes = len(video_files)
            processed_count = 0
            
            self._batch_start_time = time.time()
            
            def _init_progress(t=total_episodes):
                self.progress_label.configure(text=f"Processing: 0 / {t}")
                self.eta_label.configure(text="")
            self.safe_after(0, _init_progress)

            for video in video_files:
                try:
                    vid_path = os.path.join(folder, video)
                    out_path = os.path.join(output_dir, video)

                    if self.cancel_requested:
                        self.log("CANCELLED by user.", "WARNING")
                        break

                    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000000:
                        self.log(f"Skipping Ep: {video} (Already exists in Output - Resume active)", "WARNING")
                        continue

                    vid_ep = self.extract_episode_number(video)
                    if not vid_ep:
                        self.log(f"Failed to extract episode number from {video}", "ERROR")
                        continue
                        
                    count_attempted += 1

                    matched_sub = self.find_matching_sub(vid_ep, sub_files)
                    if not matched_sub:
                        self.log(f"Skipping Ep {vid_ep}: No matching subtitle found in 'subs' folder.", "ERROR")
                        count_no_sub += 1
                        continue

                    self.log(f"Processing Ep {vid_ep}: Video='{video}', Subtitle='{matched_sub}'")
                    sub_path = os.path.join(subs_folder, matched_sub)

                    # 1. سحب مدة الفيديو
                    vid_duration = self.get_video_duration(vid_path)

                    # 2. فرمتة وتأمين التوقيتات داخل الترجمة
                    temp_sub_path = self.standardize_ass_file(sub_path, res_x, res_y, vid_duration)
                    if not temp_sub_path:
                        continue

                    # 3. سحب الصوت الياباني
                    best_audio = self.get_best_audio_stream(vid_path)
                    if not best_audio:
                        self.log(f"Skipping Ep {vid_ep}: No Japanese audio track found.", "ERROR")
                        count_no_audio += 1
                        if os.path.exists(temp_sub_path):
                            os.remove(temp_sub_path)
                        continue
                    
                    self.log(f"Selected Audio - Index: {best_audio['index']}, Lang: {best_audio['language']}, Channels: {best_audio['channels']}")

                    # 4. بناء أمر الدمج
                    ffmpeg_cmd = [
                        self.ffmpeg_path, '-y', 
                        '-i', vid_path, 
                        '-i', temp_sub_path,
                        '-map', '0:v:0',
                        '-map', f"0:{best_audio['index']}",
                        '-map', '1:0',
                        '-c:v', 'copy', 
                        '-c:a', 'copy', 
                        '-c:s', 'copy',
                        '-metadata:s:0', 'language=ara',
                        '-metadata:s:0', 'title=Anime Phoenix Subtitles',
                        '-disposition:s:0', 'default'
                    ]
                    
                    if vid_duration:
                        ffmpeg_cmd.extend(['-t', str(vid_duration)])
                        
                    ffmpeg_cmd.append(out_path)

                    ffmpeg_error_output = ""
                    try:
                        proc = subprocess.Popen(
                            ffmpeg_cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        # Poll so we can honour cancel_requested mid-encode
                        while proc.poll() is None:
                            if self.cancel_requested:
                                proc.terminate()
                                self.log(f"FFmpeg process terminated by user for Ep {vid_ep}.", "WARNING")
                                break
                            time.sleep(0.5)

                        _, stderr_output = proc.communicate(timeout=10)
                        ffmpeg_error_output = stderr_output or ""

                        if self.cancel_requested:
                            pass  # handled above
                        elif proc.returncode != 0:
                            self.log(f"FFmpeg muxing failed for Ep {vid_ep}.", "ERROR")
                            count_ffmpeg_err += 1
                            if ffmpeg_error_output:
                                last_lines = "\n".join(ffmpeg_error_output.strip().split('\n')[-5:])
                                self.log(f"FFmpeg Error Details:\n{last_lines}", "ERROR")
                        else:
                            self.log(f"SUCCESS: Ep {vid_ep} completed.")
                            count_succeeded += 1

                    except Exception as e:
                        self.log(f"Unexpected error during FFmpeg for Ep {vid_ep}: {e}", "ERROR")
                        count_ffmpeg_err += 1
                    finally:
                        if os.path.exists(temp_sub_path):
                            try:
                                os.remove(temp_sub_path)
                            except OSError as e:
                                self.log(f"Failed to remove temp file {temp_sub_path}: {e}", "WARNING")
                        if self.cancel_requested and os.path.exists(out_path):
                            try:
                                os.remove(out_path)
                            except OSError:
                                pass
                finally:
                    processed_count += 1
                    
                    elapsed = time.time() - self._batch_start_time
                    avg_per_ep = elapsed / processed_count
                    remaining = avg_per_ep * (total_episodes - processed_count)
                    
                    if processed_count == total_episodes:
                        eta_text = "// ETA: Done"
                    else:
                        m, s = divmod(int(remaining), 60)
                        eta_text = f"// ETA: {m}m {s}s"
                        
                    def _update_progress(c=processed_count, t=total_episodes, eta=eta_text):
                        self.progress_label.configure(text=f"// PROCESSING: {c} / {t}")
                        self.eta_label.configure(text=eta)
                    self.safe_after(0, _update_progress)
            
            self.log(f"--- COMPLETED BATCH: {os.path.basename(folder)} ---", "INFO")
            
            def _remove_folder_and_update(f=folder):
                if f in self.folder_queue:
                    self.folder_queue.remove(f)
                    self.update_queue_ui()
                    
            self.safe_after(0, _remove_folder_and_update)

        self.log("ALL QUEUES PROCESSED SUCCESSFULLY.", "INFO")
        
        summary_msg = (
            "══ BATCH SUMMARY ══\n"
            f"Attempted : {count_attempted}\n"
            f"Succeeded : {count_succeeded}\n"
            f"No Subtitle : {count_no_sub}\n"
            f"No JPN Stereo : {count_no_audio}\n"
            f"FFmpeg Error : {count_ffmpeg_err}\n"
            "══════════════════"
        )
        self.log(summary_msg, "INFO")
        
        self.safe_after(0, _finalize_ui)

if __name__ == "__main__":
    app = PhoenixSubsMuxerFixer()
    app.mainloop()