import logging
from typing import Callable


class VoiceActivityDetector:
    VOICE_THRESHOLD = 0.8
    INACTIVITY_LIMIT = 2  # seconds

    def __init__(self, vad_engine, audio_data_provider, voice_activity_handler: Callable[[bool, bytes], None]):
        self.vad_engine = vad_engine
        self.audio_data_provider = audio_data_provider
        self.voice_activity_handler = voice_activity_handler
        self.inactivity_frames = 0

    def run(self):
        while True:
            frame = self.audio_data_provider.get_audio_frame()
            print("This is each frame")
            if frame is None:
                continue

            is_voice = self.vad_engine.process(frame) > self.VOICE_THRESHOLD
            self.voice_activity_handler(is_voice, frame)

            if not is_voice:
                self.inactivity_frames += 1
                if (self.inactivity_frames > self.INACTIVITY_LIMIT * self.vad_engine.sample_rate /
                        self.vad_engine.frame_length):
                    logging.info("Inactivity detected - Exiting")
                    break
            else:
                self.inactivity_frames = 0


