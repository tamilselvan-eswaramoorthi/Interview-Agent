#!/usr/bin/env python3
"""
Flask Web Application for AI Interview Assistant
"""

import os
import logging
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

from audio_handler import AudioStreamHandler
from ai_handler import GeminiHandler
from gcp_bucket_listener import GCPBucketListener
from utils import list_audio_devices, verify_device

# Configuration
DEVICE_ID = 11
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
socketio = SocketIO(app, cors_allowed_origins="*")


class WebTranscriptionApp:
    def __init__(self):
        self.is_recording = False
        self.recording_thread = None
        self.bucket_listener_thread = None
        self.start_time = datetime.now()  # Record webapp start time
        self.image_list = []  # Track all processed images
        
        self.audio_handler = AudioStreamHandler(ASSEMBLYAI_API_KEY, DEVICE_ID) if ASSEMBLYAI_API_KEY else None
        self.ai_handler = GeminiHandler(GEMINI_API_KEY) if GEMINI_API_KEY else None
        
        # Initialize GCP bucket listener if configured
        self.bucket_listener = None
        if GCP_BUCKET_NAME and GEMINI_API_KEY:
            try:
                # Pass start_time to only process images uploaded after webapp starts
                self.bucket_listener = GCPBucketListener(GCP_BUCKET_NAME, start_time=self.start_time)
                self.bucket_listener.on_new_image = self._handle_new_image
                self._start_bucket_monitoring()
                logger.info(f"GCP bucket listener initialized for: {GCP_BUCKET_NAME}")
                logger.info(f"Only processing images uploaded after: {self.start_time}")
            except Exception as e:
                logger.error(f"Failed to initialize GCP bucket listener: {e}")
                self.bucket_listener = None
        
        # Setup callbacks
        if self.audio_handler:
            self.audio_handler.on_status_update = self._handle_status_update
            self.audio_handler.on_transcript_update = self._handle_transcript
        
        if self.ai_handler:
            self.ai_handler.on_response = self._handle_ai_response
            self.ai_handler.on_clear_transcription = self._handle_clear_transcription
            self.ai_handler.on_image_response = self._handle_image_response
        
    def _handle_status_update(self, message, color='black'):
        """Send status update to web client"""
        socketio.emit('status_update', {'message': message, 'color': color})
        
    def _handle_transcript(self, transcript):
        """Send transcript to web client and process with AI"""
        socketio.emit('transcription', {'text': transcript})
        if self.ai_handler:
            self.ai_handler.process_transcript(transcript)
    
    def _handle_ai_response(self, response_text):
        """Send AI response to web client"""
        socketio.emit('ai_response', {'text': response_text, 'type': 'text'})
    
    def _handle_clear_transcription(self):
        """Clear transcription on web client"""
        socketio.emit('clear_transcription')
    
    def _start_bucket_monitoring(self):
        """Start monitoring GCP bucket in background thread"""
        def monitor_bucket():
            if self.bucket_listener:
                self.bucket_listener.listen(interval=10)
        
        self.bucket_listener_thread = threading.Thread(target=monitor_bucket)
        self.bucket_listener_thread.daemon = True
        self.bucket_listener_thread.start()
        logger.info("Bucket monitoring thread started")
    
    def _handle_new_image(self, local_path, file_info):
        """Handle new image detected from GCP bucket"""
        logger.info(f"Processing new image: {local_path}")
        
        # Add to image list (prepend to keep latest at top)
        image_data = {
            'name': file_info['name'],
            'local_path': local_path,
            'created': file_info.get('created'),
            'timestamp': datetime.now().isoformat()
        }
        self.image_list.insert(0, image_data)  # Insert at beginning for latest-first order
        
        # Notify client about new image in list
        socketio.emit('new_image_item', {
            'name': file_info['name'],
            'timestamp': image_data['timestamp']
        })
        
        socketio.emit('status_update', {
            'message': f"📸 New image detected: {file_info['name']}", 
            'color': 'blue'
        })
        
        # Process the image with Gemini
        if self.ai_handler:
            self.ai_handler.process_image(local_path)
    
    def _handle_image_response(self, response_text, image_path):
        """Handle response from image analysis - send result only, no image"""
        image_name = os.path.basename(image_path)
        
        # Send only the text response for the specific image
        socketio.emit('image_response', {
            'text': response_text,
            'image_name': image_name,
            'image_path': image_path
        })
        logger.info(f"Image analysis response sent for: {image_name}")
    
    def get_image_list(self):
        """Get list of all processed images"""
        return self.image_list
    
    def start_recording(self):
        """Start audio recording"""
        if not self.audio_handler:
            return {'success': False, 'error': 'Audio handler not initialized'}
        
        if self.is_recording:
            return {'success': False, 'error': 'Already recording'}
        
        # Cleanup existing client
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
        self._handle_status_update("Recording... Speak into your microphone", 'red')
        
        self.recording_thread = threading.Thread(target=self._run_streaming)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        return {'success': True}
    
    def _run_streaming(self):
        """Run audio streaming in background thread"""
        try:
            self.audio_handler.start_streaming()
        except Exception as e:
            self._handle_status_update(f"Error starting recording: {e}", 'red')
        finally:
            if self.is_recording:
                self.is_recording = False
                self._handle_status_update("Recording stopped unexpectedly", 'orange')
    
    def stop_recording(self):
        """Stop audio recording"""
        if not self.audio_handler:
            return {'success': False, 'error': 'Audio handler not initialized'}
        
        self.is_recording = False
        self.audio_handler.stop_streaming()
        
        if hasattr(self, 'recording_thread') and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        self._handle_status_update("Recording stopped", 'black')
        return {'success': True}
    
    def toggle_ai_freeze(self, freeze):
        """Toggle AI freeze state"""
        if not self.ai_handler:
            return {'success': False, 'error': 'AI handler not initialized'}
        
        self.ai_handler.set_frozen(freeze)
        if freeze:
            self._handle_status_update("AI responses frozen", 'orange')
        else:
            self._handle_status_update("AI responses active", 'green')
        
        return {'success': True, 'is_frozen': freeze}


# Create global app instance
web_app = WebTranscriptionApp()


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected")
    emit('status_update', {'message': 'Connected to server', 'color': 'green'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected")


@socketio.on('start_recording')
def handle_start_recording():
    """Handle start recording request"""
    result = web_app.start_recording()
    emit('recording_state', {'is_recording': result.get('success', False), 'error': result.get('error')})


@socketio.on('stop_recording')
def handle_stop_recording():
    """Handle stop recording request"""
    result = web_app.stop_recording()
    emit('recording_state', {'is_recording': False, 'error': result.get('error')})


@socketio.on('toggle_freeze')
def handle_toggle_freeze(data):
    """Handle AI freeze toggle"""
    freeze = data.get('freeze', False)
    result = web_app.toggle_ai_freeze(freeze)
    emit('freeze_state', {'is_frozen': result.get('is_frozen', False), 'error': result.get('error')})


@socketio.on('clear_all')
def handle_clear_all():
    """Handle clear all request"""
    emit('clear_all')


@socketio.on('get_image_list')
def handle_get_image_list():
    """Handle request for image list"""
    emit('image_list', {'images': web_app.get_image_list()})


def run_flask_app(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask application"""
    logger.info(f"Starting Flask application on {host}:{port}")
    logger.info(f"Webapp start time: {web_app.start_time}")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    # List available audio devices
    list_audio_devices()
    
    # Verify device
    if not verify_device(DEVICE_ID):
        logger.warning(f"Device {DEVICE_ID} not available!")
    
    # Run the app
    run_flask_app(debug=True)
