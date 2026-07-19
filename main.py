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
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading as _threading

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

        self.title("Phoenix Muxer v3.1 — Multi-Tool Edition")
        self.geometry("1020x980")
        self.resizable(True, True)
        self.minsize(900, 800)
        self.configure(bg="#050508") 
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.tools_dir = os.path.join(self.base_dir, "tools")
        self.ffmpeg_path = os.path.join(self.tools_dir, "ffmpeg.exe")
        self.ffprobe_path = os.path.join(self.tools_dir, "ffprobe.exe")
        
        self.folder_queue = []
        self.standalone_subs_queue = []
        
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
        # A. TOP ACCENT BAR
        top_accent_1 = ctk.CTkFrame(self, height=2, fg_color="#c0092e", corner_radius=0)
        top_accent_1.pack(fill="x", padx=0, pady=0)
        top_accent_2 = ctk.CTkFrame(self, height=1, fg_color="#00d4ff", corner_radius=0)
        top_accent_2.pack(fill="x", padx=0, pady=0)

        # Main Frame
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=(15, 15))

        # B. HEADER ROW
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        header_left = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_left.pack(side="left")

        title_label = ctk.CTkLabel(
            header_left,
            text="PHOENIX MUXER",
            font=ctk.CTkFont(family="Consolas", size=32, weight="bold"),
            text_color="#c0092e"
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            header_left,
            text="BATCH MUXER & SUBTITLE STANDARDIZER  v3.1",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color="#00d4ff"
        )
        subtitle_label.pack(anchor="w", pady=(0, 5))

        stat_row = ctk.CTkFrame(header_left, fg_color="transparent")
        stat_row.pack(anchor="w")

        self.stat_attempted = ctk.CTkLabel(stat_row, text="▸ ATTEMPTED: 0", font=ctk.CTkFont(family="Consolas", size=9), text_color="#3a3a4e")
        self.stat_attempted.pack(side="left", padx=(0, 15))
        
        self.stat_success = ctk.CTkLabel(stat_row, text="▸ SUCCESS: 0", font=ctk.CTkFont(family="Consolas", size=9), text_color="#3a3a4e")
        self.stat_success.pack(side="left", padx=(0, 15))
        
        self.stat_failed = ctk.CTkLabel(stat_row, text="▸ FAILED: 0", font=ctk.CTkFont(family="Consolas", size=9), text_color="#3a3a4e")
        self.stat_failed.pack(side="left")

        header_right = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_right.pack(side="right", anchor="n")

        self.status_badge = ctk.CTkLabel(
            header_right, text="◈ STANDBY", font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color="#2a2a3e"
        )
        self.status_badge.pack(side="left", padx=(0, 15))

        self.theme_btn = ctk.CTkButton(
            header_right, text="☀", width=36, height=36, corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=18),
            fg_color="transparent", hover_color="#1a1a2e", border_width=1, border_color="#2a2a3e",
            command=self.toggle_theme
        )
        self.theme_btn.pack(side="left", padx=(0, 15))

        # C. THIN DIVIDER
        divider = ctk.CTkFrame(main_frame, height=1, fg_color="#0e0e18")
        divider.pack(fill="x", pady=(0, 15))

        # --- GLOBAL SETTINGS CARD ---
        settings_frame = ctk.CTkFrame(main_frame, fg_color="#080810", corner_radius=8, border_width=1, border_color="#131320")
        settings_frame.pack(fill="x", ipadx=15, ipady=10, pady=(0, 10))

        ctk.CTkLabel(
            settings_frame, text="⟨ GLOBAL CONFIGURATION ⟩", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#00d4ff"
        ).pack(anchor="w", pady=(0, 8))

        res_inner = ctk.CTkFrame(settings_frame, fg_color="transparent")
        res_inner.pack(fill="x")

        ctk.CTkLabel(res_inner, text="PlayResX:", font=ctk.CTkFont(family="Consolas", size=12), text_color="#888890").grid(row=0, column=0, padx=(0, 8))
        self.res_x_entry = ctk.CTkEntry(res_inner, width=90, justify="center", font=ctk.CTkFont(family="Consolas", weight="bold"), fg_color="#06060a", border_color="#c0092e", border_width=1, text_color="#e0e0e0", corner_radius=4)
        self.res_x_entry.insert(0, "1920")
        self.res_x_entry.grid(row=0, column=1, padx=(0, 10))

        ctk.CTkLabel(res_inner, text="×", font=ctk.CTkFont(family="Consolas", size=12), text_color="#3a3a4e").grid(row=0, column=2, padx=(0, 10))

        ctk.CTkLabel(res_inner, text="PlayResY:", font=ctk.CTkFont(family="Consolas", size=12), text_color="#888890").grid(row=0, column=3, padx=(0, 8))
        self.res_y_entry = ctk.CTkEntry(res_inner, width=90, justify="center", font=ctk.CTkFont(family="Consolas", weight="bold"), fg_color="#06060a", border_color="#c0092e", border_width=1, text_color="#e0e0e0", corner_radius=4)
        self.res_y_entry.insert(0, "1080")
        self.res_y_entry.grid(row=0, column=4, padx=(0, 15))

        v_sep = ctk.CTkFrame(res_inner, width=1, fg_color="#131320")
        v_sep.grid(row=0, column=5, sticky="ns", padx=(0, 15))

        ctk.CTkLabel(res_inner, text="RAW REGEX (advanced):", font=ctk.CTkFont(family="Consolas", size=12), text_color="#888890").grid(row=0, column=6, padx=(0, 8))
        
        pattern_frame = ctk.CTkFrame(res_inner, fg_color="transparent")
        pattern_frame.grid(row=0, column=7, sticky="w")
        
        self.pattern_entry = ctk.CTkEntry(pattern_frame, width=260, justify="left", font=ctk.CTkFont(family="Consolas", size=11), fg_color="#06060a", border_color="#00d4ff", border_width=1, text_color="#e0e0e0", corner_radius=4, placeholder_text="Custom regex e.g.: (?:EP?)(\d{1,4})")
        self.pattern_entry.pack(anchor="w")
        
        ctk.CTkLabel(pattern_frame, text="Custom episode regex — group 1 must capture the number", font=ctk.CTkFont(family="Consolas", size=9), text_color="#2a2a3e").pack(anchor="w", pady=(2, 0))


        # --- TABS CONTAINER ---
        self.tabview = ctk.CTkTabview(
            main_frame, fg_color="#03030a", border_color="#131320", border_width=1,
            text_color="#c0c0d0", segmented_button_fg_color="#080810", 
            segmented_button_selected_color="#1a1a2e", segmented_button_selected_hover_color="#1a1a2e",
            segmented_button_unselected_color="#050508", segmented_button_unselected_hover_color="#0a0a14"
        )
        self.tabview.pack(fill="both", expand=True, pady=(0, 10))
        
        tab_muxer = self.tabview.add("BATCH MUXER")
        tab_subs = self.tabview.add("SUBTITLE STANDARDIZER")


        # ==========================================
        # TAB 1: BATCH MUXER
        # ==========================================
        queue_frame = ctk.CTkFrame(tab_muxer, fg_color="transparent")
        queue_frame.pack(fill="both", expand=True, padx=5, pady=5)

        queue_header = ctk.CTkFrame(queue_frame, fg_color="transparent")
        queue_header.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(queue_header, text="⟨ MUXER FOLDER QUEUE ⟩", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#00d4ff").pack(side="left")
        
        queue_buttons = ctk.CTkFrame(queue_header, fg_color="transparent")
        queue_buttons.pack(side="right")

        ctk.CTkLabel(queue_buttons, text="TEMPLATE ({ep_number} placeholder):", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#00d4ff").pack(side="left", padx=(0, 8))

        template_frame = ctk.CTkFrame(queue_buttons, fg_color="transparent")
        template_frame.pack(side="left", padx=(0, 15))

        self.ep_template_entry = ctk.CTkEntry(
            template_frame, width=220, justify="left", 
            font=ctk.CTkFont(family="Consolas", size=11), fg_color="#06060a", 
            border_color="#00d4ff", border_width=1, text_color="#e0e0e0", 
            corner_radius=4, placeholder_text="e.g. _-_{ep_number}  or  E{ep_number}"
        )
        self.ep_template_entry.pack(anchor="w")

        ctk.CTkLabel(
            template_frame, text="Use {ep_number} as placeholder — last match wins", 
            font=ctk.CTkFont(family="Consolas", size=9), text_color="#2a2a3e"
        ).pack(anchor="w", pady=(2, 0))

        self.preview_btn = ctk.CTkButton(
            queue_buttons, text="◈ PREVIEW MATCHES", height=28,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), fg_color="transparent", hover_color="#0a1a20", text_color="#00d4ff", border_width=1, border_color="#00d4ff", corner_radius=4,
            command=self.show_preview_window
        )
        self.preview_btn.pack(side="left", padx=(0, 8))

        self.add_folder_btn = ctk.CTkButton(
            queue_buttons, text="+ FOLDER", height=28, width=80,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), fg_color="transparent", hover_color="#1a1a2e", text_color="#c0c0d0", border_width=1, border_color="#2a2a3e", corner_radius=4,
            command=self.add_folder_to_queue
        )
        self.add_folder_btn.pack(side="left", padx=(0, 8))

        self.clear_queue_btn = ctk.CTkButton(
            queue_buttons, text="✕ CLEAR", height=28, width=80,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), fg_color="transparent", hover_color="#1a1a2e", text_color="#c0c0d0", border_width=1, border_color="#2a2a3e", corner_radius=4,
            command=self.clear_queue
        )
        self.clear_queue_btn.pack(side="left")

        queue_separator = ctk.CTkFrame(queue_frame, height=1, fg_color="#131320")
        queue_separator.pack(fill="x", pady=(0, 8))

        self.queue_listbox = ctk.CTkScrollableFrame(queue_frame, height=100, fg_color="#03030a", border_color="#131320", border_width=1)
        self.queue_listbox.pack(fill="both", expand=True)
        
        self.queue_listbox.drop_target_register(DND_FILES)
        self.queue_listbox.dnd_bind('<<Drop>>', self.on_drop_muxer)

        self.queue_hint_label = ctk.CTkLabel(
            self.queue_listbox, text="⟶  drop folders here or click + FOLDER", 
            font=ctk.CTkFont(family="Consolas", size=11), text_color="#1a1a2e"
        )
        self.queue_hint_label.pack(pady=30)

        action_row = ctk.CTkFrame(tab_muxer, fg_color="transparent")
        action_row.pack(fill="x", pady=(10, 0))

        self.process_btn = ctk.CTkButton(
            action_row, text="⟩ INITIALIZE BATCH MUXING", 
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"), height=52, corner_radius=6,
            fg_color="#080810", hover_color="#8a0720", text_color="#1e1e2e", border_width=1, border_color="#131320", state="disabled",
            command=self.start_processing_thread
        )
        self.process_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        def _cancel_command():
            self.cancel_requested = True
            self.cancel_btn.configure(state="disabled", text_color="#1e1e2e", border_color="#131320")

        self.cancel_btn = ctk.CTkButton(
            action_row, text="[ ABORT ]", width=130, height=52, corner_radius=6,
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            fg_color="transparent", hover_color="#1a0408", text_color="#1e1e2e", border_width=1, border_color="#131320", state="disabled",
            command=_cancel_command
        )
        self.cancel_btn.pack(side="right")


        # ==========================================
        # TAB 2: SUBTITLE STANDARDIZER
        # ==========================================
        subs_frame = ctk.CTkFrame(tab_subs, fg_color="transparent")
        subs_frame.pack(fill="both", expand=True, padx=5, pady=5)

        subs_header = ctk.CTkFrame(subs_frame, fg_color="transparent")
        subs_header.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(subs_header, text="⟨ TARGET .ASS FILES ⟩", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#00d4ff").pack(side="left")
        
        subs_buttons = ctk.CTkFrame(subs_header, fg_color="transparent")
        subs_buttons.pack(side="right")

        self.add_subs_btn = ctk.CTkButton(
            subs_buttons, text="+ ADD .ASS FILES", height=28,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), fg_color="transparent", hover_color="#1a1a2e", text_color="#c0c0d0", border_width=1, border_color="#2a2a3e", corner_radius=4,
            command=self.add_standalone_subs
        )
        self.add_subs_btn.pack(side="left", padx=(0, 8))

        self.clear_subs_btn = ctk.CTkButton(
            subs_buttons, text="✕ CLEAR", height=28, width=80,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), fg_color="transparent", hover_color="#1a1a2e", text_color="#c0c0d0", border_width=1, border_color="#2a2a3e", corner_radius=4,
            command=self.clear_standalone_subs
        )
        self.clear_subs_btn.pack(side="left")

        subs_separator = ctk.CTkFrame(subs_frame, height=1, fg_color="#131320")
        subs_separator.pack(fill="x", pady=(0, 8))

        self.subs_listbox = ctk.CTkScrollableFrame(subs_frame, height=100, fg_color="#03030a", border_color="#131320", border_width=1)
        self.subs_listbox.pack(fill="both", expand=True)
        
        self.subs_listbox.drop_target_register(DND_FILES)
        self.subs_listbox.dnd_bind('<<Drop>>', self.on_drop_subs)

        self.subs_hint_label = ctk.CTkLabel(
            self.subs_listbox, text="⟶  drop .ass files here or click + ADD .ASS FILES", 
            font=ctk.CTkFont(family="Consolas", size=11), text_color="#1a1a2e"
        )
        self.subs_hint_label.pack(pady=30)

        subs_action_row = ctk.CTkFrame(tab_subs, fg_color="transparent")
        subs_action_row.pack(fill="x", pady=(10, 0))

        self.process_subs_btn = ctk.CTkButton(
            subs_action_row, text="⟩ STANDARDIZE SUBTITLES IN-PLACE", 
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"), height=52, corner_radius=6,
            fg_color="#080810", hover_color="#8a0720", text_color="#1e1e2e", border_width=1, border_color="#131320", state="disabled",
            command=self.start_standardizer_thread
        )
        self.process_subs_btn.pack(side="left", fill="x", expand=True)


        # --- PROGRESS SECTION (GLOBAL) ---
        progress_frame = ctk.CTkFrame(main_frame, fg_color="#080810", corner_radius=6, border_width=1, border_color="#131320")
        progress_frame.pack(fill="x", pady=(0, 10), ipadx=10, ipady=8)

        progress_top = ctk.CTkFrame(progress_frame, fg_color="transparent")
        progress_top.pack(fill="x", padx=5, pady=(0, 5))

        self.progress_label = ctk.CTkLabel(
            progress_top, text="◈ IDLE", 
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#2a2a3e"
        )
        self.progress_label.pack(side="left")

        self.eta_label = ctk.CTkLabel(
            progress_top, text="",
            font=ctk.CTkFont(family="Consolas", size=11), text_color="#00d4ff"
        )
        self.eta_label.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame, height=14, corner_radius=4,
            fg_color="#0a0a14", progress_color="#c0092e",
            border_width=1, border_color="#1a1a2e"
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=5, pady=(0, 5))

        self.speed_label = ctk.CTkLabel(
            progress_frame, text="",
            font=ctk.CTkFont(family="Consolas", size=10), text_color="#3a3a4e"
        )
        self.speed_label.pack()

        def _open_last_output():
            if hasattr(self, 'last_output_dir') and os.path.exists(self.last_output_dir):
                os.startfile(self.last_output_dir)

        self.open_output_btn = ctk.CTkButton(
            main_frame, text="[ OPEN OUTPUT ]", height=32, corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=12), 
            fg_color="transparent", hover_color="#1a1a1e", text_color="#c0092e", border_width=1, border_color="#2a0810",
            command=_open_last_output
        )
        self.open_output_btn.pack_forget()

        # --- LOG SECTION (GLOBAL) ---
        log_header = ctk.CTkFrame(main_frame, fg_color="transparent")
        log_header.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(log_header, text="⟨ SYSTEM LOG ⟩", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#00d4ff").pack(anchor="w")

        self.log_box = ctk.CTkTextbox(main_frame, height=150, fg_color="#03030a", text_color="#4a6070", font=ctk.CTkFont(family="Consolas", size=11), border_color="#131320", border_width=1)
        self.log_box.pack(fill="x", pady=0)

    def log(self, message, level="INFO"):
        color_map = {
            "INFO":    "#4a6070",
            "WARNING": "#c08000",
            "ERROR":   "#c0092e",
            "SUCCESS": "#00a050",
        }
        def _append_log():
            tag = level
            color = color_map.get(level, "#4a6070")
            try:
                self.log_box.tag_config(tag, foreground=color)
            except Exception:
                pass
            self.log_box.insert("end", f"[{level}] {message}\n", tag)
            self.log_box.see("end")
        self.safe_after(0, _append_log)
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
                if "custom_pattern" in data:
                    if hasattr(self, 'pattern_entry'):
                        self.pattern_entry.delete(0, 'end')
                        self.pattern_entry.insert(0, data["custom_pattern"])
                if "ep_template" in data:
                    if hasattr(self, 'ep_template_entry'):
                        self.ep_template_entry.delete(0, 'end')
                        self.ep_template_entry.insert(0, data["ep_template"])
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
                "theme_mode": self.theme_mode,
                "custom_pattern": self.pattern_entry.get().strip() if hasattr(self, 'pattern_entry') else "",
                "ep_template": self.ep_template_entry.get().strip() if hasattr(self, 'ep_template_entry') else "",
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

    # =======================================================
    # MUXER TAB QUEUE LOGIC
    # =======================================================
    def on_drop_muxer(self, event):
        if self.is_processing: return
        if not self.tools_ready:
            self.log("Cannot add folders. Tools are missing.", "WARNING")
            return
            
        paths = self.tk.splitlist(event.data)
        added_any = False
        
        for path in paths:
            if not os.path.isdir(path): continue
            if path in self.folder_queue:
                self.log(f"Folder already in queue: {os.path.basename(path)}", "WARNING")
                continue
                
            subs_path = os.path.join(path, "subs")
            if not os.path.exists(subs_path):
                self.log(f"Rejected {os.path.basename(path)}: Missing 'subs' directory.", "ERROR")
                continue
                
            self.folder_queue.append(path)
            self.log(f"Added to Muxer queue: {path}")
            
            vid_count = len([f for f in os.listdir(path) if f.endswith(('.mkv', '.mp4'))])
            sub_count = len([f for f in os.listdir(subs_path) if f.endswith('.ass')])
            if vid_count != sub_count:
                self.log(f"WARNING: Video/subtitle count mismatch — {vid_count} vs {sub_count}", "WARNING")
            added_any = True
            
        if added_any:
            self.update_queue_ui()
            self.process_btn.configure(state="normal", fg_color="#c0092e", text_color="#ffffff", border_width=0)

    def add_folder_to_queue(self):
        if not self.tools_ready:
            self.log("Cannot add folders. Tools are missing.", "WARNING")
            return
        self.pick_multiple_folders(callback=self._on_folders_selected)

    def _on_folders_selected(self, folders):
        if not folders: return
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
                    added_any = True
        if added_any:
            self.update_queue_ui()
            self.process_btn.configure(state="normal", fg_color="#c0092e", text_color="#ffffff", border_width=0)

    def update_queue_ui(self):
        def _update():
            for widget in self.queue_listbox.winfo_children():
                if widget != getattr(self, 'queue_hint_label', None):
                    widget.destroy()
            
            if len(self.folder_queue) == 0:
                if hasattr(self, 'queue_hint_label'): self.queue_hint_label.pack(pady=40)
            else:
                if hasattr(self, 'queue_hint_label'): self.queue_hint_label.pack_forget()
                
            for i, folder in enumerate(self.folder_queue):
                row = ctk.CTkFrame(self.queue_listbox, fg_color="#0e0e12", corner_radius=4, border_width=1, border_color="#1e1e26")
                row.pack(fill="x", pady=2, padx=2)
                ctk.CTkLabel(row, text=f"{i+1}. {os.path.basename(folder)}", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#c0c0c8").pack(side="left", padx=10, pady=5)
                remove_btn = ctk.CTkButton(row, text="[X]", width=30, height=24, font=ctk.CTkFont(family="Consolas", size=11), fg_color="transparent", hover_color="#2a0810", text_color="#b4092c", border_width=1, border_color="#2a0810", command=lambda f=folder: self.remove_from_queue(f))
                remove_btn.pack(side="right", padx=10)
        self.safe_after(0, _update)

    def remove_from_queue(self, folder):
        if self.is_processing: return
        self.folder_queue.remove(folder)
        self.update_queue_ui()
        if not self.folder_queue:
            self.process_btn.configure(state="disabled", fg_color="#080810", text_color="#1e1e2e", border_width=1, border_color="#131320")

    def clear_queue(self):
        if self.is_processing: return
        self.folder_queue.clear()
        self.update_queue_ui()
        self.process_btn.configure(state="disabled", fg_color="#080810", text_color="#1e1e2e", border_width=1, border_color="#131320")

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
                except Exception: pass
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
            if callback: callback(paths)
        def cancel():
            dialog.destroy()
            if callback: callback([])

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkButton(btn_row, text="[ BROWSE LOCATION ]", font=ctk.CTkFont(family="Consolas", size=12), fg_color="transparent", hover_color="#1a1a1e", text_color="#c0c0c8", border_width=1, border_color="#2a2a2e", corner_radius=4, command=browse_root).pack(side="left")
        ctk.CTkButton(btn_row, text="[ CANCEL ]", width=100, font=ctk.CTkFont(family="Consolas", size=12), fg_color="transparent", hover_color="#1a1a1e", text_color="#c0c0c8", border_width=1, border_color="#2a2a2e", corner_radius=4, command=cancel).pack(side="right")
        ctk.CTkButton(btn_row, text="[ CONFIRM ]", width=100, font=ctk.CTkFont(family="Consolas", size=12), fg_color="transparent", hover_color="#1a1a1e", text_color="#c0c0c8", border_width=1, border_color="#2a2a2e", corner_radius=4, command=confirm).pack(side="right", padx=(0, 10))

    # =======================================================
    # SUBTITLE STANDARDIZER TAB QUEUE LOGIC
    # =======================================================
    def on_drop_subs(self, event):
        if self.is_processing: return
        paths = self.tk.splitlist(event.data)
        self._add_subs_to_queue(paths)

    def add_standalone_subs(self):
        if self.is_processing: return
        paths = filedialog.askopenfilenames(
            title="Select .ass Subtitle Files",
            filetypes=[("ASS Subtitles", "*.ass")],
            initialdir=self.last_browse_dir
        )
        if paths:
            self.last_browse_dir = os.path.dirname(paths[0])
            self._add_subs_to_queue(paths)

    def _add_subs_to_queue(self, paths):
        added_any = False
        for p in paths:
            if not p.lower().endswith('.ass'): continue
            if p not in self.standalone_subs_queue:
                self.standalone_subs_queue.append(p)
                added_any = True
        if added_any:
            self.update_subs_ui()
            self.process_subs_btn.configure(state="normal", fg_color="#c0092e", text_color="#ffffff", border_width=0)

    def update_subs_ui(self):
        def _update():
            for widget in self.subs_listbox.winfo_children():
                if widget != getattr(self, 'subs_hint_label', None):
                    widget.destroy()
            
            if len(self.standalone_subs_queue) == 0:
                if hasattr(self, 'subs_hint_label'): self.subs_hint_label.pack(pady=30)
            else:
                if hasattr(self, 'subs_hint_label'): self.subs_hint_label.pack_forget()
                
            for i, sub in enumerate(self.standalone_subs_queue):
                row = ctk.CTkFrame(self.subs_listbox, fg_color="#0e0e12", corner_radius=4, border_width=1, border_color="#1e1e26")
                row.pack(fill="x", pady=2, padx=2)
                ctk.CTkLabel(row, text=f"{i+1}. {os.path.basename(sub)}", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#c0c0c8").pack(side="left", padx=10, pady=5)
                remove_btn = ctk.CTkButton(row, text="[X]", width=30, height=24, font=ctk.CTkFont(family="Consolas", size=11), fg_color="transparent", hover_color="#2a0810", text_color="#b4092c", border_width=1, border_color="#2a0810", command=lambda f=sub: self.remove_from_subs(f))
                remove_btn.pack(side="right", padx=10)
        self.safe_after(0, _update)

    def remove_from_subs(self, sub):
        if self.is_processing: return
        self.standalone_subs_queue.remove(sub)
        self.update_subs_ui()
        if not self.standalone_subs_queue:
            self.process_subs_btn.configure(state="disabled", fg_color="#080810", text_color="#1e1e2e", border_width=1, border_color="#131320")

    def clear_standalone_subs(self):
        if self.is_processing: return
        self.standalone_subs_queue.clear()
        self.update_subs_ui()
        self.process_subs_btn.configure(state="disabled", fg_color="#080810", text_color="#1e1e2e", border_width=1, border_color="#131320")

    # =======================================================
    # CORE LOGIC (REGEX & PARSING)
    # =======================================================
    def apply_template_pattern(self, template, name):
        if '{ep_number}' not in template:
            return None
        parts = template.split('{ep_number}')
        if len(parts) != 2:
            return None  # only one {ep_number} placeholder allowed
        prefix_literal, suffix_literal = parts
        pattern = re.escape(prefix_literal) + r'0*(\d{1,4})' + re.escape(suffix_literal)
        matches = re.findall(pattern, name, re.IGNORECASE)
        if matches:
            return str(int(matches[-1]))  # always prefer the LAST match
        return None

    def extract_episode_number(self, filename):
        name = os.path.splitext(filename)[0]
        name = re.sub(r'\b(1080p|720p|2160p|4k|x265|x264|10bit|HEVC|BluRay|WEBRip|HDR)\b', '', name, flags=re.IGNORECASE)
        
        # Pre-clean: strip standalone years (18xx, 19xx, 20xx) that are NOT episode numbers
        name = re.sub(r'(?i)(?<!\be)(?<!\bep)(?<!\bepisode)(?<!\be )(?<!\bep )(?<!\bepisode )\b(?:18|19|20)\d{2}\b', '', name)

        # Priority 0: user-defined template pattern
        if hasattr(self, 'ep_template_entry'):
            template = self.ep_template_entry.get().strip()
            if template and '{ep_number}' in template:
                result = self.apply_template_pattern(template, name)
                if result:
                    return result

        if hasattr(self, 'pattern_entry'):
            custom = self.pattern_entry.get().strip()
            if custom:
                try:
                    matches = list(re.finditer(custom, name, re.IGNORECASE))
                    valid = [m for m in matches if m.lastindex and m.lastindex >= 1]
                    if valid: return str(int(valid[-1].group(1)))
                except re.error: pass

        # Priority 1: Explicit episode markers
        match = re.search(r'\b(?:E|EP|Episode)\s*0*(\d{1,4})\b', name, re.IGNORECASE)
        if match: return str(int(match.group(1)))

        # Priority 2: "- 01" fansub pattern (take the LAST match)
        matches = re.findall(r'(?<!\d)-\s*0*(\d{1,4})(?!\d)', name)
        if matches: return str(int(matches[-1]))

        # Priority 3: Bracketed number at end
        match = re.search(r'\[0*(\d{1,4})\]\s*$', name)
        if match: return str(int(match.group(1)))

        return None

    def get_best_audio_stream(self, video_path):
        cmd = [self.ffprobe_path, '-v', 'error', '-show_entries', 'stream=index,codec_type,channels:stream_tags=language', '-of', 'json', video_path]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            data = json.loads(result.stdout)
            audio_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
            if not audio_streams: return None
            jp_streams = [s for s in audio_streams if s.get('tags', {}).get('language', '').lower() in ['jpn', 'ja', 'japanese']]
            if not jp_streams: return None
            for s in jp_streams:
                if s.get('channels', 0) == 2: return {'index': s['index'], 'language': s.get('tags', {}).get('language', ''), 'channels': 2}
            return {'index': jp_streams[0]['index'], 'language': jp_streams[0].get('tags', {}).get('language', ''), 'channels': jp_streams[0].get('channels', 0)}
        except Exception: return None

    def get_video_duration(self, video_path):
        cmd = [self.ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return float(result.stdout.strip())
        except Exception: return None

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

    def standardize_ass_file_lines(self, filepath, res_x, res_y, vid_duration=None):
        try:
            lines = None
            for enc in ['utf-8-sig', 'cp1256', 'latin-1']:
                try:
                    with open(filepath, 'r', encoding=enc) as f: lines = f.readlines()
                    break
                except UnicodeDecodeError: continue

            if lines is None: return None

            new_lines = []
            current_section = None
            required_header = [
                "[Script Info]\n", "; Script generated by anime phoenix\n", "; http://www.anime-phoenix.com/\n",
                "Title: subtitles\n", "ScriptType: v4.00+\n", "PlayDepth: 0\n",
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

            time_pattern = re.compile(r'(\d+):(\d+):(\d+)\.(\d+)')
            def time_to_seconds(h, m, s, cs): return int(h)*3600 + int(m)*60 + int(s) + int(cs)/100.0
            def seconds_to_ass_time(seconds): return f"{int(seconds // 3600)}:{int((seconds % 3600) // 60):02d}:{int(seconds % 60):02d}.{int(round((seconds % 1) * 100)):02d}"

            final_lines = []
            for line in new_lines:
                if line.startswith("Dialogue:") and vid_duration:
                    parts = line.split(",", 9)
                    if len(parts) >= 9:
                        end_match = time_pattern.match(parts[2].strip())
                        if end_match:
                            h, m, s, cs = end_match.groups()
                            end_sec = time_to_seconds(h, m, s, cs)
                            if end_sec > (vid_duration + 5):
                                parts[2] = seconds_to_ass_time(vid_duration)
                                line = ",".join(parts)
                final_lines.append(line)
            return final_lines
        except Exception as e:
            self.log(f"Subtitle sanitation failed for {os.path.basename(filepath)}: {e}", "ERROR")
            return None

    def standardize_ass_file(self, filepath, res_x, res_y, vid_duration=None):
        final_lines = self.standardize_ass_file_lines(filepath, res_x, res_y, vid_duration)
        if not final_lines: return None
        try:
            fd, temp_path = tempfile.mkstemp(suffix=".ass", text=True)
            with os.fdopen(fd, 'w', encoding='utf-8-sig') as f:
                f.writelines(final_lines)
            return temp_path
        except Exception: return None

    def standardize_ass_file_inplace(self, filepath, res_x, res_y):
        final_lines = self.standardize_ass_file_lines(filepath, res_x, res_y, vid_duration=None)
        if not final_lines: return False
        try:
            with open(filepath, 'w', encoding='utf-8-sig') as f:
                f.writelines(final_lines)
            return True
        except Exception as e:
            self.log(f"Failed to overwrite {os.path.basename(filepath)}: {e}", "ERROR")
            return False

    def normalize_ep(self, ep_str):
        try: return str(int(ep_str))
        except: return ep_str

    def find_matching_sub(self, vid_ep, sub_files):
        norm_vid = self.normalize_ep(vid_ep)
        exact = [s for s in sub_files if self.normalize_ep(self.extract_episode_number(s)) == norm_vid]
        if len(exact) >= 1: return exact[0]
        try:
            vid_ep_int = int(norm_vid)
            int_matches = [s for s in sub_files if self.extract_episode_number(s) and self.normalize_ep(self.extract_episode_number(s)).isdigit() and int(self.normalize_ep(self.extract_episode_number(s))) == vid_ep_int]
            if len(int_matches) >= 1: return int_matches[0]
        except: pass
        return None

    def verify_output_integrity(self, out_path, vid_ep):
        cmd = [self.ffprobe_path, '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'json', out_path]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
            data = json.loads(result.stdout)
            types = [s.get('codec_type') for s in data.get('streams', [])]
            missing = [x for x in ['video', 'audio', 'subtitle'] if x not in types]
            if missing: self.log(f"Integrity WARNING Ep {vid_ep}: Output missing streams: {', '.join(missing)}", "WARNING")
            else: self.log(f"Integrity OK Ep {vid_ep}: All streams verified.", "INFO")
        except Exception as e: self.log(f"Integrity check failed for Ep {vid_ep}: {e}", "WARNING")

    def show_preview_window(self):
        if self.is_processing: return
        if not self.folder_queue:
            self.log("Queue is empty — add folders first.", "WARNING")
            return

        preview = ctk.CTkToplevel(self)
        preview.title("Preview — Video ↔ Subtitle Matches")
        preview.geometry("860x560")
        preview.configure(fg_color="#050508")
        preview.transient(self)

        ctk.CTkLabel(preview, text="⟨ DRY-RUN PREVIEW — VIDEO ↔ SUBTITLE MATCH TABLE ⟩", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#00d4ff").pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(preview, text="No files are processed. This only shows how episodes will be paired.", font=ctk.CTkFont(family="Consolas", size=9), text_color="#2a2a3e").pack(anchor="w", padx=20, pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(preview, fg_color="#03030a", border_color="#131320", border_width=1)
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        header_row = ctk.CTkFrame(scroll, fg_color="#0a0a18", corner_radius=0)
        header_row.pack(fill="x", pady=(0, 2))
        for col_text, col_width in [("#", 40), ("FOLDER", 160), ("VIDEO FILE", 220), ("SUBTITLE FILE", 220), ("STATUS", 100)]:
            ctk.CTkLabel(header_row, text=col_text, width=col_width, font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#00d4ff", anchor="w").pack(side="left", padx=4, pady=4)

        row_num = 0
        for folder in self.folder_queue:
            subs_folder = os.path.join(folder, "subs")
            if not os.path.exists(subs_folder): continue
            video_files = sorted([f for f in os.listdir(folder) if f.endswith(('.mkv', '.mp4'))], key=lambda f: (self.extract_episode_number(f) or ""))
            sub_files = [f for f in os.listdir(subs_folder) if f.endswith('.ass')]
            folder_name = os.path.basename(folder)

            for video in video_files:
                row_num += 1
                vid_ep = self.extract_episode_number(video)
                matched_sub = self.find_matching_sub(vid_ep, sub_files) if vid_ep else None
                status = "✔ MATCHED" if matched_sub else "✘ NO SUB"
                status_color = "#00a050" if matched_sub else "#c0092e"
                row_bg = "#080810" if row_num % 2 == 0 else "#050508"

                data_row = ctk.CTkFrame(scroll, fg_color=row_bg, corner_radius=0)
                data_row.pack(fill="x", pady=1)

                for cell_text, col_width, color in [(str(row_num), 40, "#3a3a5e"), (folder_name[:22], 160, "#8080a0"), (video[:28], 220, "#c0c0d0"), ((matched_sub or "—")[:28], 220, "#8080a0"), (status, 100, status_color)]:
                    ctk.CTkLabel(data_row, text=cell_text, width=col_width, font=ctk.CTkFont(family="Consolas", size=10), text_color=color, anchor="w").pack(side="left", padx=4, pady=3)

        ctk.CTkButton(preview, text="[ CLOSE ]", height=32, corner_radius=4, font=ctk.CTkFont(family="Consolas", size=12), fg_color="transparent", hover_color="#0a0a14", text_color="#c0092e", border_width=1, border_color="#2a0810", command=preview.destroy).pack(pady=(0, 15))


    # =======================================================
    # SUBTITLE STANDARDIZER PROCESSING THREAD
    # =======================================================
    def start_standardizer_thread(self):
        if not self.standalone_subs_queue: return
        self.is_processing = True
        self.cancel_requested = False
        
        self.process_subs_btn.configure(state="disabled", fg_color="#080810", text_color="#1e1e2e", border_width=1, border_color="#131320", text="⟩ PROCESSING SUBTITLES...")
        self.add_subs_btn.configure(state="disabled")
        self.clear_subs_btn.configure(state="disabled")
        
        self.status_badge.configure(text="◈ ACTIVE", text_color="#00d4ff")
        self.progress_bar.set(0)
        self.progress_label.configure(text="◈ STANDARDIZING...")
        self.speed_label.configure(text="")
        
        threading.Thread(target=self.process_standardize_queue, daemon=True).start()

    def process_standardize_queue(self):
        def _finalize_ui():
            self.is_processing = False
            self.process_subs_btn.configure(state="normal", fg_color="#c0092e", text_color="#ffffff", border_width=0, text="⟩ STANDARDIZE SUBTITLES IN-PLACE")
            self.add_subs_btn.configure(state="normal")
            self.clear_subs_btn.configure(state="normal")
            self.status_badge.configure(text="◈ STANDBY", text_color="#2a2a3e")
            self.progress_bar.set(1.0)
            self.progress_label.configure(text="◈ SUBTITLE BATCH COMPLETE")
            self.speed_label.configure(text="")
            self.standalone_subs_queue.clear()
            self.update_subs_ui()
            self.safe_after(3000, lambda: self.progress_bar.set(0) or self.progress_label.configure(text="◈ IDLE"))

        res_x = self.res_x_entry.get().strip()
        res_y = self.res_y_entry.get().strip()
        if not (res_x and res_y and res_x.isdigit() and res_y.isdigit()):
            self.safe_after(0, lambda: messagebox.showerror("Validation Error", "Invalid resolution values."))
            self.safe_after(0, _finalize_ui)
            return

        total_files = len(self.standalone_subs_queue)
        success_count = 0
        failed_count = 0

        self.log(f"--- STARTING SUBTITLE STANDARDIZATION BATCH ({total_files} files) ---", "INFO")

        for i, filepath in enumerate(list(self.standalone_subs_queue)):
            if self.cancel_requested: break
            
            self.log(f"Standardizing: {os.path.basename(filepath)}")
            success = self.standardize_ass_file_inplace(filepath, res_x, res_y)
            if success:
                self.log(f"SUCCESS: {os.path.basename(filepath)}", "SUCCESS")
                success_count += 1
            else:
                failed_count += 1

            progress_val = (i + 1) / total_files
            self.safe_after(0, lambda pv=progress_val, c=i+1, t=total_files: (
                self.progress_bar.set(pv),
                self.progress_label.configure(text=f"◈ PROCESSING: {c} / {t}")
            ))

        self.log(f"--- COMPLETED SUBTITLE BATCH: {success_count} SUCCESS, {failed_count} FAILED ---", "INFO")
        self.safe_after(0, _finalize_ui)


    # =======================================================
    # BATCH MUXER PROCESSING THREAD
    # =======================================================
    def start_processing_thread(self):
        if not self.folder_queue: return
        self.is_processing = True
        self.cancel_requested = False
        self.process_btn.configure(state="disabled", fg_color="#080810", text_color="#1e1e2e", border_width=1, border_color="#131320", text="⟩ PROCESSING...")
        self.add_folder_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal", text_color="#c0092e", border_color="#c0092e")
        self.status_badge.configure(text="◈ ACTIVE", text_color="#00d4ff")
        self.progress_bar.set(0)
        self.progress_label.configure(text="◈ INITIALIZING...")
        self.speed_label.configure(text="")
        if hasattr(self, 'open_output_btn'):
            self.open_output_btn.pack_forget()
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        def _finalize_ui():
            self.is_processing = False
            self.process_btn.configure(state="normal", fg_color="#c0092e", text_color="#ffffff", border_width=0, text="⟩ INITIALIZE BATCH PROCESS")
            self.add_folder_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled", text_color="#1e1e2e", border_color="#131320")
            self.status_badge.configure(text="◈ STANDBY", text_color="#2a2a3e")
            self.progress_bar.set(1.0)
            self.progress_label.configure(text="◈ BATCH COMPLETE")
            self.speed_label.configure(text="")
            self.safe_after(3000, lambda: self.progress_bar.set(0) or self.progress_label.configure(text="◈ IDLE"))
            if hasattr(self, 'last_output_dir') and self.last_output_dir:
                self.open_output_btn.pack(fill="x", pady=(5, 0))

        res_x = self.res_x_entry.get().strip()
        res_y = self.res_y_entry.get().strip()

        if not (res_x and res_y and res_x.isdigit() and res_y.isdigit()):
            self.safe_after(0, lambda: messagebox.showerror("Validation Error", "Invalid resolution values."))
            self.safe_after(0, _finalize_ui)
            return

        count_attempted = 0
        count_succeeded = 0
        count_no_sub = 0
        count_no_audio = 0
        count_ffmpeg_err = 0

        for folder in list(self.folder_queue):
            if self.cancel_requested: break
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
                self.log(f"Skipping batch {os.path.basename(folder)}: Insufficient disk space.", "ERROR")
                self.safe_after(0, lambda f=folder: self.folder_queue.remove(f) if f in self.folder_queue else None)
                self.safe_after(0, self.update_queue_ui)
                continue
            
            video_files.sort(key=lambda f: (0, float(self.extract_episode_number(f))) if self.extract_episode_number(f) and self.extract_episode_number(f).replace('.','').isdigit() else (2, f))
            sub_files = [f for f in os.listdir(subs_folder) if f.endswith('.ass')]

            total_episodes = len(video_files)
            processed_count = 0
            self._batch_start_time = time.time()
            self.safe_after(0, lambda t=total_episodes: self.progress_label.configure(text=f"◈ PROCESSING: 0 / {t}"))

            MAX_WORKERS = 2
            ep_lock = _threading.Lock()

            def process_single_episode(video):
                nonlocal count_attempted, count_succeeded, count_no_sub, count_no_audio, count_ffmpeg_err, processed_count
                try:
                    vid_path = os.path.join(folder, video)
                    out_path = os.path.join(output_dir, video)
                    if self.cancel_requested: return
                    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000000:
                        self.log(f"Skipping Ep: {video} (Already exists — Resume active)", "WARNING")
                        return

                    vid_ep = self.extract_episode_number(video)
                    if not vid_ep: return
                    with ep_lock: count_attempted += 1

                    matched_sub = self.find_matching_sub(vid_ep, sub_files)
                    if not matched_sub:
                        self.log(f"Skipping Ep {vid_ep}: No matching subtitle found.", "ERROR")
                        with ep_lock: count_no_sub += 1
                        return

                    self.log(f"Processing Ep {vid_ep}: Video='{video}', Subtitle='{matched_sub}'")
                    vid_duration = self.get_video_duration(vid_path)
                    temp_sub_path = self.standardize_ass_file(os.path.join(subs_folder, matched_sub), res_x, res_y, vid_duration)
                    if not temp_sub_path: return

                    best_audio = self.get_best_audio_stream(vid_path)
                    if not best_audio:
                        self.log(f"Skipping Ep {vid_ep}: No Japanese audio track found.", "ERROR")
                        with ep_lock: count_no_audio += 1
                        if os.path.exists(temp_sub_path): os.remove(temp_sub_path)
                        return

                    ffmpeg_cmd = [
                        self.ffmpeg_path, '-y', '-i', vid_path, '-i', temp_sub_path,
                        '-map', '0:v:0', '-map', f"0:{best_audio['index']}", '-map', '1:0',
                        '-c:v', 'copy', '-c:a', 'copy', '-c:s', 'copy',
                        '-metadata:s:0', 'language=ara', '-metadata:s:0', 'title=Anime Phoenix Subtitles', '-disposition:s:0', 'default'
                    ]
                    if vid_duration: ffmpeg_cmd.extend(['-t', str(vid_duration)])
                    ffmpeg_cmd.append(out_path)

                    try:
                        proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
                        while proc.poll() is None:
                            if self.cancel_requested:
                                proc.terminate()
                                break
                            time.sleep(0.5)

                        _, stderr_out = proc.communicate(timeout=10)
                        if self.cancel_requested: pass
                        elif proc.returncode != 0:
                            self.log(f"FFmpeg failed for Ep {vid_ep}.", "ERROR")
                            with ep_lock: count_ffmpeg_err += 1
                        else:
                            self.verify_output_integrity(out_path, vid_ep)
                            self.log(f"SUCCESS: Ep {vid_ep} completed.", "SUCCESS")
                            with ep_lock: count_succeeded += 1
                    except Exception as e:
                        self.log(f"Unexpected FFmpeg error for Ep {vid_ep}: {e}", "ERROR")
                        with ep_lock: count_ffmpeg_err += 1
                    finally:
                        if os.path.exists(temp_sub_path):
                            try: os.remove(temp_sub_path)
                            except: pass
                        if self.cancel_requested and os.path.exists(out_path):
                            try: os.remove(out_path)
                            except: pass
                finally:
                    with ep_lock: processed_count += 1
                    elapsed = time.time() - self._batch_start_time
                    with ep_lock: _pc = processed_count
                    avg_per_ep = elapsed / max(_pc, 1)
                    remaining = avg_per_ep * (total_episodes - _pc)
                    epm = (60 / avg_per_ep) if avg_per_ep > 0 else 0
                    eta_text = "◈ DONE" if _pc >= total_episodes else f"ETA {int(remaining // 60)}m {int(remaining % 60)}s"
                    
                    self.safe_after(0, lambda c=_pc, t=total_episodes, eta=eta_text, pv=_pc/max(total_episodes,1), e=epm: (
                        self.progress_label.configure(text=f"◈ PROCESSING: {c} / {t}"),
                        self.eta_label.configure(text=eta),
                        self.progress_bar.set(pv),
                        self.speed_label.configure(text=f"{e:.1f} ep/min"),
                        self.stat_attempted.configure(text=f"▸ ATTEMPTED: {count_attempted}"),
                        self.stat_success.configure(text=f"▸ SUCCESS: {count_succeeded}"),
                        self.stat_failed.configure(text=f"▸ FAILED: {count_no_sub + count_no_audio + count_ffmpeg_err}")
                    ))

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {executor.submit(process_single_episode, video): video for video in video_files}
                for future in as_completed(futures):
                    if self.cancel_requested:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    try: future.result()
                    except: pass
            
            self.log(f"--- COMPLETED BATCH: {os.path.basename(folder)} ---", "INFO")
            self.safe_after(0, lambda f=folder: self.folder_queue.remove(f) if f in self.folder_queue else None)
            self.safe_after(0, self.update_queue_ui)

        self.log("ALL QUEUES PROCESSED SUCCESSFULLY.", "INFO")
        self.safe_after(0, _finalize_ui)

if __name__ == "__main__":
    app = PhoenixSubsMuxerFixer()
    app.mainloop()