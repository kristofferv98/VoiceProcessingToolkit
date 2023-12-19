# === IMPORTS SECTION ===
# Note: Ensure that only the necessary dependencies for the VAD process are imported.
# Avoid importing classes that will be injected as dependencies.
import logging
import numpy as np
import pyaudio
import pvcobra

logger = logging.getLogger(__name__)
# Purpose: Import only essential libraries needed for voice activity detection.
# Caution: Avoid importing unnecessary modules to keep the class focused on its primary responsibility.


# === MAIN COBRA VAD CLASS DEFINITION ===
class CobraVAD:
    """
    Handles voice activity detection using the Cobra VAD engine.
    Responsibilities:
    - Process audio data frames for voice activity detection.
    - Invoke a handler function when voice activity is detected.
    """

    def __init__(self, vad_engine: pvcobra.VoiceActivityDetector, audio_data_provider: AudioDataProvider, voice_activity_handler: Callable[[str], None]):
        if not isinstance(vad_engine, pvcobra.VoiceActivityDetector):
            raise TypeError("vad_engine must be an instance of pvcobra.VoiceActivityDetector")
        if not isinstance(audio_data_provider, AudioDataProvider):
            raise TypeError("audio_data_provider must be an instance of AudioDataProvider")
        if not callable(voice_activity_handler):
            raise TypeError("voice_activity_handler must be callable")
        """
        Initialize the Cobra VAD.
        Args:
            vad_engine: An instance of the Cobra VAD engine.
            audio_data_provider: An instance that provides audio data frames.
            voice_activity_handler: A callable that handles detected voice activity.
        """
        if not isinstance(vad_engine, pvcobra.VoiceActivityDetector):
            raise TypeError("vad_engine must be an instance of pvcobra.VoiceActivityDetector")
        if not isinstance(audio_data_provider, AudioDataProvider):
            raise TypeError("audio_data_provider must be an instance of AudioDataProvider")
        if not callable(voice_activity_handler):
            raise TypeError("voice_activity_handler must be callable")

        self.vad_engine = vad_engine
        self.audio_data_provider = audio_data_provider
        self.voice_activity_handler = voice_activity_handler


    # The existing process_audio method is correct as per the plan and does not need changes.

# This entire __init__ method is removed because we are now passing in the dependencies.

    # This method will be removed as the logic is now handled by the PyAudioDataProvider class.

    # Placeholder for refactored start_recording method
    # The actual refactoring would involve breaking down the complex logic into smaller, more manageable functions.
    # However, without the full context of the existing complex logic, I cannot provide the exact changes needed.
    # If you can provide the specific sections of the code that need refactoring, I can then give you the detailed
    # SEARCH/REPLACE blocks for those changes.

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

        if frames:
            try:
                with wave.open(file_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(self.pyaudio_instance.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(self.cobra_handle.sample_rate)
                    wf.writeframes(b''.join(frames))
                logging.info(f"Saved recording to {file_path}")
            except Exception as e:
                logging.error(f"Failed to save recording to {file_path}: {e}")
        else:
            logging.warning("No frames to save to WAV file.")

    def cleanup(self) -> None:
        """
        Clean up resources, ensuring all acquired resources are released.
        """
        if self.audio_data_provider:
            try:
                self.audio_data_provider.cleanup()
            except Exception as e:
                logging.error(f"Error during audio_data_provider cleanup: {e}")
        if self.vad_engine:
            try:
                self.vad_engine.delete()
            except Exception as e:
                logging.error(f"Error during vad_engine cleanup: {e}")
