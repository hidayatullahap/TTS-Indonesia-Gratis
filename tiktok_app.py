import os
import threading
import queue
import asyncio
import re
import html
import customtkinter as ctk
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent
from g2p_id.scripts.tts import tts
from simpleaudio import WaveObject
from uuid import uuid4

# Speaker Mapping from app.py
SPEAKER_MAPPING = {
    "Wibowo - Jantan": "wibowo",
    "Ardi - Lembut": "ardi",
    "Gadis - Merdu": "gadis",
    "Juminten - Jawa": "JV-00264",
    "Asep - Sunda": "SU-00060"
}

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class TikTokTTSApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TikTok Live TTS Desktop")
        self.geometry("600x550")
        
        # UI Elements
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.label_title = ctk.CTkLabel(self, text="TikTok Live TTS Integration", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_title.grid(row=0, column=0, padx=20, pady=20)

        # Username Input
        self.frame_user = ctk.CTkFrame(self)
        self.frame_user.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.frame_user.grid_columnconfigure(1, weight=1)
        
        self.label_user = ctk.CTkLabel(self.frame_user, text="TikTok Username:")
        self.label_user.grid(row=0, column=0, padx=10, pady=10)
        
        self.entry_user = ctk.CTkEntry(self.frame_user, placeholder_text="@username")
        self.entry_user.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Speaker Selection
        self.frame_speaker = ctk.CTkFrame(self)
        self.frame_speaker.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.frame_speaker.grid_columnconfigure(1, weight=1)
        
        self.label_speaker = ctk.CTkLabel(self.frame_speaker, text="Select Speaker:")
        self.label_speaker.grid(row=0, column=0, padx=10, pady=10)
        
        self.speaker_options = list(SPEAKER_MAPPING.keys())
        self.combo_speaker = ctk.CTkComboBox(self.frame_speaker, values=self.speaker_options)
        self.combo_speaker.set("Ardi - Lembut")
        self.combo_speaker.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Control Buttons
        self.frame_controls = ctk.CTkFrame(self)
        self.frame_controls.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.frame_controls.grid_columnconfigure((0, 1), weight=1)

        self.btn_start = ctk.CTkButton(self.frame_controls, text="Start Connection", command=self.start_app, fg_color="green", hover_color="darkgreen")
        self.btn_start.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.btn_stop = ctk.CTkButton(self.frame_controls, text="Stop Connection", command=self.stop_app, state="disabled", fg_color="red", hover_color="darkred")
        self.btn_stop.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Log Area
        self.log_area = ctk.CTkTextbox(self, height=200)
        self.log_area.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.log_area.configure(state="disabled")

        self.status_label = ctk.CTkLabel(self, text="Status: Disconnected", text_color="gray")
        self.status_label.grid(row=5, column=0, padx=20, pady=5)

        # Backend Logic Setup
        self.queue = queue.Queue()
        self.running = False
        self.client = None
        self.worker_thread = None
        self.tiktok_thread = None

    def log(self, message):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", message + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def update_status(self, status, color="gray"):
        self.status_label.configure(text=f"Status: {status}", text_color=color)

    def tts_worker(self):
        """Background thread to process TTS and play audio sequentially."""
        while self.running:
            try:
                # Use a timeout to occasionally check if self.running is still True
                comment_data = self.queue.get(timeout=1)
                user, text, speaker = comment_data
                
                clean_text = self.clean_comment(text)
                if not clean_text:
                    continue
                
                self.log(f"Speaking [{user}]: {clean_text}")
                
                filename = f"live_{speaker}_{str(uuid4())[:8]}.wav"
                output_path = os.path.join(OUTPUT_DIR, filename)
                
                # Generate TTS
                result = tts(f"{user} berkata: {clean_text}", speaker=speaker, output_file=output_path)
                
                if result == 0 and os.path.exists(output_path):
                    # Play audio and wait until done
                    try:
                        wave_obj = WaveObject.from_wave_file(output_path)
                        play_obj = wave_obj.play()
                        play_obj.wait_done()
                    except Exception as play_error:
                        self.log(f"Playback Error: {play_error}")
                    
                    # Optional: cleanup file after playing
                    try:
                        os.remove(output_path)
                    except:
                        pass
                
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                if self.running:
                    self.log(f"Worker Error: {e}")

    def clean_comment(self, text):
        # Remove emojis and unescape HTML
        text = html.unescape(text)
        # Simple regex to keep alphanumeric and some punctuation
        text = re.sub(r'[^\w\s,.?!]', '', text)
        return text.strip()

    def setup_client(self, username):
        self.client = TikTokLiveClient(unique_id=username)

        @self.client.on(ConnectEvent)
        async def on_connect(event):
            self.after(0, lambda: self.log(f"Connected to @{username}"))
            self.after(0, lambda: self.update_status("Connected", "green"))

        @self.client.on(DisconnectEvent)
        async def on_disconnect(event):
            self.after(0, lambda: self.log("Disconnected from TikTok"))
            self.after(0, lambda: self.update_status("Disconnected", "gray"))
            self.after(0, self.reset_ui)

        @self.client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            speaker_label = self.combo_speaker.get()
            speaker_id = SPEAKER_MAPPING.get(speaker_label, "ardi")
            self.queue.put((event.user.nickname, event.comment, speaker_id))
            self.after(0, lambda: self.log(f"Chat: {event.user.nickname}: {event.comment}"))

        try:
            # client.run() is blocking, that's why we run it in a thread
            self.client.run()
        except Exception as e:
            if self.running:
                self.after(0, lambda: self.log(f"Connection Error: {e}"))
                self.after(0, self.stop_app)

    def start_app(self):
        username = self.entry_user.get().strip()
        if not username:
            self.log("Error: Please enter a TikTok username.")
            return

        if username.startswith("@"):
            username = username[1:]

        self.running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.entry_user.configure(state="disabled")
        self.combo_speaker.configure(state="disabled")
        
        self.log(f"Connecting to @{username}...")
        self.update_status("Connecting...", "orange")

        # Start TTS Worker
        self.worker_thread = threading.Thread(target=self.tts_worker, daemon=True)
        self.worker_thread.start()

        # Start TikTok Client in another thread
        self.tiktok_thread = threading.Thread(target=self.setup_client, args=(username,), daemon=True)
        self.tiktok_thread.start()

    def reset_ui(self):
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.entry_user.configure(state="normal")
        self.combo_speaker.configure(state="normal")
        self.update_status("Disconnected", "gray")

    def stop_app(self):
        self.running = False
        self.log("Stopping connection...")
        
        if self.client:
            try:
                # Version 6.6.5 uses disconnect() or close()
                self.client.disconnect()
            except Exception as e:
                self.log(f"Error while disconnecting: {e}")
        
        self.reset_ui()

    def on_closing(self):
        self.stop_app()
        self.destroy()

if __name__ == "__main__":
    app = TikTokTTSApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
