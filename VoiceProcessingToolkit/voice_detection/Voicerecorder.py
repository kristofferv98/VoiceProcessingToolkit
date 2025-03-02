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
from VoiceProcessingToolkit.shared_resources import thread_manager

logger = logging.getLogger(__name__)


# Audio Data Provider Class
class AudioDataProvider:
    def __init__(self, audio_format=pyaudio.paInt16, channels=1, rate=16000, frames_per_buffer=512):
        self.audio_format = audio_format
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.stream = None
        self.py_audio = pyaudio.PyAudio()
        self.recording_finished_event = threading.Event()  # Signal recording completion

    def start_stream(self) -> bool:
        """
        Start the audio input stream.
        
        Returns:
            bool: True if the stream was started successfully, False otherwise.
        """
        try:
            self.stream = self.py_audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.frames_per_buffer
            )
            return True
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            return False

    def read_audio(self) -> Optional[bytes]:
        """
        Read audio data from the stream.
        
        Returns:
            bytes or None: Audio data read from the stream, or None if an error occurred.
        """
        if not self.stream:
            logger.error("Cannot read audio: stream not started")
            return None
        
        try:
            data = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
            return data
        except Exception as e:
            logger.error(f"Error reading audio data: {e}")
            return None

    def get_next_frame(self):
        """Legacy method for backward compatibility"""
        return self.read_audio()

    def stop_stream(self) -> None:
        """Stop the audio input stream and clean up resources."""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.warning(f"Error closing audio stream: {e}")
            finally:
                self.stream = None
                
        if self.py_audio:
            try:
                self.py_audio.terminate()
            except Exception as e:
                logger.warning(f"Error terminating PyAudio: {e}")
            finally:
                self.py_audio = None
    
    def get_sample_size(self) -> int:
        """
        Get the sample size in bytes for the audio format.
        
        Returns:
            int: Sample size in bytes.
        """
        if self.py_audio:
            return self.py_audio.get_sample_size(self.audio_format)
        return 2  # Default for paInt16
    
    def __del__(self):
        """Ensure cleanup when the object is garbage collected."""
        self.stop_stream()


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
        
        # Set up PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
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
            # Open audio stream
            self.stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.frames_per_buffer
            )
            
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
            
            # Main recording loop
            while not self.stopped:
                # Read audio data
                data = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
                audio_frame = np.frombuffer(data, dtype=np.int16)
                
                # Check voice activity with Cobra
                voice_probability = self.cobra.process(audio_frame)
                currently_speaking = voice_probability >= self.voice_threshold
                
                if currently_speaking:
                    if not is_speaking:
                        logger.info(colored("Voice detected, recording...", "green"))
                    
                    is_speaking = True
                    last_voice_time = time.time()
                    
                    if not recording_started:
                        recording_started = True
                        recording_start_time = time.time()
                        # Add any buffered silence frames at the beginning
                        frames.extend(silence_frames)
                        silence_frames = []
                    
                    frames.append(data)
                else:
                    # Not speaking, accumulate silence
                    if recording_started:
                        frames.append(data)
                    else:
                        # Buffer some silence before speech for better recordings
                        silence_frames.append(data)
                        if len(silence_frames) > int(self.buffer_length / frame_duration):
                            silence_frames.pop(0)
                    
                    # Check if we've exceeded silence limit
                    elapsed_silence = time.time() - last_voice_time
                    if recording_started and elapsed_silence >= self.silence_limit:
                        logger.info(colored(f"Silence limit reached ({elapsed_silence:.1f}s), stopping recording", "yellow"))
                        break
                
                # Check for inactivity timeout
                if recording_started:
                    elapsed_total = time.time() - recording_start_time
                    if elapsed_total >= self.inactivity_limit:
                        logger.info(colored(f"Recording reached inactivity limit ({elapsed_total:.1f}s), stopping", "yellow"))
                        break
            
            # Check if recording is valid (meets minimum length)
            recording_length = len(frames) * frame_duration
            if recording_started and recording_length >= self.min_recording_length:
                # Save the recording
                self.recorded_file = self._save_recording(frames)
                logger.info(colored(f"Recording saved: {self.recorded_file} ({recording_length:.1f}s)", "green"))
            else:
                logger.info(colored(f"Recording too short ({recording_length:.1f}s), discarding", "red"))
                self.recorded_file = None
        
        except Exception as e:
            logger.error(f"Error during recording: {e}")
            self.recorded_file = None
        
        finally:
            # Clean up resources
            self._cleanup()
            with self.lock:
                self.is_recording = False
    
    def _save_recording(self, frames: List[bytes]) -> str:
        """
        Save the recorded audio frames to a WAV file.
        
        Args:
            frames: List of audio frame data
        
        Returns:
            str: Path to the saved file
        """
        timestamp = int(time.time())
        filename = os.path.join(self.output_dir, f"recording_{timestamp}.wav")
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
        
        return filename
    
    def stop_recording(self) -> None:
        """
        Stop the ongoing recording process.
        """
        logger.info("Stopping recording")
        with self.lock:
            self.stopped = True
    
    def _cleanup(self) -> None:
        """
        Clean up audio resources.
        """
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def cleanup(self) -> None:
        """
        Clean up all resources used by the AudioRecorder.
        """
        logger.info("Cleaning up AudioRecorder resources")
        self.stop_recording()
        self._cleanup()
        
        if self.audio:
            self.audio.terminate()
            self.audio = None
        
        if self.cobra:
            self.cobra.delete()
            self.cobra = None


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
