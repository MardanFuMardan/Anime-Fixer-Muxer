import os
import re
import subprocess
import json
import logging
import threading
import tempfile
import customtkinter as ctk
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

class PhoenixSubsMuxerFixer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Phoenix Subs Muxer - Ultimate Edition")
        self.geometry("850x750")
        self.resizable(False, False)
        # OLED Pitch Black Background
        self.configure(fg_color="#000000") 
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.tools_dir = os.path.join(self.base_dir, "tools")
        self.ffmpeg_path = os.path.join(self.tools_dir, "ffmpeg.exe")
        self.ffprobe_path = os.path.join(self.tools_dir, "ffprobe.exe")
        
        self.folder_queue = []
        self.tools_ready = False
        self.is_processing = False
        
        self.setup_ui()
        self.check_local_tools()

    def setup_ui(self):
        # --- الفريم الرئيسي مع Padding ممتاز ---
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # --- الهيدر (العنوان) ---
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="PHOENIX MUXER", 
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color="#00E5FF" # Neon Cyan
        )
        title_label.pack(side="left")
        
        self.status_badge = ctk.CTkLabel(
            header_frame, text="⚫ STANDBY", font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#AAAAAA", fg_color="#111111", corner_radius=8, padx=10, pady=5
        )
        self.status_badge.pack(side="right", pady=5)

        # --- كارت الإعدادات ---
        settings_frame = ctk.CTkFrame(main_frame, corner_radius=12, fg_color="#0A0A0A", border_width=1, border_color="#1A1A1A")
        settings_frame.pack(fill="x", pady=10, ipadx=15, ipady=15)
        
        ctk.CTkLabel(settings_frame, text="DISPLAY RESOLUTION (ASS)", font=ctk.CTkFont(size=12, weight="bold"), text_color="#777777").pack(anchor="w", pady=(0, 10))

        res_inner = ctk.CTkFrame(settings_frame, fg_color="transparent")
        res_inner.pack(fill="x")

        ctk.CTkLabel(res_inner, text="PlayResX:", font=ctk.CTkFont(size=13)).grid(row=0, column=0, padx=(0, 10))
        self.res_x_entry = ctk.CTkEntry(res_inner, width=100, justify="center", font=ctk.CTkFont(weight="bold"), fg_color="#000000", border_color="#333333")
        self.res_x_entry.insert(0, "1920")
        self.res_x_entry.grid(row=0, column=1, padx=(0, 40))

        ctk.CTkLabel(res_inner, text="PlayResY:", font=ctk.CTkFont(size=13)).grid(row=0, column=2, padx=(0, 10))
        self.res_y_entry = ctk.CTkEntry(res_inner, width=100, justify="center", font=ctk.CTkFont(weight="bold"), fg_color="#000000", border_color="#333333")
        self.res_y_entry.insert(0, "1080")
        self.res_y_entry.grid(row=0, column=3)

        # --- كارت نظام الطابور (Queue System) ---
        queue_frame = ctk.CTkFrame(main_frame, corner_radius=12, fg_color="#0A0A0A", border_width=1, border_color="#1A1A1A")
        queue_frame.pack(fill="both", expand=True, pady=10, ipadx=15, ipady=15)

        queue_header = ctk.CTkFrame(queue_frame, fg_color="transparent")
        queue_header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(queue_header, text="BATCH PROCESSING QUEUE", font=ctk.CTkFont(size=12, weight="bold"), text_color="#777777").pack(side="left")
        
        self.add_folder_btn = ctk.CTkButton(
            queue_header, text="+ ADD ANIME FOLDER", width=140, height=30,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color="#7D5FFF", hover_color="#5F3DC4",
            command=self.add_folder_to_queue
        )
        self.add_folder_btn.pack(side="right")

        self.queue_listbox = ctk.CTkScrollableFrame(queue_frame, height=120, fg_color="#000000", border_color="#111111", border_width=1)
        self.queue_listbox.pack(fill="x")

        # --- كارت التنفيذ والسجلات ---
        action_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_frame.pack(fill="x", pady=(15, 0))

        self.process_btn = ctk.CTkButton(
            action_frame, text="INITIALIZE BATCH PROCESS", 
            font=ctk.CTkFont(size=15, weight="bold"), height=50,
            fg_color="#00CC66", hover_color="#00994C", state="disabled",
            command=self.start_processing_thread
        )
        self.process_btn.pack(fill="x", pady=(0, 15))

        self.log_box = ctk.CTkTextbox(action_frame, height=160, fg_color="#050505", text_color="#00E5FF", font=ctk.CTkFont(family="Consolas", size=11), border_color="#1A1A1A", border_width=1)
        self.log_box.pack(fill="x")

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

    def check_local_tools(self):
        if os.path.exists(self.ffmpeg_path) and os.path.exists(self.ffprobe_path):
            self.tools_ready = True
            self.log("System tools validated successfully.", "INFO")
        else:
            self.tools_ready = False
            self.log("CRITICAL: FFmpeg toolkit not found in /tools directory.", "ERROR")
            messagebox.showerror("Error", "FFmpeg tools missing from the tools directory.")

    def add_folder_to_queue(self):
        if not self.tools_ready:
            self.log("Cannot add folders. Tools are missing.", "WARNING")
            return
            
        folder = filedialog.askdirectory(title="Select Anime Root Folder")
        if folder:
            if folder in self.folder_queue:
                self.log(f"Folder already in queue: {os.path.basename(folder)}", "WARNING")
                return
                
            subs_path = os.path.join(folder, "subs")
            if not os.path.exists(subs_path):
                self.log(f"Rejected {os.path.basename(folder)}: Missing 'subs' directory.", "ERROR")
                messagebox.showerror("Structure Error", f"The folder '{os.path.basename(folder)}' does not contain a 'subs' subdirectory.")
                return
            
            self.folder_queue.append(folder)
            self.update_queue_ui()
            self.process_btn.configure(state="normal")
            self.log(f"Added to queue: {folder}")

    def update_queue_ui(self):
        def _update():
            for widget in self.queue_listbox.winfo_children():
                widget.destroy()
                
            for i, folder in enumerate(self.folder_queue):
                row = ctk.CTkFrame(self.queue_listbox, fg_color="#111111", corner_radius=6)
                row.pack(fill="x", pady=2, padx=2)
                
                ctk.CTkLabel(row, text=f"{i+1}. {os.path.basename(folder)}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").pack(side="left", padx=10, pady=5)
                
                remove_btn = ctk.CTkButton(row, text="X", width=30, height=24, fg_color="#FF3333", hover_color="#CC0000", command=lambda f=folder: self.remove_from_queue(f))
                remove_btn.pack(side="right", padx=10)
        self.after(0, _update)

    def remove_from_queue(self, folder):
        if self.is_processing:
            return
        self.folder_queue.remove(folder)
        self.update_queue_ui()
        if not self.folder_queue:
            self.process_btn.configure(state="disabled")
        self.log(f"Removed from queue: {os.path.basename(folder)}")

    def extract_episode_number(self, filename):
        clean_name = re.sub(r'1080p|720p|2160p|4k|x265|x264|10bit', '', filename, flags=re.IGNORECASE)
        match = re.search(r'(?:E|EP|Episode|- |v)\s*0*(\d+)', clean_name, re.IGNORECASE)
        if match:
            return match.group(1)
        numbers = re.findall(r'\d+', clean_name)
        return numbers[-1] if numbers else None

    def get_best_audio_stream(self, video_path):
        cmd = [self.ffprobe_path, '-v', 'error', '-show_entries', 'stream=index,codec_type,channels:stream_tags=language', '-of', 'json', video_path]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            data = json.loads(result.stdout)
            
            audio_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
            if not audio_streams: return None

            for stream in audio_streams:
                lang = stream.get('tags', {}).get('language', '').lower()
                channels = stream.get('channels', 0)
                if lang in ['jpn', 'ja', 'japanese'] and channels == 2:
                    return {'index': stream['index'], 'language': lang, 'channels': channels}
            return None
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
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()

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

    def start_processing_thread(self):
        if not self.folder_queue: return
        self.is_processing = True
        self.process_btn.configure(state="disabled", fg_color="#333333", text="PROCESSING IN PROGRESS...")
        self.add_folder_btn.configure(state="disabled")
        self.status_badge.configure(text="🟢 ACTIVE", text_color="#00CC66", fg_color="#003311")
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        res_x = self.res_x_entry.get().strip()
        res_y = self.res_y_entry.get().strip()

        for folder in list(self.folder_queue):
            self.log(f"--- STARTING BATCH: {os.path.basename(folder)} ---", "INFO")
            subs_folder = os.path.join(folder, "subs")
            output_dir = os.path.join(folder, "Phoenix_Output")
            os.makedirs(output_dir, exist_ok=True)

            video_files = [f for f in os.listdir(folder) if f.endswith(('.mkv', '.mp4'))]
            sub_files = [f for f in os.listdir(subs_folder) if f.endswith('.ass')]

            for video in video_files:
                vid_path = os.path.join(folder, video)
                out_path = os.path.join(output_dir, video)

                if os.path.exists(out_path) and os.path.getsize(out_path) > 5000000:
                    self.log(f"Skipping Ep: {video} (Already exists in Output - Resume active)", "WARNING")
                    continue

                vid_ep = self.extract_episode_number(video)
                if not vid_ep:
                    self.log(f"Failed to extract episode number from {video}", "ERROR")
                    continue

                matched_sub = next((s for s in sub_files if self.extract_episode_number(s) == vid_ep), None)
                if not matched_sub:
                    self.log(f"Skipping Ep {vid_ep}: No matching subtitle found in 'subs' folder.", "ERROR")
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
                    self.log(f"Skipping Ep {vid_ep}: No Japanese stereo audio track found.", "ERROR")
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
                    '-c:s', 'ass',
                    '-metadata:s:s:0', 'language=ara',
                    '-metadata:s:s:0', 'title=Anime Phoenix Subtitles',
                    '-disposition:s:s:0', 'default'
                ]
                
                if vid_duration:
                    ffmpeg_cmd.extend(['-t', str(vid_duration)])
                    
                ffmpeg_cmd.append(out_path)

                try:
                    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    self.log(f"SUCCESS: Ep {vid_ep} completed.")
                except subprocess.CalledProcessError:
                    self.log(f"FFmpeg muxing failed for Ep {vid_ep}.", "ERROR")
                finally:
                    if os.path.exists(temp_sub_path):
                        try:
                            os.remove(temp_sub_path)
                        except OSError as e:
                            self.log(f"Failed to remove temp file {temp_sub_path}: {e}", "WARNING")
            
            self.log(f"--- COMPLETED BATCH: {os.path.basename(folder)} ---", "INFO")
            self.folder_queue.remove(folder)
            self.update_queue_ui()

        self.log("ALL QUEUES PROCESSED SUCCESSFULLY.", "INFO")
        
        def _finalize_ui():
            self.is_processing = False
            self.process_btn.configure(state="disabled", fg_color="#00CC66", text="INITIALIZE BATCH PROCESS")
            self.add_folder_btn.configure(state="normal")
            self.status_badge.configure(text="⚫ STANDBY", text_color="#AAAAAA", fg_color="#111111")
            
        self.after(0, _finalize_ui)

if __name__ == "__main__":
    app = PhoenixSubsMuxerFixer()
    app.mainloop()