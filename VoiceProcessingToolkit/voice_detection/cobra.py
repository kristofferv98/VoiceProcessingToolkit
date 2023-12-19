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
    - Initialize the Cobra VAD engine.
    - Process audio data frames for voice activity detection.
    - Invoke a handler function when voice activity is detected.
    """

    def __init__(self, vad_engine, audio_data_provider, voice_activity_handler):
        """
        Initialize the Cobra VAD.
        Args:
            vad_engine: An instance of the Cobra VAD engine.
            audio_data_provider: An instance that provides audio data frames.
            voice_activity_handler: A callable that handles detected voice activity.
        """
        self.vad_engine = vad_engine
        self.audio_data_provider = audio_data_provider
        self.voice_activity_handler = voice_activity_handler

    def _initialize_vad_engine(self):
        """
        Internal method to initialize the Cobra VAD engine.
        """
        return pvcobra.create(access_key=self.access_key)

    # The existing process_audio method is correct as per the plan and does not need changes.

# This entire __init__ method is removed because we are now passing in the dependencies.

    # This method will be removed as the logic is now handled by the PyAudioDataProvider class.

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
        """
        Clean up resources, ensuring all acquired resources are released.
        """
        try:
            self.audio_data_provider.cleanup()
            self.vad_engine.delete()
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
