import logging
import wave
import os
from collections import deque
from .cobra import PyAudioDataProvider
from .voice_activity_detector import VoiceActivityDetector

class AudioRecorder:
    def __init__(self, access_key, audio_data_provider=None):
        # Configuration attributes from sample code
        self.VOICE_THRESHOLD = 0.8
        self.SILENCE_LIMIT = 2
        self.BUFFER_LENGTH = 2
        self.INACTIVITY_LIMIT = 2
        self.MIN_RECORDING_LENGTH = 3

        self.voice_activity_detector = VoiceActivityDetector(access_key)
        self.audio_data_provider = audio_data_provider or PyAudioDataProvider(rate=self.voice_activity_detector.sample_rate, frames_per_buffer=self.voice_activity_detector.frame_length)
        self.frames_to_save = deque(maxlen=self.BUFFER_LENGTH * self.voice_activity_detector.sample_rate // self.voice_activity_detector.frame_length)
        self.is_recording = False

    def start_recording(self):
        # Logic to start recording using voice_activity_detector and audio_data_provider from sample code
        recording = False
        silent_frames = 0
        inactivity_frames = 0
        frames_to_save = []

        try:
            while True:
                audio_frame = self.audio_data_provider.get_audio_frame()
                voice_probability = self.voice_activity_detector.process(audio_frame)

                if voice_probability > self.VOICE_THRESHOLD:
                    inactivity_frames = 0
                    silent_frames = 0
                    if not recording:
                        recording = True
                        frames_to_save = list(self.frames_to_save)  # Collect buffered audio when voice is detected
                        logging.info("Voice Detected - Starting Recording")
                    frames_to_save.append(audio_frame)
                else:
                    if len(self.frames_to_save) == self.frames_to_save.maxlen:
                        self.frames_to_save.popleft()
                    self.frames_to_save.append(audio_frame)
                    inactivity_frames += 1
                    if recording:
                        silent_frames += 1
                        frames_to_save.append(audio_frame)
                        if (silent_frames * self.voice_activity_detector.frame_length / self.voice_activity_detector.sample_rate > self.SILENCE_LIMIT):
                            recording_length = len(frames_to_save) * self.voice_activity_detector.frame_length / self.voice_activity_detector.sample_rate
                            if recording_length >= self.MIN_RECORDING_LENGTH:
                                self.save_to_wav_file(frames_to_save)
                                logging.info(f"Recording of {recording_length:.2f} seconds saved.")
                                return "SAVE"
                            else:
                                frames_to_save = []
                                recording = False
                                logging.info(f"Recording of {recording_length:.2f} seconds is under the minimum length. Not saved.")

                if (inactivity_frames * self.voice_activity_detector.frame_length / self.voice_activity_detector.sample_rate > self.INACTIVITY_LIMIT):
                    logging.info("No voice detected for a while. Exiting...")
                    return 'NO_VOICE_EXIT'
        except KeyboardInterrupt:
            if frames_to_save:
                recording_length = len(frames_to_save) * self.voice_activity_detector.frame_length / self.voice_activity_detector.sample_rate
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

    def save_to_wav_file(self, frames):
        # Logic to save frames to a WAV file from sample code
        duration = len(frames) * self.voice_activity_detector.frame_length / self.voice_activity_detector.sample_rate
        if duration < self.MIN_RECORDING_LENGTH:
            return 'UNDER_MIN_LENGTH'

        recordings_dir = os.path.join(os.path.dirname(__file__), 'Wav_MP3')
        filename = os.path.join(recordings_dir, "recording.wav")

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.audio_data_provider.py_audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.voice_activity_detector.sample_rate)
            wf.writeframes(b''.join(frames))
        logging.info(f"Saved to {filename}")
        return 'SAVE'

    def cleanup(self):
        self.voice_activity_detector.cleanup()
        self.audio_data_provider.cleanup()
