import logging
import os
import tempfile
import wave
from collections import deque
from typing import Optional, List

import numpy as np
import pvcobra
import pyaudio
from dotenv import load_dotenv

from VoiceProcessingToolkit.audio_processing.koala import KoalaAudioProcessor
from VoiceProcessingToolkit.transcription.whisper import WhisperTranscriber

logger = logging.getLogger(__name__)


class CobraVoiceRecorder:
    """
    CobraVoiceRecorder uses the Cobra VAD engine to record voice audio.
    This class provides methods to start and stop voice recording, process audio frames,
    save recordings to WAV files, and perform cleanup.
    """

    def __init__(self, access_key: Optional[str] = None) -> None:
        self.access_key = access_key or os.environ.get('PICOVOICE_APIKEY')
        if not self.access_key:
            raise ValueError("Cobra access key must be provided or set as an environment variable 'PICOVOICE_APIKEY'")
        self.cobra_handle = pvcobra.create(access_key=self.access_key)

        self.pyaudio_instance = pyaudio.PyAudio()
        try:
            self.stream = self.pyaudio_instance.open(format=pyaudio.paInt16, channels=1,
                                                     rate=self.cobra_handle.sample_rate,
                                                     input=True, frames_per_buffer=self.cobra_handle.frame_length)
        except Exception as e:
            logger.exception("Failed to initialize PyAudio stream: %s", e)
            raise
        self.audio_buffer = deque(maxlen=int(self.cobra_handle.sample_rate * 2 / self.cobra_handle.frame_length))
        self.koala_processor = KoalaAudioProcessor(access_key=self.access_key)
        self.file_check_thread = None
        self.stop_check = False

        # Configuration
        self.voice_threshold = 0.7
        self.silence_limit = 2
        self.inactivity_limit = 2
        self.min_recording_length = 3
        self.audio_buffer = deque(
            maxlen=2 * self.cobra_handle.sample_rate // self.cobra_handle.frame_length)

    def get_next_audio_frame(self) -> np.ndarray:
        logging.debug("CobraVoiceRecorder: Reading the next audio frame")
        frame = self.stream.read(self.cobra_handle.frame_length, exception_on_overflow=False)
        return np.frombuffer(frame, dtype=np.int16)

    def start_recording(self) -> Optional[str]:
        # Use a temporary directory if no output directory is provided
        # Create a temporary directory and manage its lifecycle manually
        temp_dir = tempfile.TemporaryDirectory()
        wav_mp3_directory = temp_dir.name
        file_path = os.path.join(wav_mp3_directory, "recorded_voice.wav")
        processed_file_path = os.path.join(wav_mp3_directory, "processed_voice.wav")

        recording = False
        silent_frames = 0
        inactivity_frames = 0
        frames_to_save = []

        try:
            while True:
                audio_frame = self.get_next_audio_frame()
                try:
                    voice_probability = self.cobra_handle.process(audio_frame)
                except pvcobra.CobraError as e:
                    logging.exception("Cobra processing error: %s", e)
                    raise
                except Exception as e:
                    logging.exception("Unexpected error during Cobra processing: %s", e)
                    raise

                if voice_probability > self.voice_threshold:
                    inactivity_frames = 0
                    silent_frames = 0
                    if not recording:
                        recording = True
                        frames_to_save = list(self.audio_buffer)  # Collect buffered audio when voice is detected
                        logging.info("Voice Detected - Starting Recording")
                    frames_to_save.append(audio_frame)
                else:
                    if len(self.audio_buffer) == self.audio_buffer.maxlen:
                        self.audio_buffer.popleft()
                    self.audio_buffer.append(audio_frame)
                    inactivity_frames += 1
                    if recording:
                        silent_frames += 1
                        frames_to_save.append(audio_frame)
                        if (
                                silent_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate >
                                self.silence_limit):
                            recording_length = len(
                                frames_to_save) * self.cobra_handle.frame_length / self.cobra_handle.sample_rate
                            if recording_length >= self.min_recording_length:
                                self.save_to_wav_file(frames_to_save, file_path)
                                self.koala_processor.process_audio(file_path, processed_file_path)
                                logging.info(f"Recording of {recording_length:.2f} seconds saved to {file_path}.")
                                if processed_file_path:
                                    logging.info(f"Audio processed and saved as {processed_file_path}.")
                                    transcription_result = self.transcribe_audio(processed_file_path)
                                else:
                                    logging.error(f"Error: Processed file could not be created.")
                                    transcription_result = None
                                if transcription_result is not None:
                                    return transcription_result
                                else:
                                    return "SAVE"
                            else:
                                frames_to_save = []
                                recording = False
                                logging.info(
                                    f"Recording of {recording_length:.2f} seconds is under the minimum length. Not "
                                    f"saved.")

                if (
                        inactivity_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate >
                        self.inactivity_limit):
                    logging.info("No voice detected for a while. Exiting...")
                    return 'NO_VOICE_EXIT'
        except Exception as e:
            logging.exception("An error occurred during recording: %s", e)
        finally:
            self.cleanup()
            temp_dir.cleanup()  # Clean up the temporary directory

    def save_to_wav_file(self, frames: List[np.ndarray], file_path: str) -> None:
        logging.debug("CobraVoiceRecorder: Saving frames to WAV file: %s", file_path)
        """
        Saves the recorded frames to a WAV file.

        Args:
            frames (list): List of audio frames to save.
            file_path (str): Path to the output WAV file.
        """
        if not file_path:
            logging.error("No file path specified for saving the WAV file.")
            return

        try:
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.pyaudio_instance.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.cobra_handle.sample_rate)
                wf.writeframes(b''.join(frames))
            logging.info(f"Saved recording to {file_path}")
        except Exception as e:
            logging.error(f"Failed to save recording to {file_path}: {e}")

    def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        logging.debug("CobraVoiceRecorder: Starting transcription for audio file: %s", audio_file_path)
        """
        Transcribes the recorded audio file using the WhisperTranscriber.

        Args:
            audio_file_path (str): Path to the recorded audio file.

        Returns:
            str: The transcription result or None if transcription fails.
        """
        transcriber = WhisperTranscriber()
        return transcriber.transcribe_audio(audio_file_path)

    def cleanup(self) -> None:
        self.stream.stop_stream()
        self.stream.close()
        self.cobra_handle.delete()


if __name__ == '__main__':
    load_dotenv()
    # The basicConfig call is removed because logging is now configured above
    recorder = CobraVoiceRecorder(access_key=os.getenv('PICOVOICE_APIKEY'))
    result = recorder.start_recording()
    print(f"Recording Result: {result}")
