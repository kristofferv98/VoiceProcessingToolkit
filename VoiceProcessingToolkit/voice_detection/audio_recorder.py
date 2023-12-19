import logging
import os
import wave
from collections.abc import Callable
from typing import List


class AudioRecorder:
    SILENCE_LIMIT = 2  # seconds
    MIN_RECORDING_LENGTH = 3  # seconds
    OUTPUT_DIRECTORY = 'MP3'

    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.frames_to_save = []
        self.is_recording = False
        self.silent_frames = 0

    @staticmethod
    def ensure_output_directory_exists():
        recordings_dir = os.path.join(os.getcwd(), AudioRecorder.OUTPUT_DIRECTORY)
        if not os.path.exists(recordings_dir):
            os.makedirs(recordings_dir)
            logging.info(f"Created directory {recordings_dir}")

    def handle_voice_activity(self, is_voice, frame):
        if is_voice:
            self.handle_voice_detected(frame)
        else:
            self.handle_silence_detected(frame)

    def handle_voice_detected(self, frame):
        if not self.is_recording:
            self.is_recording = True
            self.frames_to_save.clear()
            logging.info("Voice Detected - Starting Recording")
        self.frames_to_save.append(frame)
        self.silent_frames = 0

    def handle_silence_detected(self, frame):
        if self.is_recording:
            self.silent_frames += 1
            self.frames_to_save.append(frame)
            if self.silent_frames > self.SILENCE_LIMIT * 16000 / 1024:  # Example values for sample rate and frame
                # length
                self.finish_recording()

    def finish_recording(self):
        if len(self.frames_to_save) >= self.MIN_RECORDING_LENGTH * 16000 / 1024:
            file_path = self.prepare_file_path()
            self.save_to_wav_file(self.frames_to_save, file_path)
            if self.callback:
                self.callback(file_path)
        self.frames_to_save.clear()
        self.is_recording = False
        self.silent_frames = 0
        logging.info("Silence detected - Stopping Recording")

    def prepare_file_path(self) -> str:
        recordings_dir = os.path.join(os.getcwd(), AudioRecorder.OUTPUT_DIRECTORY)
        file_name = "VoiceProcessingToolkit/voice_detection/MP3/raw_output.wav"
        return os.path.join(recordings_dir, file_name)

    def save_to_wav_file(self, frames: List[bytes], file_path: str):
        if not frames:
            logging.warning("No frames to save to WAV file.")
            return

        try:
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # Assuming 16-bit audio
                wf.setframerate(16000)  # Example sample rate
                wf.writeframes(b''.join(frames))
            logging.info(f"Saved recording to {file_path}")
        except IOError as e:
            logging.error(f"Failed to save recording to {file_path}: {e}")

