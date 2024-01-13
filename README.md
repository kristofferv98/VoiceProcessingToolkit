 # VoiceProcessingToolkit

 ## Introduction
 VoiceProcessingToolkit is a comprehensive Python library designed for a wide range of voice processing tasks, including wake word detection, voice recording, speech-to-text transcription, and text-to-speech synthesis. It aims to simplify the development of voice-activated applications and services by providing robust and easy-to-use tools.

 ## Features
 - Wake word detection using Picovoice Porcupine for reliable voice activation.
 - Voice recording with adjustable settings for voice activity detection to ensure high-quality audio capture.
 - Speech-to-text transcription leveraging OpenAI's Whisper model for accurate and fast conversion of speech into text.
 - Text-to-speech synthesis utilizing ElevenLabs' API, offering a wide range of customizable voices and languages.
 - Environment variable configuration for API keys to ensure secure and flexible integration with third-party services.
 - Example usage scripts provided to demonstrate the toolkit's capabilities and ease of use.
 - Extensible architecture allowing for the addition of new features and customization to fit specific use cases.

 ## Installation
 To install VoiceProcessingToolkit, run the following command:
 ```bash
 pip install VoiceProcessingToolkit
 ```

 ## Usage
 Here is a simple example of how to use the toolkit to detect a wake word and perform an action:
 ```python
 from VoiceProcessingManager import VoiceProcessingManager
 import os

 # Set environment variables for API keys
 os.environ['PICOVOICE_APIKEY'] = 'your-picovoice-api-key'
 os.environ['OPENAI_API_KEY'] = 'your-openai-api-key'
 os.environ['ELEVENLABS_API_KEY'] = 'your-elevenlabs-api-key'


 # Create a VoiceProcessingManager instance with default settings
 vpm = VoiceProcessingManager.create_default_instance(wake_word='jarvis')

 # Run the voice processing manager with transcription and text-to-speech
 text = vpm.run()


 print(f"Processed text: {text}")
 ```
 You can also run the toolkit without any recording, and provide your own text to convert to speech:

 ```python
from VoiceProcessingToolkit.VoiceProcessingManager import text_to_speech_stream
from dotenv import load_dotenv

load_dotenv()

text = "Hello, welcome to the Voice Processing Toolkit!"

text = text_to_speech_stream(text=text)

print(f"Processed text: {text}")
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
 - `run(tts=False, streaming=False)`: Processes a voice command with optional text-to-speech functionality.
 - `setup()`: Initializes the components of the voice processing manager.
 - `process_voice_command()`: Processes a voice command using the configured components.

 For a more detailed explanation of these attributes and methods, please refer to the inline documentation within the `VoiceProcessingManager.py` file.

 ## Getting Started
 To get started with VoiceProcessingToolkit, please refer to the inline documentation and example usage scripts provided in the toolkit. These resources provide detailed instructions on configuration, usage examples, and customization options.

 ## Example Usage
 The toolkit includes several example scripts that demonstrate different use cases and features. You can find these examples in the `example_usage` directory:

 - [Simple Setup](example_usage/Simple_setup.py): Demonstrates the basic setup and usage of the VoiceProcessingManager.
 - [Create Wake Word Data](example_usage/Create_wakeword_data.py): Demonstrates how to create a wake word dataset using the VoiceProcessingManager.
 - [Wake Word Decorators](example_usage/Wakeword_decorators.py): Demonstrates how to register actions with the VoiceProcessingManager that will be triggered when the wake word is detected.
 - [Custom Recording Logic](example_usage/Custom_recording_logic.py): Demonstrates custom recording settings and runs the VoiceProcessingManager without the wake word detector.
 - [Text to Speech](example_usage/Text_to_speach.py): Demonstrates the text to speech functionality with text as input using the VoiceProcessingManager.


 ## Configuration
 The toolkit can be configured with various settings such as wake word sensitivity, audio sample rate, and text-to-speech voice selection. For detailed configuration options, please see the `configuration.md` or visit the documentation in the example_usage folder.

 ## Contributing
 Contributions to the VoiceProcessingToolkit are welcome! Please read the CONTRIBUTING.md file for guidelines on how to contribute.

 ## Support
 If you encounter any issues or have questions, please file an issue on the [GitHub issue tracker](https://github.com/kristofferv98/VoiceProcessingToolkit/issues).

 ## License
 VoiceProcessingToolkit is licensed under the MIT License. See the LICENSE file for more details.

 ## Acknowledgements
 I would like to extend my gratitude to OpenAI, ElevenLabs, and Picovoice for their exceptional tools that have significantly contributed to the development of this project. Their innovative technologies have been instrumental in enabling the capabilities of the VoiceProcessingToolkit.
 VoiceProcessingToolkit is licensed under the MIT License. See the LICENSE file for more details.
