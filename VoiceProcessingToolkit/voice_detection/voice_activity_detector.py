import collections
import logging
import os
import wave
from datetime import datetime
from typing import Callable, List

import numpy as np
import pyaudio

from .audio_data_provider import AudioDataProvider

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    VOICE_THRESHOLD = 0.8
    SILENCE_LIMIT = 2  # seconds
    BUFFER_LENGTH = 2  # seconds
    INACTIVITY_LIMIT = 2  # seconds
    MIN_RECORDING_LENGTH = 3  # seconds
    OUTPUT_DIRECTORY = 'MP3'  # Output directory for recordings

    def __init__(self, vad_engine, audio_data_provider: AudioDataProvider,
                 voice_activity_handler: Callable[[str], None]):
        self.vad_engine = vad_engine
        self.audio_data_provider = audio_data_provider
        self.voice_activity_handler = voice_activity_handler
        self.silent_frame_buffer = collections.deque(
            maxlen=self.BUFFER_LENGTH * self.vad_engine.sample_rate // self.vad_engine.frame_length
        )

    def ensure_output_directory_exists(self):
        recordings_dir = os.path.join(os.getcwd(), self.OUTPUT_DIRECTORY)
        os.makedirs(recordings_dir, exist_ok=True)

    def prepare_file_path(self) -> str:
        self.ensure_output_directory_exists()
        filename = datetime.now().strftime("output_%Y%m%d_%H%M%S.wav")
        return os.path.join(os.getcwd(), self.OUTPUT_DIRECTORY, filename)

    def start_recording(self, callback: Callable[[str], None]) -> None:
        frames_to_save = []
        recording = False
        silent_frames = 0
        inactivity_frames = 0

        while True:
            frame = self.audio_data_provider.get_audio_frame()
            is_voice = self.vad_engine.process(frame) > self.VOICE_THRESHOLD

            if is_voice:
                recording = self.handle_voice_detected(frame, frames_to_save)
            else:
                recording, silent_frames = self.handle_silence(frame, frames_to_save, recording, silent_frames,
                                                               callback)

            inactivity_frames = self.handle_inactivity(inactivity_frames)

            if inactivity_frames * self.vad_engine.frame_length / self.vad_engine.sample_rate > self.INACTIVITY_LIMIT:
                logger.info("Inactivity detected - Exiting")
                break

    def handle_voice_detected(self, frame: np.ndarray, frames_to_save: List[np.ndarray]) -> bool:
        logger.info("Voice Detected - Starting Recording")
        frames_to_save.append(frame)
        return True

    def handle_silence(self, frame: np.ndarray, frames_to_save: List[np.ndarray], recording: bool, silent_frames: int,
                       callback: Callable[[str], None]) -> (bool, int):
        if recording:
            silent_frames += 1
            frames_to_save.append(frame)
            if silent_frames > self.SILENCE_LIMIT * self.vad_engine.sample_rate / self.vad_engine.frame_length:
                self.finish_recording(frames_to_save, callback)
                return False, 0
        return recording, silent_frames

    def handle_inactivity(self, inactivity_frames: int) -> int:
        if not any(self.vad_engine.process(frame) for frame in self.silent_frame_buffer):
            inactivity_frames += 1
        return inactivity_frames

    def finish_recording(self, frames_to_save: List[np.ndarray], callback: Callable[[str], None]):
        if (len(frames_to_save) >= self.MIN_RECORDING_LENGTH * self.vad_engine.sample_rate /
                self.vad_engine.frame_length):
            file_path = self.prepare_file_path()
            self.save_to_wav_file(frames_to_save, file_path)
            if callback:
                callback(file_path)
            logger.info(f"Recording finished and saved to {file_path}")
        else:
            logger.info("Silence detected but recording length was too short. Not saved.")

    def save_to_wav_file(self, frames: List[np.ndarray], file_path: str):
        if not frames:
            logger.warning("No frames to save to WAV file.")
            return

        try:
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.vad_engine.sample_rate)
                wf.writeframes(b''.join(frames))
            logger.info(f"Saved recording to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save recording: {e}")

    def cleanup(self):
        self.audio_data_provider.cleanup()
        self.vad_engine.delete()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def __del__(self):
        self.cleanup()


