#!/usr/bin/env python3
import collections
import logging
import os
import wave

import pyaudio
import numpy as np
import threading



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
        self.recording = False
        self.frames_to_save = []
        self.silent_frames = 0
        while self.is_recording:
            frame = audio_data_provider.get_next_frame()
            self.process_frame(frame)
            if self.should_stop_recording():
                self.finalize_recording()
                break
            self.check_inactivity_duration()

    def process_frame(self, frame):
        if frame is not None:
            voice_activity_detected = self.detect_voice_activity(frame)
            self.manage_recording_state(frame, voice_activity_detected)

    def detect_voice_activity(self, frame):
        audio_frame = np.frombuffer(frame, dtype=np.int16)
        voice_probability = self.vad_engine.process(audio_frame)
        return voice_probability > self.VOICE_THRESHOLD

    def manage_recording_state(self, frame, voice_activity_detected):
        if voice_activity_detected:
            self.inactivity_frames = 0
            if not self.recording:
                self.start_new_recording(frame)
            self.frames_to_save.append(frame)
        else:
            self.buffer_audio_frame(frame)
            self.inactivity_frames += 1
            if self.recording:
                self.frames_to_save.append(frame)
                self.check_silence_duration()

    def start_new_recording(self, frame):
        self.recording = True
        self.frames_to_save = list(self.audio_buffer)  # Collect buffered audio when voice is detected
        self.logger.info("Voice Detected - Starting Recording")

    def buffer_audio_frame(self, frame):
        if len(self.audio_buffer) == self.audio_buffer.maxlen:
            self.audio_buffer.popleft()
        self.audio_buffer.append(frame)

    def check_inactivity_duration(self):
        if (self.inactivity_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate > self.INACTIVITY_LIMIT):
            self.finalize_recording()

    def finalize_recording(self):
        recording_length = len(self.frames_to_save) * self.vad_engine.frame_length / self.vad_engine.sample_rate
        if recording_length >= self.MIN_RECORDING_LENGTH:
            self.save_to_wav_file(self.frames_to_save)
            self.logger.info(f"Recording of {recording_length:.2f} seconds saved.")
        else:
            self.logger.info(f"Recording of {recording_length:.2f} seconds is under the minimum length. Not saved.")
        self.recording = False
        self.frames_to_save = []

    def should_stop_recording(self):
        # Logic to determine if recording should stop
        return not self.is_recording


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

