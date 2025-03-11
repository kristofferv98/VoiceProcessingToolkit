#!/usr/bin/env python3
"""
Unified audio management module that handles both streaming and recording.
This module replaces both AudioStream and AudioDataProvider with a single AudioManager class.
"""

import logging
import pyaudio
import threading
import wave
import os
from typing import Optional, List, Dict, Any, Tuple, Union
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class AudioManager:
    """
    Unified audio management class handling both streaming and recording.
    This replaces both AudioStream and AudioDataProvider with a single class.
    """
    
    def __init__(
        self,
        rate: int = 16000,
        channels: int = 1,
        audio_format: int = pyaudio.paInt16,
        frames_per_buffer: int = 512,
        buffer_duration: float = 3.0  # Duration of rolling buffer in seconds
    ):
        """
        Initialize the AudioManager.
        
        Args:
            rate: Sample rate for audio recording (Hz)
            channels: Number of audio channels
            audio_format: PyAudio format (e.g. pyaudio.paInt16)
            frames_per_buffer: Number of frames per buffer
            buffer_duration: Duration of the rolling buffer in seconds
        """
        self.rate = rate
        self.channels = channels
        self.audio_format = audio_format
        self.frames_per_buffer = frames_per_buffer
        
        # Rolling buffer for wake word context
        self._buffer_size = int(rate * buffer_duration * channels)
        self._rolling_buffer = bytearray(self._buffer_size * 2)  # 2 bytes per sample for 16-bit audio
        self._buffer_index = 0
        
        # PyAudio setup
        self._py_audio = pyaudio.PyAudio()
        self._stream = None
        self._is_streaming = False
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Status tracking
        self._is_recording = False
        self._recording_frames = []
        
        logger.debug(f"AudioManager initialized: rate={rate}, channels={channels}, format={audio_format}")
    
    def start_stream(self) -> bool:
        """
        Start the audio stream.
        
        Returns:
            bool: True if the stream was started successfully, False otherwise
        """
        with self._lock:
            if self._is_streaming:
                logger.debug("Stream is already running")
                return True
            
            try:
                self._stream = self._py_audio.open(
                    format=self.audio_format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.frames_per_buffer
                )
                self._is_streaming = True
                logger.debug("Audio stream started successfully")
                return True
            except Exception as e:
                logger.error(f"Error starting audio stream: {e}")
                return False
    
    def read_audio(self, exception_on_overflow=False) -> Optional[bytes]:
        """
        Read audio data from the stream.
        
        Args:
            exception_on_overflow: Whether to raise an exception on buffer overflow
            
        Returns:
            bytes or None: Audio data if read successfully, None if the stream is not active
        """
        with self._lock:
            if not self._is_streaming or self._stream is None:
                return None
            
            try:
                data = self._stream.read(self.frames_per_buffer, exception_on_overflow)
                self._update_rolling_buffer(data)
                
                # Add to recording if we're currently recording
                if self._is_recording:
                    self._recording_frames.append(data)
                
                return data
            except Exception as e:
                logger.error(f"Error reading audio data: {e}")
                return None
    
    def _update_rolling_buffer(self, data: bytes) -> None:
        """
        Update the rolling buffer with new audio data.
        
        Args:
            data: New audio data to add to the buffer
        """
        data_len = len(data)
        
        # If data won't fit in the remaining buffer space, wrap around
        if self._buffer_index + data_len > len(self._rolling_buffer):
            # Calculate remaining space
            remaining = len(self._rolling_buffer) - self._buffer_index
            
            # Copy first part to end of buffer
            self._rolling_buffer[self._buffer_index:] = data[:remaining]
            
            # Copy second part to beginning of buffer
            self._rolling_buffer[:data_len - remaining] = data[remaining:]
            
            # Update buffer index
            self._buffer_index = data_len - remaining
        else:
            # Copy data to buffer
            self._rolling_buffer[self._buffer_index:self._buffer_index + data_len] = data
            
            # Update buffer index
            self._buffer_index = (self._buffer_index + data_len) % len(self._rolling_buffer)
    
    def get_buffer(self) -> bytes:
        """
        Get the current content of the rolling buffer.
        
        Returns:
            bytes: Current content of the rolling buffer
        """
        with self._lock:
            # Return buffer in chronological order
            return bytes(self._rolling_buffer[self._buffer_index:] + self._rolling_buffer[:self._buffer_index])
    
    def start_recording(self) -> None:
        """
        Start recording audio.
        """
        with self._lock:
            if self._is_recording:
                logger.warning("Already recording")
                return
            
            self._is_recording = True
            self._recording_frames = []
            logger.debug("Started recording")
    
    def stop_recording(self) -> List[bytes]:
        """
        Stop recording and return the recorded frames.
        
        Returns:
            List[bytes]: Recorded audio frames
        """
        with self._lock:
            if not self._is_recording:
                logger.warning("Not recording")
                return []
            
            frames = self._recording_frames
            self._is_recording = False
            self._recording_frames = []
            logger.debug(f"Stopped recording, captured {len(frames)} frames")
            return frames
    
    def save_recording(self, frames: List[bytes], output_path: str) -> bool:
        """
        Save recorded audio frames to a WAV file.
        
        Args:
            frames: List of audio frames to save
            output_path: Path to save the recording
            
        Returns:
            bool: True if the recording was saved successfully, False otherwise
        """
        if not frames:
            logger.warning("No frames to save")
            return False
        
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            with wave.open(output_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.get_sample_size())
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(frames))
            
            logger.info(f"Recording saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving recording: {e}")
            return False
    
    def get_sample_size(self) -> int:
        """
        Get the sample size in bytes for the current audio format.
        
        Returns:
            int: Sample size in bytes
        """
        return self._py_audio.get_sample_size(self.audio_format)
    
    def stop_stream(self) -> None:
        """
        Stop the audio stream.
        """
        with self._lock:
            if self._stream:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except Exception as e:
                    logger.error(f"Error stopping audio stream: {e}")
                finally:
                    self._stream = None
                    self._is_streaming = False
    
    def cleanup(self) -> None:
        """
        Clean up all resources used by the audio manager.
        """
        self.stop_stream()
        if self._py_audio:
            self._py_audio.terminate()
            self._py_audio = None
        logger.debug("AudioManager resources cleaned up")
    
    def __del__(self) -> None:
        """
        Ensure resources are properly cleaned up when the object is garbage collected.
        """
        self.cleanup()
    
    def __enter__(self):
        """Support for context manager pattern (with statement)."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context."""
        self.cleanup() 