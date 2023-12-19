# Wake Word Detector Documentation

## WakeWordDetector Class

The `WakeWordDetector` class is responsible for continuously listening to the microphone's audio stream and detecting the specified wake word. When the wake word is detected, it triggers the execution of registered actions.

### Attributes:
- `access_key (str)`: The access key for the Porcupine wake word engine.
- `wake_word (str)`: The wake word that the detector should listen for.
- `sensitivity (float)`: The sensitivity of the wake word detection, between 0 and 1.
- `audio_stream_manager (AudioStreamManager)`: Manages the audio stream from the microphone.
- `action_manager (ActionManager)`: Manages the actions to be executed when the wake word is detected.
- `play_notification_sound (bool)`: Indicates whether to play a notification sound upon detection.

### Methods:
- `__init__(...)`: Initializes the WakeWordDetector with the provided parameters.
- `initialize_porcupine()`: Initializes the Porcupine wake word engine.
- `voice_loop()`: The main loop that listens for the wake word and triggers the registered actions.
- `run()`: Starts the wake word detection loop in a separate thread.
- `cleanup()`: Cleans up the resources used by the wake word detector.

## ActionManager Class

The `ActionManager` class manages a list of actions (functions) to be executed when the wake word is detected. It supports both synchronous and asynchronous functions.

### Attributes:
- `_actions (list)`: A list of action functions to be executed.

### Methods:
- `__init__()`: Initializes a new instance of ActionManager with an empty list of actions.
- `register_action(action_function)`: Registers a new action function to the list of actions.
- `execute_actions()`: Executes all registered action functions concurrently.

## Decorators

### register_action_decorator

The `register_action_decorator` is used to register an action function with the `ActionManager`. It takes the `ActionManager` instance as an argument and returns a decorator that can be used to register action functions.

### Example Usage

```python
from VoiceProcessingToolkit.wake_word_detector import WakeWordDetector, ActionManager

# Create an instance of ActionManager
action_manager = ActionManager()

# Define an action function
def my_action():
    print("Action executed!")

# Register the action function using the decorator
@register_action_decorator(action_manager)
def my_decorated_action():
    print("Decorated action executed!")

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

Replace `"your-picovoice_api_key"` with your actual Picovoice API key to use this example.
