 # VoiceProcessingToolkit

 ## Introduction
 VoiceProcessingToolkit is a comprehensive Python library designed for a wide range of voice processing tasks, including wake word detection, voice recording, speech-to-text transcription, and text-to-speech synthesis. It aims to simplify the development of voice-activated applications and services by providing robust and easy-to-use tools.

 ## Features
 - Wake word detection using state-of-the-art models.
 - High-quality voice recording with voice activity detection.
 - Accurate transcription of speech to text.
 - Text-to-speech synthesis with customizable voices.

 ## Installation
 To install VoiceProcessingToolkit, run the following command:
 ```bash
 pip install git+https://github.com/your-github/VoiceProcessingToolkit.git
 ```

 Note: Replace the URL with the actual repository URL if the package is not available on PyPI.

 ## Usage
 Here is a simple example of how to use the toolkit to detect a wake word and perform an action:
 ```python
 from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager

 voice_processing_manager = VoiceProcessingManager.create_default_instance(wake_word='computer')
 voice_processing_manager.run()
 ```

 The `VoiceProcessingManager` class provides a high-level interface for managing the voice processing pipeline. It can be configured with various settings such as wake word sensitivity, audio sample rate, and text-to-speech voice selection.

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

 - [Simple Setup](example_usage/Simple_setup.py): Demonstrates a simple setup with default configurations.
 - [Create Wake Word Data](example_usage/Create_wakeword_data.py): Demonstrate how to create a dataset for wake word detection.
 - [Wake Word Decorators](example_usage/Wakeword_decorators.py): Illustrates the use of decorators for wake word actions.
 - [Custom Recording Logic](example_usage/Custom_recording_logic.py): Provides an example of customizing the recording logic.


 ## Configuration
 The toolkit can be configured with various settings such as wake word sensitivity, audio sample rate, and text-to-speech voice selection. For detailed configuration options, please see the `configuration.md` or visit the documentation in the example_usage folder.

 ## Contributing
 Contributions to the VoiceProcessingToolkit are welcome! Please read the CONTRIBUTING.md file for guidelines on how to contribute.

 ## Support
If you encounter any issues or have questions, please file an issue on the [GitHub issue tracker](https://github.com/your-github/VoiceProcessingToolkit/issues).

## License
VoiceProcessingToolkit is licensed under the MIT License. See the LICENSE file for more details.

## Acknowledgements
I would like to extend my gratitude to OpenAI, ElevenLabs, and Picovoice for their exceptional tools that have significantly contributed to the development of this project. Their innovative technologies have been instrumental in enabling the capabilities of the VoiceProcessingToolkit.
 VoiceProcessingToolkit is licensed under the MIT License. See the LICENSE file for more details.