import argparse
from VoiceProcessingToolkit.wake_word_detector import WakeWordDetector, AudioStreamManager, ActionManager
from VoiceProcessingToolkit.text_to_speech.elevenlabs import text_to_speech

def main():
    parser = argparse.ArgumentParser(description='VoiceProcessingToolkit Command Line Interface')
    subparsers = parser.add_subparsers(help='sub-command help', dest='command')

    # Wake word detection command
    parser_wake_word = subparsers.add_parser('wake-word', help='Start wake word detection')
    parser_wake_word.add_argument('--access-key', type=str, required=True, help='Access key for the Porcupine wake word engine')
    parser_wake_word.add_argument('--wake-word', type=str, required=True, help='Wake word to detect')
    parser_wake_word.add_argument('--sensitivity', type=float, default=0.5, help='Sensitivity of the wake word detection')

    # Text-to-speech command
    parser_tts = subparsers.add_parser('tts', help='Convert text to speech')
    parser_tts.add_argument('text', type=str, help='Text to convert to speech')

    # Parse the arguments
    args = parser.parse_args()

    if args.command == 'wake-word':
        # Initialize and start wake word detection
        audio_stream_manager = AudioStreamManager(rate=16000, channels=1, format=pyaudio.paInt16, frames_per_buffer=512)
        action_manager = ActionManager()
        detector = WakeWordDetector(
            access_key=args.access_key,
            wake_word=args.wake_word,
            sensitivity=args.sensitivity,
            action_manager=action_manager,
            audio_stream_manager=audio_stream_manager
        )
        detector.run()
    elif args.command == 'tts':
        # Perform text-to-speech
        text_to_speech(args.text)

if __name__ == '__main__':
    main()
