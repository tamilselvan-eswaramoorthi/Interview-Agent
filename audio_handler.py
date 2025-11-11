import assemblyai as aai
from assemblyai.streaming.v3 import (
    StreamingClient,
    StreamingClientOptions,
    StreamingEvents,
    StreamingParameters
)
import logging
import threading


logger = logging.getLogger(__name__)


class AudioStreamHandler:
    def __init__(self, api_key, device_id):
        self.api_key = api_key
        self.device_id = device_id
        self.client = None
        self.is_recording = False
        self.current_transcript = ""
        self.last_processed_transcript = ""
        self.transcript_timer = None
        self.transcript_delay = 3.0
        
        self.on_status_update = None
        self.on_transcript_update = None
        
    def start_streaming(self):
        try:
            self.client = StreamingClient(
                StreamingClientOptions(
                    api_key=self.api_key,
                    api_host="streaming.assemblyai.com",
                )
            )

            def on_begin(client, event):
                if self.on_status_update:
                    self.on_status_update(f"Session started: {event.id}", 'green')

            def on_turn(client, event):
                if event.transcript.strip():
                    self.current_transcript = event.transcript.strip()
                    
                    if self.transcript_timer:
                        self.transcript_timer.cancel()
                    
                    if event.end_of_turn:
                        self._process_transcript_immediately()
                    else:
                        self._schedule_transcript_processing()

            def on_terminated(client, event):
                if self.on_status_update:
                    self.on_status_update(f"Session terminated: {event.audio_duration_seconds} seconds processed", 'black')

            def on_error(client, error):
                if self.on_status_update:
                    self.on_status_update(f"Error: {error}", 'red')

            self.client.on(StreamingEvents.Begin, on_begin)
            self.client.on(StreamingEvents.Turn, on_turn)
            self.client.on(StreamingEvents.Termination, on_terminated)
            self.client.on(StreamingEvents.Error, on_error)

            self.client.connect(
                StreamingParameters(
                    device_index=self.device_id,
                    sample_rate=16000,
                    format_turns=True,
                    min_end_of_turn_silence_when_confident=2000,
                    max_turn_silence=5000,
                    end_of_turn_confidence_threshold=0.8
                )
            )

            self.client.stream(
                aai.extras.MicrophoneStream(device_index=self.device_id, sample_rate=16000)
            )
            
        except Exception as e:
            if self.on_status_update:
                self.on_status_update(f"Error starting recording: {e}", 'red')
            raise
        finally:
            if self.client:
                try:
                    self.client.disconnect(terminate=True)
                except Exception as cleanup_error:
                    logger.info(f"Error during cleanup: {cleanup_error}")
                finally:
                    self.client = None
                    
    def stop_streaming(self):
        self.is_recording = False
        
        if self.transcript_timer:
            self.transcript_timer.cancel()
            self.transcript_timer = None
            
        if self.client:
            try:
                self.client.disconnect(terminate=True)
            except Exception as e:
                logger.info(f"Error disconnecting client: {e}")
            finally:
                self.client = None
                
    def _process_transcript_immediately(self):
        if self.current_transcript and self.current_transcript != self.last_processed_transcript:
            if self.on_transcript_update:
                self.on_transcript_update(self.current_transcript)
            self.last_processed_transcript = self.current_transcript
        
    def _schedule_transcript_processing(self):
        def process_delayed():
            if self.current_transcript and self.current_transcript != self.last_processed_transcript:
                self._process_transcript_immediately()
        
        self.transcript_timer = threading.Timer(self.transcript_delay, process_delayed)
        self.transcript_timer.start()
