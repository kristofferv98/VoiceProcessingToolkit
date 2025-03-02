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
from typing import Optional, Tuple, List, Dict, Any, Union

from VoiceProcessingToolkit.interfaces import AudioRecorderInterface
from VoiceProcessingToolkit.config import default_config
from VoiceProcessingToolkit.shared_resources import thread_manager

logger = logging.getLogger(__name__)


# Audio Data Provider Class
class AudioDataProvider:
    def __init__(self, frames_per_buffer: int = 1024, channels: int = 1, 
                 rate: int = 16000, audio_format: int = pyaudio.paInt16):
        """
        Initialize a new AudioDataProvider.
        
        Args:
            frames_per_buffer: Number of frames per buffer.
            channels: Number of audio channels.
            rate: Sample rate.
            audio_format: Audio format (e.g., pyaudio.paInt16).
        """
        self.frames_per_buffer = frames_per_buffer
        self.channels = channels
        self.rate = rate
        self.audio_format = audio_format
        
        self.py_audio: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.logger = logging.getLogger(__name__)
        
        # Cache of audio devices
        self._input_device_info: Optional[Dict[str, Any]] = None

    def start_stream(self) -> bool:
        """
        Start the audio input stream.
        
        Returns:
            bool: True if the stream was started successfully, False otherwise.
        """
        try:
            # Clean up any existing stream first
            self.stop_stream()
            
            self.py_audio = pyaudio.PyAudio()
            
            # Get default input device
            device_info = self._get_default_input_device()
            if device_info:
                self.logger.info(f"Using input device: {device_info['name']}")
            
            self.stream = self.py_audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.frames_per_buffer
            )
            
            self.logger.debug("Audio stream started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start audio stream: {e}")
            self.stop_stream()  # Clean up partial resources
            return False
    
    def stop_stream(self) -> None:
        """Stop the audio input stream and clean up resources."""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                self.logger.debug("Audio stream closed")
            except Exception as e:
                self.logger.warning(f"Error closing audio stream: {e}")
            finally:
                self.stream = None
                
        if self.py_audio:
            try:
                self.py_audio.terminate()
                self.logger.debug("PyAudio terminated")
            except Exception as e:
                self.logger.warning(f"Error terminating PyAudio: {e}")
            finally:
                self.py_audio = None
    
    def read_audio(self) -> Optional[bytes]:
        """
        Read audio data from the stream.
        
        Returns:
            bytes or None: Audio data read from the stream, or None if an error occurred.
        """
        if not self.stream:
            self.logger.error("Cannot read audio: stream not started")
            return None
        
        try:
            data = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
            return data
        except Exception as e:
            self.logger.error(f"Error reading audio data: {e}")
            return None
    
    def _get_default_input_device(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the default input device.
        
        Returns:
            dict or None: Information about the default input device, or None if not available.
        """
        if not self.py_audio:
            return None
            
        if self._input_device_info is not None:
            return self._input_device_info
            
        try:
            default_input_device_index = self.py_audio.get_default_input_device_info()['index']
            self._input_device_info = self.py_audio.get_device_info_by_index(default_input_device_index)
            return self._input_device_info
        except Exception as e:
            self.logger.warning(f"Could not get default input device info: {e}")
            return None
    
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


class VoiceActivityDetector:
    """
    Detects voice activity in audio data.
    
    Attributes:
        energy_threshold (float): Threshold for energy-based voice detection.
        silence_threshold (float): Energy level below which audio is considered silence.
        min_speaking_time (float): Minimum duration of speech to be considered a valid segment.
        min_silence_time (float): Minimum duration of silence to finish recording.
        max_speaking_time (float): Maximum allowed duration for a recording.
        frame_duration_ms (float): Duration of each audio frame in milliseconds.
        logger (logging.Logger): Logger for this class.
    """
    
    def __init__(self, 
                 energy_threshold: float = None,
                 silence_threshold: float = None,
                 min_speaking_time: float = None,
                 min_silence_time: float = None,
                 max_speaking_time: float = None,
                 frame_duration_ms: float = None):
        """
        Initialize a new VoiceActivityDetector.
        
        Args:
            energy_threshold: Threshold for energy-based voice detection.
            silence_threshold: Energy level below which audio is considered silence.
            min_speaking_time: Minimum duration of speech to be considered a valid segment.
            min_silence_time: Minimum duration of silence to finish recording.
            max_speaking_time: Maximum allowed duration for a recording.
            frame_duration_ms: Duration of each audio frame in milliseconds.
        """
        audio_config = default_config.audio
        
        self.energy_threshold = energy_threshold if energy_threshold is not None else audio_config.energy_threshold
        self.silence_threshold = silence_threshold if silence_threshold is not None else audio_config.silence_threshold
        self.min_speaking_time = min_speaking_time if min_speaking_time is not None else audio_config.min_speaking_time
        self.min_silence_time = min_silence_time if min_silence_time is not None else audio_config.min_silence_time
        self.max_speaking_time = max_speaking_time if max_speaking_time is not None else audio_config.max_speaking_time
        self.frame_duration_ms = frame_duration_ms if frame_duration_ms is not None else audio_config.frame_duration_ms
        
        self.logger = logging.getLogger(__name__)
    
    def is_speech(self, audio_data: bytes, audio_format: int, channels: int) -> Tuple[bool, float]:
        """
        Determine if the audio data contains speech based on energy levels.
        
        Args:
            audio_data: Raw audio data bytes.
            audio_format: Audio format (e.g., pyaudio.paInt16).
            channels: Number of audio channels.
            
        Returns:
            tuple: (is_speech, energy) where is_speech is a boolean indicating
                   if speech was detected, and energy is the calculated energy level.
        """
        # Convert audio bytes to NumPy array
        if audio_format == pyaudio.paInt16:
            numpy_data = np.frombuffer(audio_data, dtype=np.int16)
        else:
            self.logger.warning(f"Unsupported audio format: {audio_format}, treating as int16")
            numpy_data = np.frombuffer(audio_data, dtype=np.int16)
        
        # For multi-channel audio, average the channels
        if channels > 1:
            numpy_data = numpy_data.reshape(-1, channels)
            numpy_data = np.mean(numpy_data, axis=1)
        
        # Calculate energy (RMS of the signal)
        energy = np.sqrt(np.mean(numpy_data.astype(np.float32)**2))
        
        # Detect speech based on energy threshold
        is_speech = energy > self.energy_threshold
        is_silence = energy < self.silence_threshold
        
        return is_speech, is_silence, energy


class AudioRecorder(AudioRecorderInterface):
    """
    Records audio from a microphone when voice activity is detected.
    Implements the AudioRecorderInterface.
    
    Attributes:
        audio_provider (AudioDataProvider): Provider of audio data.
        vad (VoiceActivityDetector): Voice activity detector.
        output_dir (str): Directory to save recorded audio files.
        recording_started (bool): Flag indicating if recording is in progress.
        frames (List[bytes]): List of recorded audio frames.
        speaking_start_time (float): Time when speaking started.
        last_speech_time (float): Time of the last detected speech.
        silence_start_time (float): Time when silence started.
        current_file_path (str): Path to the current recording file.
        recording_thread (threading.Thread): Thread for recording.
        lock (threading.Lock): Lock for thread-safe operations.
        logger (logging.Logger): Logger for this class.
    """
    
    def __init__(self, 
                 audio_provider: Optional[AudioDataProvider] = None,
                 vad: Optional[VoiceActivityDetector] = None,
                 output_dir: Optional[str] = None):
        """
        Initialize a new AudioRecorder.
        
        Args:
            audio_provider: Provider of audio data. If None, creates a new one.
            vad: Voice activity detector. If None, creates a new one.
            output_dir: Directory to save recorded audio files. If None, uses default from config.
        """
        self.audio_provider = audio_provider or AudioDataProvider()
        self.vad = vad or VoiceActivityDetector()
        self.output_dir = output_dir or default_config.paths.output_dir
        
        # Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Recording state
        self.recording_started = False
        self.frames: List[bytes] = []
        self.speaking_start_time = 0.0
        self.last_speech_time = 0.0
        self.silence_start_time = 0.0
        self.current_file_path: Optional[str] = None
        
        # Thread management
        self.recording_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def perform_recording(self) -> Optional[str]:
        """
        Start the recording process.
        
        Returns:
            str or None: The path to the recorded audio file, or None if no file was recorded.
        """
        with self.lock:
            if self.recording_started:
                self.logger.warning("Recording already in progress")
                return None
            
            # Reset recording state
            self._reset_recording_state()
            
            # Start the audio stream
            if not self.audio_provider.start_stream():
                self.logger.error("Failed to start audio stream")
                return None
            
            # Start recording in a new thread
            self.recording_thread = thread_manager.create_daemon_thread(
                target=self._recording_loop,
                name="AudioRecordingThread"
            )
            self.recording_thread.start()
            
            # Wait for recording to complete
            self.recording_thread.join()
            
            # Return the path to the recorded file
            if self.current_file_path and os.path.exists(self.current_file_path):
                self.logger.info(f"Recording completed: {self.current_file_path}")
                return self.current_file_path
            
            self.logger.warning("No valid recording was made")
            return None
    
    def _recording_loop(self) -> None:
        """
        Main recording loop that records audio when speech is detected.
        """
        self.recording_started = True
        start_time = time.time()
        
        try:
            while self.recording_started and not thread_manager.is_shutdown_requested():
                # Read audio data
                audio_data = self.audio_provider.read_audio()
                if not audio_data:
                    continue
                
                # Add frame to the buffer
                with self.lock:
                    self.frames.append(audio_data)
                
                # Check for voice activity
                is_speech, is_silence, energy = self.vad.is_speech(
                    audio_data, 
                    self.audio_provider.audio_format,
                    self.audio_provider.channels
                )
                
                current_time = time.time()
                
                # Handle speech detection
                if is_speech:
                    # If this is the first speech detected, set the start time
                    if self.speaking_start_time == 0:
                        self.speaking_start_time = current_time
                    
                    # Update the last speech time
                    self.last_speech_time = current_time
                    self.silence_start_time = 0  # Reset silence timer
                    
                    # Log speech detection with energy level
                    self.logger.debug(f"Speech detected: Energy = {energy:.2f}")
                
                # Handle silence detection
                elif is_silence and self.speaking_start_time > 0:
                    # If this is the first silence after speech, set the silence start time
                    if self.silence_start_time == 0:
                        self.silence_start_time = current_time
                    
                    # Check if we've had enough silence to stop recording
                    silence_duration = current_time - self.silence_start_time
                    if silence_duration >= self.vad.min_silence_time:
                        self.logger.debug(f"Sufficient silence detected ({silence_duration:.2f}s), stopping recording")
                        break
                
                # Check if we've exceeded the maximum recording time
                if self.speaking_start_time > 0:
                    recording_duration = current_time - self.speaking_start_time
                    if recording_duration >= self.vad.max_speaking_time:
                        self.logger.debug(f"Maximum recording time reached ({recording_duration:.2f}s), stopping recording")
                        break
                
                # Check if we've been waiting for speech for too long
                if self.speaking_start_time == 0 and current_time - start_time > 10:
                    self.logger.debug("No speech detected within 10 seconds, stopping recording")
                    break
            
            # After the loop, check if we have a valid recording
            self._finalize_recording()
            
        except Exception as e:
            self.logger.error(f"Error in recording loop: {e}")
        finally:
            self.recording_started = False
            self.audio_provider.stop_stream()
    
    def _finalize_recording(self) -> None:
        """
        Finalize the recording process by checking if it's valid and saving it.
        """
        # Check if we have a valid recording
        if self.speaking_start_time == 0:
            self.logger.debug("No speech detected during recording")
            return
        
        # Check if the recording meets the minimum duration
        if self.last_speech_time - self.speaking_start_time < self.vad.min_speaking_time:
            self.logger.debug(f"Recording too short ({self.last_speech_time - self.speaking_start_time:.2f}s), discarding")
            return
        
        # Save the recording
        try:
            self._save_recording()
        except Exception as e:
            self.logger.error(f"Failed to save recording: {e}")
    
    def _save_recording(self) -> None:
        """
        Save the recorded audio to a WAV file.
        """
        if not self.frames:
            self.logger.warning("No frames to save")
            return
        
        # Generate unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        self.current_file_path = os.path.join(self.output_dir, filename)
        
        # Save as WAV file
        try:
            with wave.open(self.current_file_path, 'wb') as wave_file:
                wave_file.setnchannels(self.audio_provider.channels)
                wave_file.setsampwidth(self.audio_provider.get_sample_size())
                wave_file.setframerate(self.audio_provider.rate)
                wave_file.writeframes(b''.join(self.frames))
            
            self.logger.info(f"Recording saved to {self.current_file_path}")
        except Exception as e:
            self.logger.error(f"Error saving recording: {e}")
            self.current_file_path = None
    
    def _reset_recording_state(self) -> None:
        """Reset the internal recording state."""
        self.frames = []
        self.speaking_start_time = 0.0
        self.last_speech_time = 0.0
        self.silence_start_time = 0.0
        self.current_file_path = None
    
    def cleanup(self) -> None:
        """Clean up resources used by the audio recorder."""
        with self.lock:
            self.recording_started = False
            
            if self.audio_provider:
                self.audio_provider.stop_stream()
            
            # Reset recording state
            self._reset_recording_state()
            
            self.logger.debug("Audio recorder resources cleaned up")
    
    def __del__(self):
        """Ensure cleanup when the object is garbage collected."""
        self.cleanup()


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    load_dotenv()

    # Set up the audio recorder
    recorder = AudioRecorder()

    # Start the recording process
    recorder.perform_recording()

    # Clean up
    recorder.cleanup()
