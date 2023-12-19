# === IMPORTS SECTION ===
import logging
from typing import List

import numpy as np
import pyaudio
import pvcobra
from VoiceProcessingToolkit.audio_processing.koala import KoalaAudioProcessor

from .audio_data_provider import AudioDataProvider

logger = logging.getLogger(__name__)


# === MAIN COBRA VAD CLASS DEFINITION ===
class CobraVAD:
    """
    Handles voice activity detection using the Cobra VAD engine.

    Ensure that instances of AudioDataProvider are created elsewhere and passed into this class.
    Do not instantiate them directly within this class to maintain SRP and loose coupling.
    """

    def __init__(self, audio_data_provider: AudioDataProvider, access_key: str):
        """
        Initialize the Cobra VAD.
        Args:
            audio_data_provider: An instance that provides audio data frames.
            access_key: The access key for using Cobra VAD.
        """
        self.audio_data_provider = audio_data_provider
        self.access_key = access_key
        self.vad_engine = self._initialize_vad_engine()

    def _initialize_vad_engine(self):
        """
        Internal method to initialize the Cobra VAD engine.
        """
        return pvcobra.create(access_key=self.access_key)

    def process_audio(self):
        """
        Process audio data to detect voice activity.
        """
        while True:
            frame = self.audio_data_provider.get_audio_frame()
            is_voice = self.vad_engine.process(frame)
            if is_voice:
                logging.info("Voice activity detected.")
                self.handle_voice_activity()

    def handle_voice_activity(self):
        """
        Handle the detected voice activity.

        Define a callback mechanism or signal handling here to notify other parts of the application.
        """
        pass

    def __init__(self, access_key: str = None) -> None:
        self.access_key = access_key if access_key is not None else os.getenv('PICOVOICE_APIKEY')
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

    def start_recording(self, callback: Optional[Callable[[str], None]] = None) -> None:
        """
        Starts the voice recording process. The recording stops when the voice stops or when the inactivity limit is
        reached.

        Args:
            callback (Optional[Callable[[str], None]]): A function to call with the path to the recorded WAV file.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "recorded_voice.wav")

            recording = False
            silent_frames = 0
            inactivity_frames = 0
            frames_to_save = []

            while True:
                audio_frame = self.get_next_audio_frame()
                voice_probability = self.cobra_handle.process(audio_frame)

                if voice_probability > self.voice_threshold:
                    inactivity_frames = 0
                    silent_frames = 0
                    if not recording:
                        recording = True
                        frames_to_save = list(self.audio_buffer)  # Collect buffered audio when voice is detected
                        logger.info("Voice Detected - Starting Recording")
                    frames_to_save.append(audio_frame)
                else:
                    if recording:
                        silent_frames += 1
                        frames_to_save.append(audio_frame)
                        if silent_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate > self.silence_limit:
                            recording_length = len(
                                frames_to_save) * self.cobra_handle.frame_length / self.cobra_handle.sample_rate
                            if recording_length >= self.min_recording_length:
                                self.save_to_wav_file(frames_to_save, file_path)
                                logger.info(f"Recording of {recording_length:.2f} seconds saved to {file_path}.")
                                if callback is not None:
                                    callback(file_path)
                                return
                            else:
                                frames_to_save = []
                                recording = False
                                logger.info(f"Recording of {recording_length:.2f} seconds is under the minimum "
                                            f"length. Not saved.")
                    else:
                        if len(self.audio_buffer) == self.audio_buffer.maxlen:
                            self.audio_buffer.popleft()
                        self.audio_buffer.append(audio_frame)
                    inactivity_frames += 1

                if inactivity_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate > self.inactivity_limit:
                    logger.info("No voice detected for a while. Exiting...")
                    # Removed the return statement that returned 'NO_VOICE_EXIT'

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

    def cleanup(self) -> None:
        self.stream.stop_stream()
        self.stream.close()
        self.cobra_handle.delete()
