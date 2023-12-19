# VoiceProcessingToolkit

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Support](#support)
- [Changelog](#changelog)
- [License](#license)
- [Authors](#authors)
- [Acknowledgments](#acknowledgments)

## Overview
The VoiceProcessingToolkit is an all-encompassing suite designed for sophisticated voice detection, wake word recognition, text-to-speech synthesis, and advanced audio processing. It offers intuitive interfaces to streamline the integration of voice processing capabilities into your applications.

## Features
- Wake word detection
- Voice activity detection
- Text-to-speech conversion
- Audio processing and noise reduction

## Installation
Before installing VoiceProcessingToolkit, ensure you have Python 3.7 or higher and pip installed.

To install the VoiceProcessingToolkit, run the following command:

```bash
pip install VoiceProcessingToolkit
```

## Getting Started
To quickly start using VoiceProcessingToolkit, install the package and try out the basic functionalities as shown below. For detailed examples, please refer to our [Examples](voice_processing_examples.py) file.

### Basic Usage
Here's a quick example to get you started with the WakeWordDetector and Text-to-Speech:

```python
from VoiceProcessingToolkit.text_to_speech.elevenlabs import text_to_speech
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import record_and_transcribe

# Record audio and transcribe it using the WakeWordDetector
result = record_and_transcribe()
# Convert the transcription result to speech and play it
text_to_speech(result)
# Print the transcription result
print(result)
```
For more detailed examples, see our [Examples](voice_processing_examples.py) file.

## Documentation
For more detailed API documentation, please refer to [VoiceProcessingToolkit Documentation](#).

## Contributing
We welcome contributions to the VoiceProcessingToolkit! If you have suggestions or would like to contribute code, please read our [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on our code of conduct and the process for submitting pull requests.

## Support
If you need help or have a question, raise an issue in the [GitHub Issue Tracker](https://github.com/yourorganization/voiceprocessingtoolkit/issues) or join our community on [Discord](#).

## Changelog
For a history of changes to this library, see the [CHANGELOG.md](CHANGELOG.md) file.

## License
This project is licensed under the MIT License - see the [LICENSE](https://github.com/yourorganization/voiceprocessingtoolkit/blob/main/LICENSE) file for details.

## Authors
- Kristoffer Vatnehol - kristoffer.vatnehol@appacia.com

## Acknowledgments
- Hat tip to anyone whose code was used
- Inspiration
- etc
## Wake Word Detector

### Overview

The `wake_word_detector` module of the VoiceProcessingToolkit provides a set of classes and utilities for detecting a specified wake word using the Porcupine engine. Upon detection of the wake word, it can execute registered actions, which can be either synchronous or asynchronous functions.

### Classes

#### WakeWordDetector

The `WakeWordDetector` class is responsible for continuously listening to the microphone's audio stream and detecting the specified wake word. When the wake word is detected, it triggers the execution of registered actions.

##### Attributes:
- `access_key (str)`: The access key for the Porcupine wake word engine.
- `wake_word (str)`: The wake word that the detector should listen for.
- `sensitivity (float)`: The sensitivity of the wake word detection, between 0 and 1.
- `audio_stream_manager (AudioStreamManager)`: Manages the audio stream from the microphone.
- `action_manager (ActionManager)`: Manages the actions to be executed when the wake word is detected.
- `play_notification_sound (bool)`: Indicates whether to play a notification sound upon detection.

##### Methods:
- `__init__(self, access_key, wake_word, sensitivity, action_manager, audio_stream_manager, play_notification_sound)`: Initializes the WakeWordDetector with the provided parameters.
- `initialize_porcupine(self)`: Initializes the Porcupine wake word engine.
- `voice_loop(self)`: The main loop that listens for the wake word and triggers the registered actions.
- `run(self)`: Starts the wake word detection loop in a separate thread.
- `cleanup(self)`: Cleans up the resources used by the wake word detector.

#### ActionManager

The `ActionManager` class manages a list of actions (functions) to be executed when the wake word is detected. It supports both synchronous and asynchronous functions.

##### Attributes:
- `_actions (list)`: A list of action functions to be executed.

##### Methods:
- `__init__(self)`: Initializes a new instance of ActionManager with an empty list of actions.
- `register_action(self, action_function)`: Registers a new action function to the list of actions.
- `execute_actions(self)`: Executes all registered action functions concurrently.

#### AudioStreamManager

The `AudioStreamManager` class manages the audio stream from the microphone, ensuring that audio data is captured correctly and made available to the WakeWordDetector.

##### Methods:
- `__init__(self, rate, channels, format, frames_per_buffer)`: Initializes the audio stream with the specified parameters.
- `cleanup(self)`: Cleans up the audio stream resources.

#### NotificationSoundManager

The `NotificationSoundManager` class is responsible for playing a notification sound when the wake word is detected.

##### Methods:
- `__init__(self, sound_file_path)`: Initializes the notification sound manager with the path to the sound file.
- `play(self)`: Plays the notification sound.

### Example Usage

The `example_usage` function demonstrates how to set up and use the `WakeWordDetector` along with the `ActionManager`, `AudioStreamManager`, and `NotificationSoundManager`. It registers both synchronous and asynchronous actions to be executed upon wake word detection.

```python
from VoiceProcessingToolkit.wake_word_detector import WakeWordDetector, AudioStreamManager, NotificationSoundManager, ActionManager, register_action_decorator

def example_usage():
    # Initialize the audio stream manager with the required audio parameters
    audio_stream_manager = AudioStreamManager(rate=16000, channels=1, format=pyaudio.paInt16, frames_per_buffer=512)

    # Create an instance of ActionManager
    action_manager = ActionManager()

    # Register synchronous and asynchronous actions using the decorator
    @register_action_decorator(action_manager)
    def action_with_notification():
        print("Sync function is running...")
        time.sleep(4.5)
        print("Action function completed!")

    @register_action_decorator(action_manager)
    async def async_action_1():
        print("Async function is running...")
        await asyncio.sleep(1)
        print("Async function completed!")

    # Initialize the wake word detector with the required parameters
    detector = WakeWordDetector(
        access_key="your-picovoice_api_key",
        wake_word='jarvis',
        sensitivity=0.75,
        action_manager=action_manager,
        audio_stream_manager=audio_stream_manager,
        play_notification_sound=True
    )

    # Start the wake word detection loop
    detector.run()
```

To use this example, replace `"your-picovoice_api_key"` with your actual Picovoice API key.

### Notes

- Ensure that you have the required dependencies installed as specified in `requirements.txt`.
- The `access_key` for the Porcupine engine must be valid and have the appropriate permissions for wake word detection.
- The `wake_word` must be one of the supported wake words by the Porcupine engine.
- The `sensitivity` parameter can be adjusted to balance between detection accuracy and false positives.
- The `play_notification_sound` parameter can be set to `False` if no sound should be played upon detection.

This documentation provides a comprehensive guide to using the `wake_word_detector` module within the VoiceProcessingToolkit. It is recommended to read the documentation thoroughly to understand the capabilities and limitations of the module.
