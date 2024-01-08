#!/usr/bin/env python3
import collections
import logging
import os
import wave

import pyaudio
import numpy as np
import threading
from ctypes import c_float, c_short, byref
import pvcobra
from dotenv import load_dotenv


# Audio Data Provider Class
class AudioDataProvider:
    def __init__(self, format=pyaudio.paInt16, channels=1, rate=16000, frames_per_buffer=1024):
        self.format = format
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.stream = None
        self.py_audio = pyaudio.PyAudio()

    def start_stream(self):
        self.stream = self.py_audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer
        )

    def get_next_frame(self):
        return self.stream.read(self.frames_per_buffer, exception_on_overflow=False)

    def stop_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.py_audio.terminate()

# Cobra VAD Class
class CobraVAD:
    def __init__(self, config):
        self.cobra_handle = None
        self.logger = logging.getLogger(__name__)
        try:
            self.cobra_handle = pvcobra.create(access_key=config.access_key)
            self.logger.info("CobraVAD initialized successfully.")
        except pvcobra.CobraError as e:
            self.logger.error(f"Failed to initialize CobraVAD: {e}")
            raise
        self.frame_length = config.frame_length
        self.sample_rate = config.sample_rate

    def process(self, pcm):
        if len(pcm) != self.frame_length:
            error_message = f"Invalid frame length. Expected {self.frame_length} but received {len(pcm)}"
            self.logger.error(error_message)
            raise ValueError(error_message)

        pcm_array = (c_short * len(pcm))(*pcm)  # Correct way to create a ctypes array from PCM data
        result = c_float()
        status = self.cobra_handle.process_func(self.cobra_handle._handle, pcm_array, byref(result))

        if status is not self.cobra_handle.PicovoiceStatuses.SUCCESS:
            # Raise an exception if processing fails
            error_message = 'Processing failed'
            self.logger.error(f"{error_message}: {self.cobra_handle._get_error_stack()}")
            raise self.cobra_handle._PICOVOICE_STATUS_TO_EXCEPTION[status](message=error_message,
                                                                          message_stack=self.cobra_handle._get_error_stack())
        return result.value

    def __del__(self):
        if hasattr(self, 'cobra_handle') and self.cobra_handle is not None:
            try:
                self.cobra_handle.delete()
                self.logger.info("CobraVAD resources released successfully.")
            except Exception as e:
                self.logger.error(f"Failed to release CobraVAD resources: {e}")

# Audio Recorder Class
class AudioRecorder:
    def __init__(self, vad_engine, output_directory, min_recording_length=3):
        self.logger = logging.getLogger(__name__)
        self.py_audio = pyaudio.PyAudio()
        self.MIN_RECORDING_LENGTH = 3
        self.cobra_handle = None
        self.cobra_handle = vad_engine
        self.vad_engine = vad_engine
        self.output_directory = output_directory
        self.min_recording_length = min_recording_length
        self.is_recording = False
        self.frames = []
        self.lock = threading.Lock()
        self.recording_thread = None
        self.BUFFER_LENGTH = 3  # Length of the buffer in seconds
        self.audio_buffer = collections.deque(
            maxlen=self.BUFFER_LENGTH * self.vad_engine.sample_rate // self.vad_engine.frame_length)
        self.VOICE_THRESHOLD = 0.5  # Threshold for voice activity
        self.SILENCE_LIMIT = 3  # Duration of silence in seconds to stop recording

    def start_recording(self, audio_data_provider):
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self.record_loop, args=(audio_data_provider,))
        self.recording_thread.start()
        self.logger.info("Recording started.")

    def record_loop(self, audio_data_provider):
        recording = False
        frames_to_save = []
        inactivity_frames = 0
        silent_frames = 0
        while self.is_recording:
            frame = audio_data_provider.get_next_frame()
            if frame is not None:
                audio_frame = np.frombuffer(frame, dtype=np.int16)
                voice_probability = self.vad_engine.process(audio_frame)

                if voice_probability > self.VOICE_THRESHOLD:
                    inactivity_frames = 0
                    silent_frames = 0
                    if not recording:
                        recording = True
                        frames_to_save = list(self.audio_buffer)  # Collect buffered audio when voice is detected
                        self.logger.info("Voice Detected - Starting Recording")
                    frames_to_save.append(frame)
                else:
                    if len(self.audio_buffer) == self.audio_buffer.maxlen:
                        self.audio_buffer.popleft()
                    self.audio_buffer.append(frame)
                    inactivity_frames += 1
                    if recording:
                        silent_frames += 1
                        frames_to_save.append(frame)
                        if (silent_frames * self.vad_engine.frame_length / self.vad_engine.sample_rate > self.SILENCE_LIMIT):
                            recording_length = len(frames_to_save) * self.vad_engine.frame_length / self.vad_engine.sample_rate
                            if recording_length >= self.MIN_RECORDING_LENGTH:
                                self.save_to_wav_file(frames_to_save)
                                self.logger.info(f"Recording of {recording_length:.2f} seconds saved.")
                                return "SAVE"
                            else:
                                frames_to_save = []
                                recording = False
                                self.logger.info(f"Recording of {recording_length:.2f} seconds is under the minimum length. Not saved.")
        if self.frames:
            self.save_to_wav_file(self.frames)

    def should_stop_recording(self):
        # Logic to determine if recording should stop
        pass

    def save_to_wav_file(self, frames):
        duration = len(frames) * self.cobra_handle.frame_length / self.cobra_handle.sample_rate
        if duration < self.MIN_RECORDING_LENGTH:
            return 'UNDER_MIN_LENGTH'

        recordings_dir = os.path.join(os.path.dirname(__file__), 'Wav_MP3')
        filename = os.path.join(recordings_dir, "recording.wav")

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.py_audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.cobra_handle.sample_rate)
            wf.writeframes(b''.join(frames))
        logging.info(f"Saved to {filename}")
        return 'SAVE'


    def stop_recording(self):
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
            self.py_audio.terminate()
        self.logger.info("Recording stopped.")

