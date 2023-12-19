import logging
import threading
import time

import pvcobra
import numpy as np
import wave
import os
from collections import deque
import pyaudio  # Import PyAudio at the beginning

class VoiceRecorder:
    def __init__(self, access_key="b2UbNJ2N5xNROBsICABolmKQwtQN7ARTRTSB+U0lZg+kDieYqcx7nw=="):
        self.access_key = access_key or os.environ.get('COBRA_ACCESS_KEY')
        self.cobra_handle = pvcobra.create(access_key=self.access_key)

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=self.cobra_handle.sample_rate,
                                  input=True, frames_per_buffer=self.cobra_handle.frame_length)

        # Configuration
        self.VOICE_THRESHOLD = 0.8 #relates to to stopping recording after probability of voice is below threshold
        self.SILENCE_LIMIT = 2  # Silence limit in seconds. The max ammount of seconds where you may be silent while recording. When this time passes the recording finishes and the file is delivered.
        self.BUFFER_LENGTH = 2 # The size of the internal circular buffer in seconds. The buffer is used to keep track of surrounding noise levels. if you're in a quiet room, make this smaller. If you're in a noisy room make this larger.n
        self.INACTIVITY_LIMIT = 2 # Inactivity limit in seconds. The max ammount of seconds where you may be inactive while recording. When this time passes the recording finishes and the file is delivered.
        self.MIN_RECORDING_LENGTH = 3  # Minimum length for recording to be saved (seconds)
        self.audio_buffer = deque(
            maxlen=self.BUFFER_LENGTH * self.cobra_handle.sample_rate // self.cobra_handle.frame_length)

    def start_async_file_check(self, file_path):
        def check_loop():
            last_modified = os.path.getmtime(file_path)
            first_run = True  # Flag to indicate first run
            while not self.stop_check:
                current_modified = os.path.getmtime(file_path)
                if not first_run and current_modified != last_modified:
                    last_modified = current_modified
                    # Handle file change here
                else:
                    first_run = False  # Reset the flag after the first run
                time.sleep(0.1)  # Check every 100ms or suitable interval

        self.stop_check = False
        self.file_check_thread = threading.Thread(target=check_loop)
        self.file_check_thread.start()


    def stop_async_file_check(self):
        self.stop_check = True
        if self.file_check_thread:
            self.file_check_thread.join()
    def get_next_audio_frame(self):
        frame = self.stream.read(self.cobra_handle.frame_length, exception_on_overflow=False)
        return np.frombuffer(frame, dtype=np.int16)

    def save_to_wav_file(self, frames):
        duration = len(frames) * self.cobra_handle.frame_length / self.cobra_handle.sample_rate
        if duration < self.MIN_RECORDING_LENGTH:
            return 'UNDER_MIN_LENGTH'

        recordings_dir = os.path.join(os.path.dirname(__file__), 'Wav_MP3')
        filename = os.path.join(recordings_dir, "recording.wav")

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.cobra_handle.sample_rate)
            wf.writeframes(b''.join(frames))
        logging.info(f"Saved to {filename}")
        return 'SAVE'

    def start_recording(self, file_path=None):
        if file_path:
            self.start_async_file_check(file_path)

        recording = False
        silent_frames = 0
        inactivity_frames = 0
        frames_to_save = []

        try:
            while True:
                audio_frame = self.get_next_audio_frame()
                voice_probability = self.cobra_handle.process(audio_frame)

                if voice_probability > self.VOICE_THRESHOLD:
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
                        if (silent_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate > self.SILENCE_LIMIT):
                            recording_length = len(frames_to_save) * self.cobra_handle.frame_length / self.cobra_handle.sample_rate
                            if recording_length >= self.MIN_RECORDING_LENGTH:
                                self.save_to_wav_file(frames_to_save)
                                logging.info(f"Recording of {recording_length:.2f} seconds saved.")
                                return "SAVE"
                            else:
                                frames_to_save = []
                                recording = False
                                logging.info(f"Recording of {recording_length:.2f} seconds is under the minimum length. Not saved.")

                if (inactivity_frames * self.cobra_handle.frame_length / self.cobra_handle.sample_rate > self.INACTIVITY_LIMIT):
                    logging.info("No voice detected for a while. Exiting...")
                    return 'NO_VOICE_EXIT'
        except KeyboardInterrupt:
            if frames_to_save:
                recording_length = len(frames_to_save) * self.cobra_handle.frame_length / self.cobra_handle.sample_rate
                if recording_length >= self.MIN_RECORDING_LENGTH:
                    self.save_to_wav_file(frames_to_save)
                    logging.info(f"Recording of {recording_length:.2f} seconds saved.")
                    return "SAVE"
                else:
                    logging.info(f"Recording of {recording_length:.2f} seconds is under the minimum length. Not saved.")
                    return "UNDER_MIN_LENGTH"
            logging.info("Exiting...")
        finally:
            self.cleanup()


    def cleanup(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.cobra_handle.delete()

if __name__ == '__main__':
    recorder = VoiceRecorder()
    recorder.start_recording()
    recorder.cleanup()