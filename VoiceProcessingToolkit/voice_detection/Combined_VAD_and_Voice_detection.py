#!/usr/bin/env python3
import collections
import logging
import os
import wave
import time
import pvcobra
import pyaudio
import numpy as np
import threading
from dotenv import load_dotenv


# Audio Data Provider Class
class AudioDataProvider(object):
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


class AudioRecorder(object):
    def __init__(self, output_directory=None, access_key=None, voice_threshold=0.8, silence_limit=2, inactivity_limit=2, min_recording_length=3, buffer_length=2):
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
        self.logger = logging.getLogger(__name__)
        self.py_audio = pyaudio.PyAudio()
        self.access_key = access_key or os.environ.get('PICOVOICE_APIKEY')
        self.vad_engine = self.cobra_handle = pvcobra.create(access_key=self.access_key)
        self.output_directory = output_directory or os.path.join(os.path.dirname(__file__), 'Wav_MP3')
        self.VOICE_THRESHOLD = voice_threshold
        self.SILENCE_LIMIT = silence_limit
        self.INACTIVITY_LIMIT = inactivity_limit
        self.MIN_RECORDING_LENGTH = min_recording_length
        self.BUFFER_LENGTH = buffer_length
        self.audio_buffer = collections.deque(maxlen=self.BUFFER_LENGTH * self.cobra_handle.sample_rate // self.cobra_handle.frame_length)
        self.inactivity_frames = 0
        self.is_recording = False
        self.recording = False
        self.frames_to_save = []
        self.frames = []
        self.lock = threading.Lock()
        self.recording_thread = None
        self.audio_data_provider = None


    def perform_recording(self):
        """
        Starts the recording process, handles KeyboardInterrupt, and ensures cleanup.
        Returns:
            str: The path to the recorded audio file.
        """
        """
        Starts the recording process, handles KeyboardInterrupt, and ensures cleanup.
        Returns the path to the recorded audio file.
        """
        self.audio_data_provider = AudioDataProvider()
        self.start_recording(self.audio_data_provider)
        try:
            while self.is_recording:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.logger.info("Recording interrupted by user.")
        finally:
            self.stop_recording()
            self.cleanup()
            return self.last_saved_file

    def start_recording(self, audio_data_provider):
        """
        Starts the audio recording process using the provided audio data provider.
        Args:
            audio_data_provider (AudioDataProvider): The provider of audio data frames.
        """
        self.audio_data_provider = audio_data_provider
        self.audio_data_provider.start_stream()
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self.record_loop, args=(audio_data_provider,))
        self.recording_thread.start()
        self.logger.info("Recording started.")

    def record_loop(self, audio_data_provider):
        """
        The main loop for recording audio, processing frames, and managing recording state.
        Args:
            audio_data_provider (AudioDataProvider): The provider of audio data frames.
        """
        silent_frames = 0
        while self.is_recording:
            try:
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
                        if self.should_finalize_recording(silent_frames):
                            self.logger.info("Inactivity limit exceeded. Finalizing recording...")
                            return
            except Exception as e:
                self.logger.error(f"An error occurred during recording: {e}")
                break

    def should_finalize_recording(self, silent_frames):
        """
        Determines whether the recording should be finalized based on the number of silent frames.
        Args:
            silent_frames (int): The number of consecutive silent frames.
        Returns:
            bool: True if the recording should be finalized, False otherwise.
        """
        if self.inactivity_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate > self.INACTIVITY_LIMIT:
            self.logger.info("No voice detected for a while. Finalizing recording...")
            self.finalize_recording()
            return True
        if silent_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate > self.SILENCE_LIMIT:
            self.logger.info("Exceeded silence limit. Finalizing recording...")
            self.finalize_recording()
            return True
        return False

    def process_frame(self, frame):
        """
        Processes a single frame of audio data, detecting voice activity and managing recording state.
        Args:
            frame (bytes): A frame of audio data.
        """
        if frame is not None:
            voice_activity_detected = self.detect_voice_activity(frame)
            self.manage_recording_state(frame, voice_activity_detected)

    def detect_voice_activity(self, frame):
        """
        Detects voice activity in a frame of audio data.
        Args:
            frame (bytes): A frame of audio data.
        Returns:
            bool: True if voice activity is detected, False otherwise.
        """
        audio_frame = np.frombuffer(frame, dtype=np.int16)
        voice_probability = self.vad_engine.process(audio_frame)
        return voice_probability > self.VOICE_THRESHOLD

    def manage_recording_state(self, frame, voice_activity_detected):
        """
        Manages the recording state based on voice activity detection.
        Args:
            frame (bytes): A frame of audio data.
            voice_activity_detected (bool): Whether voice activity was detected in the frame.
        """
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
        """
        Starts a new recording, saving the buffered audio frames.
        """
        self.recording = True
        self.frames_to_save = list(self.audio_buffer)  # Collect buffered audio when voice is detected
        self.logger.info("Voice Detected - Starting Recording")

    def buffer_audio_frame(self, frame):
        """
        Buffers an audio frame for potential inclusion in a recording.
        Args:
            frame (bytes): A frame of audio data.
        """
        if len(self.audio_buffer) == self.audio_buffer.maxlen:
            self.audio_buffer.popleft()
        self.audio_buffer.append(frame)

    def check_inactivity_duration(self):
        """
        Checks the duration of inactivity and finalizes the recording if necessary.
        """
        if (
                self.inactivity_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate >
                self.INACTIVITY_LIMIT):
            self.finalize_recording()

    def finalize_recording(self):
        """
        Finalizes the recording, saving it to a file if it meets the minimum length requirement.
        Returns:
            str or bool: The path to the saved recording file, or False if the recording was not saved.
        """
        result = False
        saved_file_path = None
        if self.frames_to_save:
            recording_length = len(self.frames_to_save) * self.cobra_handle.frame_length / self.cobra_handle.sample_rate
            if recording_length >= self.MIN_RECORDING_LENGTH:
                saved_file_path = self.save_to_wav_file(self.frames_to_save)
                self.logger.info(f"Recording of {recording_length:.2f} seconds saved.")
            else:
                self.logger.info(f"Recording of {recording_length:.2f} seconds is under the minimum length. Discarded.")
        self.recording = False
        self.frames_to_save = []
        self.is_recording = False
        self.last_saved_file = saved_file_path if saved_file_path else False
        return self.last_saved_file


    def save_to_wav_file(self, frames):
        """
        Saves the recorded audio frames to a WAV file.
        Args:
            frames (list): A list of audio frames to be saved.
        Returns:
            str or bool: The path to the saved WAV file, or False if the recording was not saved.
        """
        duration = len(frames) * self.cobra_handle.frame_length / self.cobra_handle.sample_rate
        if duration < self.MIN_RECORDING_LENGTH:
            return False

        recordings_dir = os.path.join(os.path.dirname(__file__), 'Wav_MP3')

        # Check if the directory exists, if not, create it
        if not os.path.exists(recordings_dir):
            os.makedirs(recordings_dir)

        filename = os.path.join(recordings_dir, "recording.wav")

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.py_audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.cobra_handle.sample_rate)
            wf.writeframes(b''.join(frames))
        logging.info(f"Saved to {filename}")
        return os.path.abspath(filename)

    def stop_recording(self):
        """
        Stops the recording process and joins the recording thread.
        """
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
            self.py_audio.terminate()
        self.logger.info("Recording stopped.")

    def cleanup(self):
        """
        Cleans up the audio recorder by deleting the Cobra VAD engine handle.
        """
        """
        Clean up the processor by deleting the Koala handle.
        """
        self.vad_engine.delete()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    load_dotenv()
    audio_recorder = AudioRecorder(output_directory='Wav_MP3')
    file = audio_recorder.perform_recording()
    logging.info(f"Saved to {file}")