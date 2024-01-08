#!/usr/bin/env python3
import collections
import logging
import os
import wave

import pvcobra
import pyaudio
import numpy as np
import threading

from dotenv import load_dotenv


# Audio Data Provider Class
class AudioDataProvider:
    def __init__(self, audio_format=pyaudio.paInt16, channels=1, rate=16000, frames_per_buffer=512):
        self.audio_format = audio_format
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.stream = None
        self.py_audio = pyaudio.PyAudio()

    def start_stream(self):
        self.stream = self.py_audio.open(
            format=self.audio_format,
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
    def __init__(self, output_directory, access_key=None):
        self.logger = logging.getLogger(__name__)
        self.py_audio = pyaudio.PyAudio()
        self.access_key = access_key or os.environ.get('PICOVOICE_APIKEY')
        if not self.access_key:
            raise ValueError("Cobra access key must be provided or set as an environment variable 'PICOVOICE_APIKEY'")
        self.vad_engine = self.cobra_handle = pvcobra.create(access_key=self.access_key)
        self.output_directory = output_directory
        self.inactivity_frames = 0
        self.is_recording = False
        self.recording = False
        self.frames_to_save = []
        self.frames = []
        self.lock = threading.Lock()
        self.recording_thread = None
        self.BUFFER_LENGTH = 2  # The size of the internal circular buffer in seconds.
        self.audio_buffer = collections.deque(
            maxlen=self.BUFFER_LENGTH * self.cobra_handle.sample_rate // self.cobra_handle.frame_length)
        self.VOICE_THRESHOLD = 0.8  # Threshold for voice activity detection
        self.SILENCE_LIMIT = 2  # Silence limit in seconds.
        self.INACTIVITY_LIMIT = 2  # Inactivity limit in seconds.
        self.MIN_RECORDING_LENGTH = 3  # Minimum length for recording to be saved (seconds)
        self.audio_data_provider = None

    def start_recording(self, audio_data_provider):
        self.audio_data_provider = audio_data_provider
        self.audio_data_provider.start_stream()
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self.record_loop, args=(audio_data_provider,))
        self.recording_thread.start()
        self.logger.info("Recording started.")

    def record_loop(self, audio_data_provider):
        silent_frames = 0
        while self.is_recording:
            frame = audio_data_provider.get_next_frame()
            self.process_frame(frame)
            if not self.recording:
                self.buffer_audio_frame(frame)
            else:
                voice_activity_detected = self.detect_voice_activity(frame)
                if voice_activity_detected:
                    self.inactivity_frames = 0
                    self.frames_to_save.append(frame)
                else:
                    self.inactivity_frames += 1
                    silent_frames += 1
                    self.frames_to_save.append(frame)
                    if self.inactivity_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate > self.INACTIVITY_LIMIT:
                        self.logger.info("No voice detected for a while. Exiting...")
                        self.finalize_recording()
                        break
                    if silent_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate > self.SILENCE_LIMIT:
                        recording_length = len(self.frames_to_save) * self.cobra_handle.frame_length / self.cobra_handle.sample_rate
                        if recording_length >= self.MIN_RECORDING_LENGTH:
                            self.save_to_wav_file(self.frames_to_save)
                            self.logger.info(f"Recording of {recording_length:.2f} seconds saved.")
                            self.finalize_recording()
                            break

    def process_frame(self, frame):
        if frame is not None:
            voice_activity_detected = self.detect_voice_activity(frame)
            self.manage_recording_state(frame, voice_activity_detected)

    def detect_voice_activity(self, frame):
        audio_frame = np.frombuffer(frame, dtype=np.int16)
        voice_probability = self.vad_engine.process(audio_frame)
        return voice_probability > self.VOICE_THRESHOLD

    def manage_recording_state(self, frame, voice_activity_detected):
        with self.lock:
            if voice_activity_detected:
                self.inactivity_frames = 0
                if not self.is_recording:
                    self.start_new_recording()
                self.frames_to_save.append(frame)
            else:
                self.buffer_audio_frame(frame)
                self.inactivity_frames += 1
                if self.is_recording:
                    self.frames_to_save.append(frame)
                    if (
                            self.inactivity_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate >
                            self.INACTIVITY_LIMIT):
                        self.finalize_recording()

    def start_new_recording(self):
        self.recording = True
        self.frames_to_save = list(self.audio_buffer)  # Collect buffered audio when voice is detected
        self.logger.info("Voice Detected - Starting Recording")

    def buffer_audio_frame(self, frame):
        if len(self.audio_buffer) == self.audio_buffer.maxlen:
            self.audio_buffer.popleft()
        self.audio_buffer.append(frame)

    def check_inactivity_duration(self):
        if (
                self.inactivity_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate >
                self.INACTIVITY_LIMIT):
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

    def cleanup(self):
        """
        Clean up the processor by deleting the Koala handle.
        """
        self.vad_engine.delete()


if __name__ == '__main__':
    # dotenv from load_dotenv
    logging.basicConfig(level=logging.DEBUG)
    load_dotenv()
    audio_data_provider = AudioDataProvider()
    audio_data_provider.start_stream()
    audio_recorder = AudioRecorder(output_directory='Wav_MP3')
    audio_recorder.start_recording(audio_data_provider)
    input("Press Enter to stop recording...")
    audio_recorder.stop_recording()
