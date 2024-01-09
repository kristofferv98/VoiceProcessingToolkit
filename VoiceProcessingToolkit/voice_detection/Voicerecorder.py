#!/usr/bin/env python3
import collections
import logging
import os
import wave
import threading
from dotenv import load_dotenv
import numpy as np
import pyaudio
import pvcobra

logger = logging.getLogger(__name__)
load_dotenv()


# Audio Data Provider Class
class AudioDataProvider:
    def __init__(self, audio_format=pyaudio.paInt16, channels=1, rate=16000, frames_per_buffer=512):
        self._audio_format = audio_format
        self._channels = channels
        self._rate = rate
        self._frames_per_buffer = frames_per_buffer
        self._stream = None
        self._py_audio = pyaudio.PyAudio()

    def start_stream(self):
        self._stream = self._py_audio.open(
            format=self._audio_format,
            channels=self._channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._frames_per_buffer
        )

    def is_stream_active(self):
        return self._stream.is_active()

    def get_next_frame(self):
        if self.is_stream_active():
            return self._stream.read(self._frames_per_buffer, exception_on_overflow=False)
        else:
            raise IOError("Audio stream is not active.")

    def stop_stream(self):
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._py_audio.terminate()


class AudioRecorder:
    def __init__(self, output_directory=None, access_key=None, voice_threshold=0.8, silence_limit=2, inactivity_limit=2,
                 min_recording_length=3, buffer_length=2):
        """
        Initializes the audio recorder with the given parameters.
        Args:
            output_directory (str): The directory where recordings will be saved.
            access_key (str): The access key for the Cobra VAD engine.
            voice_threshold (float): The threshold for voice detection.
            silence_limit (int): The number of seconds of silence before stopping the recording.
            inactivity_limit (int): The number of seconds of inactivity before stopping the recording.
            min_recording_length (int): The minimum length of a valid recording.
            buffer_length (int): The length of the audio buffer.
        """
        self.last_saved_file = None
        self._logger = logger  # Logger is now private
        self._py_audio = pyaudio.PyAudio()
        self._access_key = access_key or os.environ.get('PICOVOICE_APIKEY')  # Access key is now private
        self._vad_engine = self._cobra_handle = pvcobra.create(
            access_key=self._access_key)  # VAD engine and Cobra handle are now private
        self._output_directory = output_directory or os.path.join(os.path.dirname(__file__),
                                                                  'Wav_MP3')  # Output directory is now private
        self.VOICE_THRESHOLD = voice_threshold
        self.SILENCE_LIMIT = silence_limit
        self.INACTIVITY_LIMIT = inactivity_limit
        self.MIN_RECORDING_LENGTH = min_recording_length
        self.BUFFER_LENGTH = buffer_length
        self._audio_buffer = collections.deque(maxlen=self.BUFFER_LENGTH * self._cobra_handle.sample_rate // self.
                                               _cobra_handle.frame_length)
        self._inactivity_frames = 0  # Inactivity frames counter is now private
        self.is_recording = False  # Recording state is now private
        self._recording = False  # Recording state is now private
        self._frames_to_save = []  # Frames to save are now private
        self._frames = []  # Frames are now private
        self._lock = threading.Lock()  # Lock for thread safety is now private
        self.recording_thread = None  # Recording thread is now private
        self._audio_data_provider = None  # Audio data provider is now private
        self._stop_recording_flag = False  # Stop recording flag is now private

    def cleanup(self):
        """
        Cleans up the resources used by the audio recorder.
        """
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join()
        if self._audio_data_provider:
            self._audio_data_provider.stop_stream()

    def perform_recording(self) -> str:
        """
        Starts the recording process, handles KeyboardInterrupt, and ensures cleanup.
        Returns:
            str: The path to the recorded audio file.
        """
        self._stop_recording_flag = False
        self._audio_data_provider = AudioDataProvider()
        self.recording_thread = threading.Thread(target=self.record_loop, args=(self._audio_data_provider,), daemon=True)
        self.recording_thread.start()
        self.recording_thread.join()
        self.recording_thread.join()
        return self.last_saved_file if self.last_saved_file else None


    def record_loop(self, audio_data_provider: AudioDataProvider) -> None:
        self._audio_data_provider = audio_data_provider
        self._audio_data_provider.start_stream()
        self.is_recording = True
        self._logger.info("Recording started.")
        silent_frames = 0
        while self.is_recording:
            if self._stop_event.is_set():
                self._logger.info("Stop event set, stopping recording loop.")
                break
            if self._stop_recording_flag:
                self._logger.info("Stop flag set, stopping recording loop.")
                break
            try:
                frame = audio_data_provider.get_next_frame()
                self.process_frame(frame)
                if not self._recording:
                    self.buffer_audio_frame(frame)
                else:
                    voice_activity_detected = self.detect_voice_activity(frame)
                    if voice_activity_detected:
                        self._inactivity_frames = 0
                        self._frames_to_save.append(frame)
                    else:
                        self._inactivity_frames += 1
                        silent_frames += 1
                        if self.should_finalize_recording(silent_frames):
                            self._logger.info("Inactivity limit exceeded. Finalizing recording...")
                            return
            except Exception as e:
                self._logger.error(f"An error occurred during recording: {e}")
                break

    def should_finalize_recording(self, silent_frames: int) -> bool:
        """
        Determines whether the recording should be finalized based on the number of silent frames.
        Args:
            silent_frames (int): The number of consecutive silent frames.
        Returns:
            bool: True if the recording should be finalized, False otherwise.
        """
        if (self._inactivity_frames * self._cobra_handle.frame_length / self._cobra_handle.sample_rate > self.
                INACTIVITY_LIMIT):
            self._logger.info("No voice detected for a while. Finalizing recording...")
            self.finalize_recording()
            return True
        if (silent_frames * self._cobra_handle.frame_length / self._cobra_handle.sample_rate > self.
                SILENCE_LIMIT):
            self._logger.info("Exceeded silence limit. Finalizing recording...")
            self.finalize_recording()
            return True
        return False

    def process_frame(self, frame: bytes) -> None:
        """
        Processes a single frame of audio data, detecting voice activity and managing recording state.
        Args:
            frame (bytes): A frame of audio data.
        """
        if frame is not None:
            voice_activity_detected = self.detect_voice_activity(frame)
            self.manage_recording_state(frame, voice_activity_detected)

    def detect_voice_activity(self, frame: bytes) -> bool:
        """
        Detects voice activity in a frame of audio data.
        Args:
            frame (bytes): A frame of audio data.
        Returns:
            bool: True if voice activity is detected, False otherwise.
        """
        audio_frame = np.frombuffer(frame, dtype=np.int16)
        voice_probability = self._vad_engine.process(audio_frame)
        return voice_probability > self.VOICE_THRESHOLD

    def manage_recording_state(self, frame: bytes, voice_activity_detected: bool) -> None:
        """
        Manages the recording state based on voice activity detection.
        Args:
            frame (bytes): A frame of audio data.
            voice_activity_detected (bool): Whether voice activity was detected in the frame.
        """
        with self._lock:
            if voice_activity_detected:
                self._inactivity_frames = 0  # Inactivity frames counter is now private
                if not self.is_recording:
                    self.start_new_recording()
                self._frames_to_save.append(frame)
            else:
                self.buffer_audio_frame(frame)
                self._inactivity_frames += 1
                if self.is_recording:
                    self._frames_to_save.append(frame)
                    if (
                            self._inactivity_frames * self._cobra_handle.frame_length / self._cobra_handle.sample_rate >
                            self.INACTIVITY_LIMIT):
                        self.finalize_recording()

    def start_new_recording(self) -> None:
        """
        Starts a new recording, saving the buffered audio frames.
        """
        self._recording = True
        self._frames_to_save = list(self._audio_buffer)  # Collect buffered audio when voice is detected
        self._logger.info("Voice Detected - Starting Recording")

    def buffer_audio_frame(self, frame: bytes) -> None:
        """
        Buffers an audio frame for potential inclusion in a recording.
        Args:
            frame (bytes): A frame of audio data.
        """
        if len(self._audio_buffer) == self._audio_buffer.maxlen:
            self._audio_buffer.popleft()
        self._audio_buffer.append(frame)

    def check_inactivity_duration(self) -> None:
        """
        Checks the duration of inactivity and finalizes the recording if necessary.
        """
        if (
                self._inactivity_frames * self._cobra_handle.frame_length / self._cobra_handle.sample_rate >
                self.INACTIVITY_LIMIT):
            self.finalize_recording()

    def finalize_recording(self) -> str:
        """
        Finalizes the recording, saving it to a file if it meets the minimum length requirement.
        Returns:
            str or bool: The path to the saved recording file, or False if the recording was not saved.
        """
        saved_file_path = None
        if self._frames_to_save:
            recording_length = len(
                self._frames_to_save) * self._cobra_handle.frame_length / self._cobra_handle.sample_rate
            if recording_length >= self.MIN_RECORDING_LENGTH:
                saved_file_path = self.save_to_wav_file(self._frames_to_save)
                self._logger.info(f"Recording of {recording_length:.2f} seconds saved.")
            else:
                self._logger.info(
                    f"Recording of {recording_length:.2f} seconds is under the minimum length. Discarded.")
        self._recording = False  # Recording state is now private
        self._frames_to_save = []  # Frames to save are now private
        self.is_recording = False  # Recording state is now private
        self.last_saved_file = saved_file_path if saved_file_path else False
        return self.last_saved_file

    def save_to_wav_file(self, frames: list):
        """
        Saves the recorded audio frames to a WAV file.
        Args:
            frames (list): A list of audio frames to be saved.
        Returns:
            str or bool: The path to the saved WAV file, or False if the recording was not saved.
        """
        duration = len(frames) * self._cobra_handle.frame_length / self._cobra_handle.sample_rate
        if duration < self.MIN_RECORDING_LENGTH:
            return False

        recordings_dir = os.path.join(os.path.dirname(__file__), 'Wav_MP3')

        # Check if the directory exists, if not, create it
        if not os.path.exists(recordings_dir):
            os.makedirs(recordings_dir)

        filename = os.path.join(recordings_dir, "recording.wav")

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self._py_audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self._cobra_handle.sample_rate)
            wf.writeframes(b''.join(frames))
        logger.info(f"Saved to {filename}")
        return os.path.abspath(filename)

    def stop_recording(self) -> None:
        """
        Stops the recording process and joins the recording thread.
        """
        self.is_recording = False  # Recording state is now private
        if self.recording_thread:
            self.recording_thread.join()
            self._py_audio.terminate()
        self._logger.info("Recording stopped.")



if __name__ == '__main__':
    audio_recorder = AudioRecorder(output_directory='Wav_MP3')
    recorded_file = audio_recorder.perform_recording()
    logger.info(f"Saved to {recorded_file}")
