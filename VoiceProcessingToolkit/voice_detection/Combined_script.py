import os
import threading
import wave
from ctypes import c_float, c_short, byref

import numpy as np
import pvcobra
import pyaudio


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

    def get_next_audio_frame(self, audio_data_provider):
        return audio_data_provider.get_next_frame()

    def record_loop(self, audio_data_provider):
        while self.is_recording:
            frame = self.get_next_audio_frame(audio_data_provider)
            if frame is not None:
                voice_prob = self.vad_engine.process(np.frombuffer(frame, dtype=np.int16))
                if voice_prob > 0.5:  # Assuming 0.5 as the threshold for voice activity
                    with self.lock:
                        self.frames.append(frame)
                else:
                    if self.should_stop_recording():
                        self.is_recording = False
        self.save_to_wav_file(self.frames)

    def save_to_wav_file(self, frames):
        file_path = os.path.join(self.output_directory, "recording.wav")
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            wav_file.setframerate(self.vad_engine.sample_rate)
            wav_file.writeframes(b''.join(frames))

    def stop_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()


class CobraVAD:
    def __init__(self, access_key, frame_length, sample_rate):
        self.cobra_handle = pvcobra.create(access_key=access_key)
        self.frame_length = frame_length
        self.sample_rate = sample_rate

    def process(self, pcm):
        if len(pcm) != self.frame_length:
            raise ValueError("Invalid frame length. Expected %d but received %d" % (self.frame_length, len(pcm)))

        result = c_float()
        status = self.cobra_handle.process_func(self.cobra_handle._handle, (c_short * len(pcm))(*pcm), byref(result))
        if status is not self.cobra_handle.PicovoiceStatuses.SUCCESS:
            raise self.cobra_handle._PICOVOICE_STATUS_TO_EXCEPTION[status](
                message='Processing failed',
                message_stack=self.cobra_handle._get_error_stack())

        return result.value

    def __del__(self):
        if self.cobra_handle is not None:
            self.cobra_handle.delete()

            raise ValueError("Invalid frame length. Expected %d but received %d" % (self.frame_length, len(pcm)))

        result = c_float()
        status = self.cobra_handle.process(pcm, byref(result))
        if status != pvcobra.PicovoiceStatus.SUCCESS:
            raise Exception('Cobra VAD processing failed')

        return result.value

    def __del__(self):
        if self.cobra_handle is not None:
            self.cobra_handle.delete()


class AudioRecorder:
    def __init__(self, vad_engine, output_directory, min_recording_length=3):
        self.vad_engine = vad_engine
        self.output_directory = output_directory
        self.min_recording_length = min_recording_length
        self.is_recording = False
        self.frames = []
        self.lock = threading.Lock()
        self.recording_thread = None

    def start_recording(self):
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self.record_loop)
        self.recording_thread.start()

    def record_loop(self):
        while self.is_recording:
            frame = self.get_next_audio_frame()
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

    def get_next_audio_frame(self):
        # Logic to get the next audio frame
        pass

    def save_to_wav_file(self, frames):
        # Logic to save frames to a WAV file
        pass

    def stop_recording(self):
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()


audio_data_provider = AudioDataProvider()
cobra_vad = CobraVAD(access_key="YOUR_ACCESS_KEY", frame_length=FRAME_LENGTH, sample_rate=SAMPLE_RATE)
audio_recorder = AudioRecorder(cobra_vad, "output_directory_path")

# Start recording process
audio_data_provider.start_stream()
audio_recorder.start_recording(audio_data_provider)
