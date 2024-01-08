#!/usr/bin/env python3
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

    def start_stream(self):
        self.stream = pyaudio.PyAudio().open(
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

# Cobra VAD Class
class CobraVAD:
    def __init__(self, access_key, frame_length, sample_rate):
        self.cobra_handle = None
        try:
            self.cobra_handle = pvcobra.create(access_key=access_key)
        except pvcobra.CobraError as e:
            print(f"Failed to initialize CobraVAD: {e}")
            raise
        self.frame_length = frame_length
        self.sample_rate = sample_rate

    def process(self, pcm):
        if len(pcm) != self.frame_length:
            raise ValueError("Invalid frame length. Expected %d but received %d" % (self.frame_length, len(pcm)))

        pcm_array = (c_short * len(pcm))(*pcm)  # Correct way to create a ctypes array from PCM data
        result = c_float()
        status = self.cobra_handle.process_func(self.cobra_handle._handle, pcm_array, byref(result))

        if status is not self.cobra_handle.PicovoiceStatuses.SUCCESS:
            # Raise an exception if processing fails
            raise self.cobra_handle._PICOVOICE_STATUS_TO_EXCEPTION[status](
                message='Processing failed',
                message_stack=self.cobra_handle._get_error_stack())
        return result.value

    def __del__(self):
        if hasattr(self, 'cobra_handle') and self.cobra_handle is not None:
            self.cobra_handle.delete()

# Audio Recorder Class
class AudioRecorder:
    def __init__(self, vad_engine, output_directory, min_recording_length=3):
        self.p = None
        self.MIN_RECORDING_LENGTH = min_recording_length
        self.cobra_handle = None
        self.vad_engine = vad_engine
        self.output_directory = output_directory
        self.min_recording_length = min_recording_length
        self.is_recording = False
        self.frames = []
        self.lock = threading.Lock()
        self.recording_thread = None

    def start_recording(self, audio_data_provider):
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self.record_loop, args=(audio_data_provider,))
        self.recording_thread.start()

    def record_loop(self, audio_data_provider):
        while self.is_recording:
            frame = audio_data_provider.get_next_frame()
            if frame is not None:
                voice_prob = self.vad_engine.process(np.frombuffer(frame, dtype=np.int16))
                if voice_prob > 0.5:  # Assuming 0.5 as the threshold for voice activity
                    with self.lock:
                        self.frames.append(frame)
                else:
                    if self.should_stop_recording():
                        self.is_recording = False
        self.save_to_wav_file(self.frames)

    def should_stop_recording(self):
        # Logic to determine if recording should stop
        pass

    def save_to_wav_file(self, frames):
        duration = len(frames) * self.vad_engine.frame_length / self.vad_engine.sample_rate
        if duration < self.MIN_RECORDING_LENGTH:
            return 'UNDER_MIN_LENGTH'

        recordings_dir = os.path.join(os.path.dirname(__file__), 'Wav_MP3')
        filename = os.path.join(recordings_dir, "recording.wav")

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.vad_engine.sample_rate)
            wf.writeframes(b''.join(frames))
        logging.info(f"Saved to {filename}")
        return 'SAVE'

    def stop_recording(self):
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()

def main():
    load_dotenv()
    api_key = os.getenv("PICOVOICE_APIKEY")

    # Example usage
    audio_data_provider = AudioDataProvider()
    FRAME_LENGTH = 1024
    SAMPLE_RATE = 16000
    # Example usage
    cobra_vad = CobraVAD(access_key=api_key, frame_length=FRAME_LENGTH, sample_rate=SAMPLE_RATE)
    audio_recorder = AudioRecorder(cobra_vad, "output_directory_path")

    # Start recording process
    audio_data_provider.start_stream()
    audio_recorder.start_recording(audio_data_provider)
