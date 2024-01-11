 # VoiceProcessingToolkit

 ## Introduction
 VoiceProcessingToolkit is a comprehensive library for voice processing tasks, including wake word detection, voice recording, transcription, and text-to-speech capabilities. It is designed to facilitate the development of voice-activated applications.

 ## Features
 - Wake word detection using state-of-the-art models.
 - High-quality voice recording with voice activity detection.
 - Accurate transcription of speech to text.
 - Text-to-speech synthesis with customizable voices.

 ## Installation
 To install VoiceProcessingToolkit, run the following command:
 ```bash
 pip install VoiceProcessingToolkit
 ```

 ## Usage
 Here is a simple example of how to use the toolkit to detect a wake word and perform an action:
 ```python
 from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager

 voice_processing_manager = VoiceProcessingManager.create_default_instance(wake_word='jarvis')
 voice_processing_manager.run()
 ```

 The `VoiceProcessingManager` class provides a high-level interface for managing the voice processing pipeline. It can be configured with various settings such as wake word sensitivity, audio sample rate, and text-to-speech voice selection.

 Attributes of `VoiceProcessingManager` include:
 - `wake_word`: The wake word for triggering voice recording.
 - `sensitivity`: Sensitivity for wake word detection.
 - `output_directory`: Directory for saving recorded audio files.
 - `audio_format`, `channels`, `rate`, `frames_per_buffer`: Audio stream parameters.
 - `voice_threshold`, `silence_limit`, `inactivity_limit`, `min_recording_length`, `buffer_length`: Voice recording parameters.
 - `use_wake_word`: Flag to use wake word detection.
 - `save_wake_word_recordings`: Flag to save audio buffer that triggered the wake word detection.
 - `play_notification_sound`: Flag to play a sound on detection.

 Methods of `VoiceProcessingManager` include:
 - `run(tts=False, streaming=False)`: Processes a voice command with optional text-to-speech functionality.
 - `setup()`: Initializes the components of the voice processing manager.
 - `process_voice_command()`: Processes a voice command using the configured components.

 ## Configuration
 The toolkit can be configured with various settings such as wake word sensitivity, audio sample rate, and text-to-speech voice selection. Refer to the documentation for detailed configuration options.

 ## Contributing
 Contributions to the VoiceProcessingToolkit are welcome! Please read the CONTRIBUTING.md file for guidelines on how to contribute.

 ## License
 VoiceProcessingToolkit is licensed under the MIT License. See the LICENSE file for more details.

 ## Acknowledgments
 Special thanks to all the contributors who have helped shape this toolkit. We also acknowledge the use of open-source models and APIs that have made this toolkit possible.
