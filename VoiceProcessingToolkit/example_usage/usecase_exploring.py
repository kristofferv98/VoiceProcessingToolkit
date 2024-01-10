import logging
from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
import wave
import pyaudio
import threading

# Basic configuration
logging.basicConfig(level=logging.INFO)

class BackgroundAudioRecorder:
    def __init__(self, rate=16000, channels=1, chunk_size=1024, record_seconds=5):
        self.rate = rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.record_seconds = record_seconds
        self.frames = []
        self.is_recording = False
        self.save_flag = threading.Event()
        self.audio_interface = pyaudio.PyAudio()
        self.stream = None

    def start_recording(self):
        self.stream = self.audio_interface.open(format=pyaudio.paInt16,
                                                channels=self.channels,
                                                rate=self.rate,
                                                input=True,
                                                frames_per_buffer=self.chunk_size)
        self.is_recording = True
        threading.Thread(target=self.record).start()

    def record(self):
        while self.is_recording:
            data = self.stream.read(self.chunk_size)
            self.frames.append(data)
            if self.save_flag.is_set():
                self.save_flag.clear()
                self.save_recording()

    def save_recording(self):
        filename = f"recording_{int(time.time())}.wav"
        filepath = os.path.join(os.getcwd(), filename)
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio_interface.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
        self.frames.clear()
        logging.info(f"Saved recording to {filepath}")

    def stop_recording(self):
        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()
        self.audio_interface.terminate()

save_audio_flag = threading.Event()


def main():
    """
    Demonstrates the basic usage of the VoiceProcessingManager.

    This script initializes the VoiceProcessingManager with default settings and runs it to process a voice command.
    The processed text is printed to the console. The script uses text-to-speech functionality without streaming.

    The script can be terminated early by a KeyboardInterrupt (Ctrl+C).
    """
    try:
        # Create a VoiceProcessingManager instance with default settings
        vpm = VoiceProcessingManager.create_default_instance()

        # Create an AudioRecorder instance
        background_audio_recorder = BackgroundAudioRecorder()
        # Start the background recording thread
        background_audio_recorder.start_recording()
        background_recording_thread.start()

        @vpm.action_manager.register_action
        def recording_flag():
            # Set the flag to trigger saving the audio snapshot
            background_audio_recorder.save_flag.set()
            print("Recording flag is set")

        # Run the voice processing manager with text-to-speech but without streaming
        text = vpm.run(tts=True, streaming=False)
        print(f"Processed text: {text}")

    except KeyboardInterrupt:
        logging.info("Interrupted by user, shutting down.")
    finally:
        # Ensure the background recording thread is stopped
        background_audio_recorder.stop_recording()


if __name__ == '__main__':
    main()
