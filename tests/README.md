# VoiceProcessingToolkit Testing Framework

This directory contains the testing framework for the VoiceProcessingToolkit. The tests are organized into unit tests and integration tests.

## Test Structure

- `unit/`: Contains unit tests for individual components
  - `test_audio_stream_manager.py`: Tests for the AudioStream class
  - `test_eleven_labs_transcriber.py`: Tests for the ElevenLabsTranscriber class
  - `test_voice_processing_manager.py`: Tests for the VoiceProcessingManager class
- `integration/`: Contains integration tests for the entire voice processing pipeline
  - `test_voice_processing_pipeline.py`: Tests for the complete voice processing pipeline
- `conftest.py`: Contains fixtures and mocks used across multiple test files

## Running Tests

To run the tests, use the following commands:

```bash
# Activate the virtual environment
source .venv_test/bin/activate

# Run all tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=VoiceProcessingToolkit

# Run tests with detailed coverage report
python -m pytest --cov=VoiceProcessingToolkit --cov-report=term-missing

# Run specific test file
python -m pytest tests/unit/test_voice_processing_manager.py
```

## Current Test Coverage

The current test coverage is approximately 30%. The following components have good coverage:

- AudioStream: 70%
- ElevenLabsTranscriber: 62%
- ActionManager: 56%

Areas that need more test coverage:

- VoiceProcessingManager: 17%
- VoiceRecorder: 18%
- WakeWordDetector: 22%
- NotificationSoundManager: 29%

## Mocking Strategy

The tests use extensive mocking to avoid dependencies on external services and hardware:

1. **AudioStream**: Mocked to avoid actual audio hardware access
2. **ElevenLabsTranscriber**: Mocked API calls to avoid actual network requests
3. **WakeWordDetector**: Mocked to avoid dependencies on Porcupine and actual wake word detection
4. **VoiceProcessingManager**: Mocked to isolate testing of specific methods

## Future Improvements

1. **Increase Test Coverage**: Add more tests to cover the missing lines, especially in the VoiceProcessingManager and WakeWordDetector classes.
2. **Add More Integration Tests**: Create more comprehensive integration tests that test different scenarios.
3. **Add Performance Tests**: Add tests to measure the performance of the voice processing pipeline.
4. **Add Error Handling Tests**: Add more tests to verify error handling in edge cases.
5. **Improve Mocking**: Refine the mocking strategy to make tests more robust and less brittle.

## Dependencies

The testing framework uses the following dependencies:

- pytest: For running tests
- pytest-cov: For measuring test coverage
- unittest.mock: For mocking dependencies 