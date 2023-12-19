import random

from VoiceProcessingToolkit.voice_detection.audio_data_provider import PyAudioDataProvider
from VoiceProcessingToolkit.voice_detection.voice_activity_detector import VoiceActivityDetector


class MockVAD:
    def __init__(self, sample_rate, frame_length):
        self.sample_rate = sample_rate
        self.frame_length = frame_length

    def process(self, frame):
        # Randomly decide if voice is detected
        return random.choice([True, False])

    def delete(self):
        # Cleanup if needed
        pass

def voice_activity_handler(frame):
    print("Voice activity detected.")

def main():
    sample_rate = 16000  # Hz
    frame_length = 512  # Adjust as needed

    # Create instances of MockVAD and PyAudioDataProvider
    vad_engine = MockVAD(sample_rate, frame_length)
    audio_data_provider = PyAudioDataProvider(rate=sample_rate, frames_per_buffer=frame_length)

    # Instantiate CobraVAD
    cobra_vad = VoiceActivityDetector(vad_engine, audio_data_provider, voice_activity_handler)

    # Start processing audio
    try:
        with cobra_vad:
            cobra_vad.start_recording(lambda file_path: print(f"Recording saved to: {file_path}"))
    except KeyboardInterrupt:
        print("Recording stopped by user")

if __name__ == "__main__":
    main()
