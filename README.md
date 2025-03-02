# VoiceProcessingToolkit

Voice Processing Toolkit is a Python package for voice processing tasks, providing a comprehensive suite of tools for wake word detection, voice recording, and transcription.

## Introduction

This toolkit provides an end-to-end solution for voice processing applications, including wake word detection (using Porcupine), voice recording, and speech-to-text conversion (using ElevenLabs API). It features a modular design with well-defined interfaces, making it easy to extend or customize for your specific use case.

## Features

- **Wake Word Detection**: Detect custom wake words using Porcupine engine
- **Voice Recording**: Record voice commands with automatic silence detection
- **Transcription**: Convert speech to text using the ElevenLabs API
- **Modular Design**: Well-defined interfaces for extending functionality
- **Resource Management**: Proper resource cleanup to prevent memory leaks
- **Thread Safety**: Robust thread management for concurrent operations
- **Comprehensive Configuration**: Flexible configuration system with sensible defaults

## Major Changes in v2.0

- **Interface-Based Architecture**: All major components now implement interfaces, making the system more modular and extensible
- **Improved Thread Management**: Robust thread handling with proper resource cleanup
- **Centralized Configuration**: New configuration system with sensible defaults
- **Enhanced Error Handling**: Comprehensive error handling with retries
- **Better Resource Management**: Proper cleanup of resources to prevent memory leaks

## Installation

You can install the package using pip:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv add VoiceProcessingToolkit
```

## Usage

### Basic Usage

```python
from VoiceProcessingToolkit import VoiceProcessingManager

# Create a default manager instance
manager = VoiceProcessingManager.create_default_instance()

# Process a voice command (detects wake word, records voice, and transcribes)
transcription = manager.run()
print(f"Transcription: {transcription}")
```

### Custom Configuration

```python
from VoiceProcessingToolkit import VoiceProcessingManager, config

# Load custom configuration from file
custom_config = config.get_config("config.json")

# Create a manager with custom parameters
manager = VoiceProcessingManager(
    wake_word="jarvis",
    sensitivity=0.8,
    output_dir="my_recordings"
)

# Process a voice command
transcription = manager.run()
```

### Using Individual Components

```python
from VoiceProcessingToolkit.wake_word_detector import WakeWordDetector
from VoiceProcessingToolkit.voice_detection import AudioRecorder
from VoiceProcessingToolkit.transcription import ElevenLabsTranscriber

# Create components
wake_word_detector = WakeWordDetector(wake_word="alexa", sensitivity=0.7)
recorder = AudioRecorder(output_dir="recordings")
transcriber = ElevenLabsTranscriber()

# Use components independently
wake_word_detector.run_blocking()  # Wait for wake word
recording_path = recorder.perform_recording()  # Record voice
transcription = transcriber.transcribe_audio(recording_path)  # Transcribe
```

## Configuration

The toolkit uses a comprehensive configuration system with sensible defaults. You can customize the configuration in several ways:

### Environment Variables

Set these environment variables to configure API keys:

- `ELEVEN_LABS_API_KEY`: API key for ElevenLabs transcription service
- `PORCUPINE_ACCESS_KEY`: Access key for Porcupine wake word detection

### Configuration File

Create a JSON configuration file with your desired settings:

```json
{
    "transcriber": {
        "provider": "elevenlabs",
        "model_id": "whisper-1",
        "max_retries": 3
    },
    "audio": {
        "rate": 16000,
        "energy_threshold": 300.0,
        "min_speaking_time": 1.0
    },
    "wake_word": {
        "wake_word": "computer",
        "sensitivity": 0.75
    },
    "paths": {
        "output_dir": "/path/to/recordings"
    }
}
```

Load the configuration in your code:

```python
from VoiceProcessingToolkit import config

custom_config = config.get_config("config.json")
```

## Testing

The toolkit includes a comprehensive testing framework to ensure the reliability and functionality of all components. For more information, see [Testing](tests/README.md).

To run tests:

```bash
python -m pytest
```

To run tests with coverage:

```bash
python -m pytest --cov=VoiceProcessingToolkit
```

## Contributing

Contributions are welcome! Here are some ways you can contribute:

- Add support for additional transcription services
- Improve wake word detection accuracy
- Add new features
- Fix bugs
- Improve documentation

Please make sure to update tests as appropriate.

## Support

If you need help using this toolkit, please open an issue on the GitHub repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Development Status

This project is actively maintained and under development. The current version is 2.0.0.

## Acknowledgements

This toolkit uses the following open-source projects:

- [Porcupine](https://github.com/Picovoice/porcupine) for wake word detection
- [PyAudio](http://people.csail.mit.edu/hubert/pyaudio/) for audio input/output

## Contact Information

For questions, feedback, or support, please contact the maintainers through GitHub issues.

