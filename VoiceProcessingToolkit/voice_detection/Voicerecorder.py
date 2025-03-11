#!/usr/bin/env python3
import collections
import logging
import os
from dotenv import load_dotenv
import wave
import time
import threading
import numpy as np
import pyaudio
import pvcobra
import datetime
from typing import Optional, List, Dict, Any, Tuple, Union
from termcolor import colored

from VoiceProcessingToolkit.interfaces import AudioRecorderInterface
from VoiceProcessingToolkit.config import default_config
from VoiceProcessingToolkit.shared_resources import thread_manager, AudioDataProvider

logger = logging.getLogger(__name__)

class AudioRecorder(AudioRecorderInterface):
    """
    Records audio when voice activity is detected using PicoVoice Cobra VAD.
    Implements the AudioRecorderInterface for compatibility with the V2 architecture.
    """
    
    def __init__(
        self,
        output_dir: str = "Wav_MP3",
        rate: int = 16000,
        channels: int = 1,
        audio_format: int = pyaudio.paInt16,
        frames_per_buffer: int = 512,
        voice_threshold: float = 0.8,
        silence_limit: float = 2.0,
        inactivity_limit: float = 2.0,
        min_recording_length: float = 2.0,
        buffer_length: float = 2.0
    ):
        """
        Initialize the AudioRecorder.
        
        Args:
            output_dir: Directory to save recorded audio files
            rate: Sample rate for audio recording
            channels: Number of audio channels
            audio_format: PyAudio format (e.g. pyaudio.paInt16)
            frames_per_buffer: Number of frames per buffer
            voice_threshold: Probability threshold for Cobra VAD (0-1)
            silence_limit: Maximum silence time before stopping (seconds)
            inactivity_limit: Maximum inactivity time before stopping (seconds)
            min_recording_length: Minimum valid recording length (seconds)
            buffer_length: Length of audio buffer (seconds)
        """
        self.output_dir = output_dir
        self.rate = rate
        self.channels = channels
        self.audio_format = audio_format
        self.frames_per_buffer = frames_per_buffer
        
        # VAD settings
        self.voice_threshold = voice_threshold
        self.silence_limit = silence_limit
        self.inactivity_limit = inactivity_limit
        self.min_recording_length = min_recording_length
        self.buffer_length = buffer_length
        
        # Status flags
        self.is_recording = False
        self.stopped = False
        
        # Initialize Cobra VAD
        try:
            self.cobra = pvcobra.create(access_key=os.environ.get('PICOVOICE_APIKEY'))
            logger.info("Cobra VAD initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cobra VAD: {e}")
            self.cobra = None
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Initialize audio provider
        self.audio_provider = AudioDataProvider(
            rate=self.rate,
            channels=self.channels,
            audio_format=self.audio_format,
            frames_per_buffer=self.frames_per_buffer
        )
        
        # Threading setup
        self.recording_thread = None
        self.lock = threading.Lock()
        
    def start_recording(self) -> Optional[str]:
        """
        Start recording audio with voice activity detection.
        
        Returns:
            str: Path to the recorded file if successful, None otherwise
        """
        if self.is_recording:
            logger.warning("Already recording, cannot start new recording")
            return None
        
        with self.lock:
            self.is_recording = True
            self.stopped = False
        
        # Start recording in a new thread
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        # Add thread to thread manager
        thread_manager.add_thread(self.recording_thread)
        
        # Wait for recording to complete
        self.recording_thread.join()
        
        # Check if recording was successful
        with self.lock:
            if hasattr(self, 'recorded_file') and self.recorded_file:
                return self.recorded_file
            return None
    
    def _record_audio(self) -> None:
        """
        Internal method to record audio with voice activity detection.
        """
        if not self.cobra:
            logger.error("Cobra VAD not initialized, aborting recording")
            with self.lock:
                self.is_recording = False
            return
        
        try:
            # Start audio stream
            if not self.audio_provider.start_stream():
                logger.error("Failed to start audio stream")
                with self.lock:
                    self.is_recording = False
                return
            
            logger.info(colored("Listening for voice activity...", "yellow"))
            
            # Initialize variables for recording
            frames = []
            silence_frames = []
            current_time = time.time()
            recording_started = False
            is_speaking = False
            last_voice_time = current_time
            recording_start_time = current_time
            
            # Calculate frame sizes
            frame_duration = self.frames_per_buffer / self.rate
            silence_limit_frames = int(self.silence_limit / frame_duration)
            inactivity_frames = int(self.inactivity_limit / frame_duration)
            min_recording_frames = int(self.min_recording_length / frame_duration)
            
            while self.is_recording and not self.stopped:
                # Read audio data
                audio_data = self.audio_provider.read_audio()
                if audio_data is None:
                    logger.error("Failed to read audio data")
                    break
                
                # Convert audio data to numpy array for VAD
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Check for voice activity
                voice_probability = self.cobra.process(audio_array)
                
                current_time = time.time()
                
                if voice_probability > self.voice_threshold:
                    is_speaking = True
                    last_voice_time = current_time
                    silence_frames = []
                    
                    if not recording_started:
                        recording_started = True
                        recording_start_time = current_time
                        logger.info(colored("Voice activity detected, starting recording...", "green"))
                    
                    frames.append(audio_data)
                else:
                    is_speaking = False
                    silence_frames.append(audio_data)
                    
                    # Check for silence or inactivity
                    if len(silence_frames) >= silence_limit_frames:
                        logger.info(colored("Silence detected, stopping recording...", "yellow"))
                        break
                    
                    if current_time - last_voice_time >= self.inactivity_limit:
                        logger.info(colored("Inactivity detected, stopping recording...", "yellow"))
                        break
                
                # Check minimum recording length
                if recording_started and current_time - recording_start_time >= self.min_recording_length:
                    if not is_speaking:
                        logger.info(colored("Minimum recording length reached, stopping...", "yellow"))
                        break
            
            # Save recording if we have enough frames
            if len(frames) >= min_recording_frames:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(self.output_dir, f"recording_{timestamp}.wav")
                
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.audio_provider.get_sample_size())
                    wf.setframerate(self.rate)
                    wf.writeframes(b''.join(frames))
                
                self.recorded_file = filename
                logger.info(colored(f"Recording saved to {filename}", "green"))
            else:
                logger.warning(colored("Recording too short, not saving", "yellow"))
                self.recorded_file = None
            
        except Exception as e:
            logger.error(f"Error during recording: {e}")
            self.recorded_file = None
        finally:
            # Clean up
            self.audio_provider.stop_stream()
            with self.lock:
                self.is_recording = False
    
    def stop_recording(self) -> None:
        """Stop the current recording."""
        with self.lock:
            self.stopped = True
            self.is_recording = False
    
    def get_last_saved_file(self) -> Optional[str]:
        """Get the path of the last saved recording."""
        return getattr(self, 'recorded_file', None)
    
    def perform_recording(self) -> Optional[str]:
        """
        Start recording audio until certain conditions are met.
        
        This implements the required method from AudioRecorderInterface.
        
        Returns:
            str or None: Path to the recorded audio file if successful, None otherwise.
        """
        logger.info("Starting audio recording")
        self.start_recording()
        # The actual recording happens in a separate thread
        # We return the path of the last saved file, which will be updated by the recording thread
        return self.get_last_saved_file()
    
    @property
    def last_saved_file(self) -> Optional[str]:
        """
        Get the path of the last saved recording.
        
        This property is added for compatibility with the interface.
        """
        return self.get_last_saved_file()
    
    def cleanup(self) -> None:
        """
        Release all resources used by the recorder.
        
        This implements the required method from AudioRecorderInterface.
        """
        logger.info("Cleaning up AudioRecorder resources")
        self.stop_recording()
        if hasattr(self, 'audio_provider') and self.audio_provider:
            self.audio_provider.stop_stream()
        if hasattr(self, 'cobra') and self.cobra:
            self.cobra.delete()
        
        # Make sure recording thread is stopped
        if hasattr(self, 'recording_thread') and self.recording_thread and self.recording_thread.is_alive():
            logger.debug("Waiting for recording thread to finish")
            self.recording_thread.join(timeout=2.0)  # Wait for 2 seconds max
            if self.recording_thread.is_alive():
                logger.warning("Recording thread did not finish in time")
    
    def __del__(self):
        """Clean up resources when the object is destroyed."""
        self.cleanup()


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    load_dotenv()

    # Set up the audio recorder
    recorder = AudioRecorder()

    # Start the recording process
    recorder.start_recording()

    # Clean up
    recorder.cleanup()

