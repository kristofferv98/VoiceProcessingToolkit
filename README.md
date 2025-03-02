# VoiceProcessingToolkit

## Introduction
VoiceProcessingToolkit is a Python library designed for voice processing tasks, including wake word detection and transcription. It aims to streamline the creation of voice-activated applications.

1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
   - [Basic Example](#basic-example)
   - [Example with Autogen](example_usage/Autogen_voice_assistant_example_pyfile.py)
5. [Configuration](#configuration)
6. [Example Usage](#example-usage)
7. [Contributing](#contributing)
8. [Support](#support)
9. [License](#license)
10. [Development Status](#development-status)
11. [Acknowledgements](#acknowledgements)
12. [Contact Information](#contact-information)

### Features
+ Wake word detection using Picovoice Porcupine.
+ High-quality voice recording with adjustable settings for Voice Activation Detection.
+ Fast and accurate speech-to-text transcription with ElevenLabs Speech-to-Text API.
+ Secure API key management with environment variables.
+ Example scripts for easy demonstration and usage.
+ Extensible architecture for feature additions and customization.

### Installation
The VoiceProcessingToolkit is available on PyPI. To install, run the following command:
```bash
pip install VoiceProcessingToolkit
```

## Usage
### Basic Example
The following is a quick-start guide to using the toolkit for wake word detection and speech transcription. 

```python
from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from dotenv import load_dotenv

import logging
import os

# logging.basicConfig(level=logging.INFO)
load_dotenv()

# Set environment variables for API keys
os.getenv('PICOVOICE_APIKEY')
os.getenv('ELEVENLABS_API_KEY')

# Create a VoiceProcessingManager instance with default settings
vpm = VoiceProcessingManager.create_default_instance(wake_word='computer')

# Run the voice processing manager with transcription
text = vpm.run()
print(text)
```

The `VoiceProcessingManager` class is the central component of the toolkit, orchestrating the voice processing workflow. It is highly configurable, allowing you to tailor the behavior to your specific needs. Below are some of the key attributes and methods provided by this class:

Attributes of `VoiceProcessingManager` include:
- `wake_word`: The wake word for triggering voice recording.
- `sensitivity`: Sensitivity for wake word detection.
- `output_directory`: Directory for saving recorded audio files<.
- `audio_format`, `channels`, `rate`, `frames_per_buffer`: Audio stream parameters.
- `voice_threshold`, `silence_limit`, `inactivity_limit`, `min_recording_length`, `buffer_length`: Voice recording parameters.
- `use_wake_word`: Flag to use wake word detection.
- `save_wake_word_recordings`: Flag to save audio buffer that triggered the wake word detection.
- `play_notification_sound`: Flag to play a sound on detection.

Methods of `VoiceProcessingManager` include:
- `run(transcription=True)`: Processes a voice command and optionally performs transcription.
- `setup()`: Initializes the components of the voice processing manager.
- `process_voice_command()`: Processes a voice command using the configured components.

For a more detailed explanation of these attributes and methods, please refer to the inline documentation within the `VoiceProcessingManager.py` file.

## Getting Started
To begin using VoiceProcessingToolkit, follow these steps:

To get started with the VoiceProcessingToolkit, follow these simple steps:

1. Install the toolkit via pip: `pip install VoiceProcessingToolkit`

2. Obtain API keys from Picovoice and ElevenLabs.

3. Set the API keys as environment variables.

4. Run an example script from the `example_usage` directory.

5. Customize `VoiceProcessingManager` settings as needed.

For a more detailed explanation of these steps, please refer to the inline documentation and example usage scripts provided in the toolkit. These resources provide detailed instructions on configuration, usage examples, and customization options.

If you have downloaded the github repository, you can run the examples from the `example_usage` directory. 
Rename the `REMOVE_THIS_TEXT.env` file to `.env` and add your API keys.
## Example Usage
The `example_usage` directory contains scripts showcasing various features:

- [Simple Setup](example_usage/Simple_setup.py): Demonstrates the basic setup and usage of the VoiceProcessingManager.
- [Create Wake Word Data](example_usage/Create_wakeword_data.py): Demonstrates how to create a wake word dataset using the VoiceProcessingManager.
- [Custom Recording Logic](example_usage/Custom_recording_logic.py): Demonstrates custom recording settings and runs the VoiceProcessingManager without the wake word detector.
- [Autogen_voice_assistant](example_usage/Autogen_voice_assistant_example.ipynb): Demonstrates how to use the VoiceProcessingManager to create a voice assistant with custom wake words and instructions.


### Configuration
Customize the toolkit with settings like wake word sensitivity and audio sample rate. See the examples for more details.

### Contributing
Contributions are welcome! See CONTRIBUTING.md for guidelines.

### Support
For issues or questions, please use the [GitHub issue tracker](https://github.com/kristofferv98/VoiceProcessingToolkit/issues).

### License
Licensed under the MIT License. See LICENSE for details.

### Development Status
The project is in development. Feedback and contributions are appreciated.

### Acknowledgements
Thanks to ElevenLabs and Picovoice for their tools that enhance this project.

### Contact Information
For help or inquiries, reach out via [GitHub Discussions](https://github.com/kristofferv98/VoiceProcessingToolkit/discussions).

