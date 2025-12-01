import logging
import os
import tkinter as tk
from tkinter import messagebox
import threading

from ui_components import TranscriptionUI
from audio_handler import AudioStreamHandler
from ai_handler import GeminiHandler
from gcp_bucket_listener import GCPBucketListener
from utils import list_audio_devices, verify_device


DEVICE_ID = 11
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.is_recording = False
        self.recording_thread = None
        self.bucket_listener_thread = None
        
        self.ui = TranscriptionUI(root)
        self.audio_handler = AudioStreamHandler(ASSEMBLYAI_API_KEY, DEVICE_ID)
        self.ai_handler = GeminiHandler(GEMINI_API_KEY)
        
        # Initialize GCP bucket listener if configured
        self.bucket_listener = None
        if GCP_BUCKET_NAME:
            try:
                self.bucket_listener = GCPBucketListener(GCP_BUCKET_NAME)
                self.bucket_listener.on_new_image = self._handle_new_image
                self._start_bucket_monitoring()
                logger.info(f"GCP bucket listener initialized for: {GCP_BUCKET_NAME}")
            except Exception as e:
                logger.error(f"Failed to initialize GCP bucket listener: {e}")
                self.bucket_listener = None
        
        self.audio_handler.on_status_update = self.ui.update_status
        self.audio_handler.on_transcript_update = self._handle_transcript
        
        self.ai_handler.on_response = self.ui.add_response
        self.ai_handler.on_clear_transcription = self.ui.clear_transcription
        self.ai_handler.on_image_response = self._handle_image_response
        
        self.ui.start_button.config(command=self.start_recording)
        self.ui.stop_button.config(command=self.stop_recording)
        self.ui.clear_button.config(command=self.ui.clear_text)
        self.ui.freeze_button.config(command=self.toggle_ai_freeze)
        
    def _handle_transcript(self, transcript):
        self.ui.add_transcription(transcript)
        self.ai_handler.process_transcript(transcript)
    
    def _start_bucket_monitoring(self):
        """Start monitoring GCP bucket in background thread"""
        def monitor_bucket():
            if self.bucket_listener:
                self.bucket_listener.listen(interval=5)
        
        self.bucket_listener_thread = threading.Thread(target=monitor_bucket)
        self.bucket_listener_thread.daemon = True
        self.bucket_listener_thread.start()
        logger.info("Bucket monitoring thread started")
    
    def _handle_new_image(self, local_path, file_info):
        """Handle new image detected from GCP bucket"""
        logger.info(f"Processing new image: {local_path}")
        self.ui.update_status(f"📸 New image detected: {file_info['name']}", 'blue')
        
        # Process the image with Gemini
        self.ai_handler.process_image(local_path)
    
    def _handle_image_response(self, response_text, image_path):
        """Handle response from image analysis"""
        image_name = os.path.basename(image_path)
        header = f"\n{'='*60}\n📸 IMAGE ANALYSIS: {image_name}\n{'='*60}\n\n"
        full_response = header + response_text
        self.ui.add_response(full_response)
        logger.info(f"Image analysis response added to UI for: {image_name}")
        
    def toggle_ai_freeze(self):
        is_frozen = not self.ai_handler.is_frozen
        self.ai_handler.set_frozen(is_frozen)
        if is_frozen:
            self.ui.freeze_button.config(text="Unfreeze AI")
            self.ui.update_status("AI responses frozen", 'orange')
        else:
            self.ui.freeze_button.config(text="Freeze AI")
            self.ui.update_status("AI responses active", 'green')
        
    def start_recording(self):
        if not ASSEMBLYAI_API_KEY or "YOUR_ASSEMBLYAI_API_KEY" in ASSEMBLYAI_API_KEY:
            messagebox.showerror("Configuration Error", 
                               "Please set your AssemblyAI API key in the environment variables.")
            return
        
        if self.audio_handler.client:
            try:
                self.audio_handler.client.disconnect(terminate=True)
            except:
                pass
            finally:
                self.audio_handler.client = None
        if self.recording_thread is not None and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)
        self.is_recording = True
        self.ui.start_button.config(state='disabled')
        self.ui.stop_button.config(state='normal')
        self.ui.update_status("Recording... Speak into your microphone", 'red')
        
        self.recording_thread = threading.Thread(target=self._run_streaming)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
    def _run_streaming(self):
        try:
            self.audio_handler.start_streaming()
        except Exception as e:
            self.ui.update_status(f"Error starting recording: {e}", 'red')
            self.root.after(0, lambda: messagebox.showerror("Recording Error", str(e)))
        finally:
            if self.is_recording:
                self.is_recording = False
                self.root.after(0, lambda: (
                    self.ui.start_button.config(state='normal'),
                    self.ui.stop_button.config(state='disabled'),
                    self.ui.update_status("Recording stopped unexpectedly", 'orange')
                ))
        
    def stop_recording(self):
        self.is_recording = False
        self.audio_handler.stop_streaming()
        
        if hasattr(self, 'recording_thread') and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        self.ui.start_button.config(state='normal')
        self.ui.stop_button.config(state='disabled')
        self.ui.update_status("Recording stopped", 'black')


def run_audio_mode():
    """Run the application in audio interview mode"""
    list_audio_devices()
    
    if not verify_device(DEVICE_ID):
        print(f"\nWARNING: Device {DEVICE_ID} not available!")
        print("Please update DEVICE_ID in the script.")
        return
    
    root = tk.Tk()
    app = TranscriptionApp(root)
    
    def on_closing():
        if app.is_recording:
            app.stop_recording()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


def main():
    """Legacy main function for backward compatibility"""
    run_audio_mode()


if __name__ == "__main__":
    main()