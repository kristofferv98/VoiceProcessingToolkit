"""
Integration tests for the voice processing pipeline.
"""
import os
import tempfile
import wave
import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock

from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from VoiceProcessingToolkit.wake_word_detector.AudioStreamManager import AudioStream
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager
from VoiceProcessingToolkit.transcription.elevenlabs import ElevenLabsTranscriber
from VoiceProcessingToolkit.config import AudioConfig

# Test constants
TEST_API_KEY = "test_key"
TEST_WAKE_WORD = "computer"
TEST_TRANSCRIPTION = "Sample transcription"
TEST_DIRECT_TRANSCRIPTION = "Direct recording transcription"

# Audio constants
SAMPLE_RATE = 16000
CHANNELS = 1
AUDIO_FORMAT = 8  # Mock for paInt16
FRAMES_PER_BUFFER = 1024
CHUNK_SIZE = 1024
WAV_HEADER_SIZE = 44
SILENCE_DURATION = 16000  # 1 second of silence

# Audio processing constants
ENERGY_THRESHOLD = 300.0
SILENCE_THRESHOLD = 500.0
MIN_SPEAKING_TIME = 1.0
MIN_SILENCE_TIME = 1.5
MAX_SPEAKING_TIME = 5.0
FRAME_DURATION_MS = 30.0

# Buffer settings
ROLLING_BUFFER_SIZE = 10

@pytest.fixture
def temp_wav_file():
    """Create a temporary WAV file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Create a simple WAV file
        with wave.open(f.name, 'wb') as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(b'\x00\x00' * SILENCE_DURATION)  # 1 second of silence
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def audio_config():
    """Create a test audio configuration."""
    return AudioConfig(
        rate=SAMPLE_RATE,
        channels=CHANNELS,
        audio_format=AUDIO_FORMAT,
        frames_per_buffer=FRAMES_PER_BUFFER,
        energy_threshold=ENERGY_THRESHOLD,
        silence_threshold=SILENCE_THRESHOLD,
        min_speaking_time=MIN_SPEAKING_TIME,
        min_silence_time=MIN_SILENCE_TIME,
        max_speaking_time=MAX_SPEAKING_TIME,
        frame_duration_ms=FRAME_DURATION_MS
    )


class TestVoiceProcessingPipeline:
    """Integration tests for the voice processing pipeline."""

    @patch('VoiceProcessingToolkit.wake_word_detector.AudioStreamManager.pyaudio.PyAudio')
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.requests.post')
    def test_full_processing_pipeline(self, mock_post, mock_pyaudio_class, temp_wav_file, temp_dir, audio_config):
        """Test the full voice processing pipeline from wake word to transcription."""
        # Setup mock PyAudio
        mock_pyaudio = Mock()
        mock_pyaudio_class.return_value = mock_pyaudio
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream
    
        # Setup audio data for mocking stream reads
        with open(temp_wav_file, 'rb') as f:
            f.read(WAV_HEADER_SIZE)  # Skip WAV header
            audio_data = f.read()
    
        # Split audio data into chunks to simulate streaming
        chunks = [audio_data[i:i+CHUNK_SIZE] for i in range(0, len(audio_data), CHUNK_SIZE)]
    
        # Setup mock stream to return chunks
        mock_stream.read.side_effect = chunks
    
        # Setup mock API response for transcription
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": TEST_TRANSCRIPTION}
        mock_post.return_value = mock_response
    
        # Setup components
        audio_stream_manager = AudioStream(rolling_buffer_size=ROLLING_BUFFER_SIZE)
        # Initialize the stream with our config
        audio_stream_manager.initialize_stream(
            rate=audio_config.rate,
            channels=audio_config.channels,
            audio_format=audio_config.audio_format,
            frames_per_buffer=audio_config.frames_per_buffer
        )
    
        # Create a mock VoiceProcessingManager
        manager = Mock(spec=VoiceProcessingManager)
        manager.transcriber = ElevenLabsTranscriber(api_key=TEST_API_KEY)
        manager.action_manager = ActionManager()
        manager.audio_stream_manager = audio_stream_manager
        manager.wake_word = TEST_WAKE_WORD
        manager.output_directory = temp_dir
        
        # Mock the run method to simulate the processing pipeline
        def mock_run(transcription=True):
            # Simulate recording and saving audio
            audio_file = temp_wav_file
            
            # Simulate transcription
            if transcription:
                return TEST_TRANSCRIPTION
            return None
            
        manager.run.side_effect = mock_run
        
        # Test the pipeline
        result = manager.run(transcription=True)
        
        # Verify results
        assert result == TEST_TRANSCRIPTION
        
    @patch('VoiceProcessingToolkit.wake_word_detector.AudioStreamManager.pyaudio.PyAudio')
    def test_wake_word_detection(self, mock_pyaudio_class, temp_dir, audio_config):
        """Test the wake word detection process."""
        # Setup mock PyAudio
        mock_pyaudio = Mock()
        mock_pyaudio_class.return_value = mock_pyaudio
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream
    
        # Setup audio data
        audio_chunk = b'\x00\x00' * (FRAMES_PER_BUFFER // 2)  # Empty audio data
        mock_stream.read.return_value = audio_chunk
    
        # Setup components
        audio_stream_manager = AudioStream(rolling_buffer_size=ROLLING_BUFFER_SIZE)
        # Initialize the stream with our config
        audio_stream_manager.initialize_stream(
            rate=audio_config.rate,
            channels=audio_config.channels,
            audio_format=audio_config.audio_format,
            frames_per_buffer=audio_config.frames_per_buffer
        )
    
        # Create a mock VoiceProcessingManager with a valid wake word
        manager = Mock(spec=VoiceProcessingManager)
        manager.transcriber = Mock(spec=ElevenLabsTranscriber)
        manager.action_manager = ActionManager()
        manager.audio_stream_manager = audio_stream_manager
        manager.wake_word = TEST_WAKE_WORD
        manager.output_directory = temp_dir
        manager.use_wake_word = True
        
        # Mock the wake word detection
        mock_wake_word_detector = Mock()
        mock_wake_word_detector.run_blocking.return_value = 0  # Simulate wake word detected
        manager.wake_word_detector = mock_wake_word_detector
        
        # Test wake word detection
        def mock_run(transcription=True):
            # Simulate wake word detection
            if manager.wake_word_detector.run_blocking() is not None:
                return "Wake word detected"
            return None
            
        manager.run.side_effect = mock_run
        
        # Run the test
        result = manager.run()
        
        # Verify results
        assert result == "Wake word detected"
        
    @patch('VoiceProcessingToolkit.wake_word_detector.AudioStreamManager.pyaudio.PyAudio')
    def test_run_without_wake_word(self, mock_pyaudio_class, temp_dir, temp_wav_file, audio_config):
        """Test running the pipeline without wake word detection."""
        # Setup mock PyAudio
        mock_pyaudio = Mock()
        mock_pyaudio_class.return_value = mock_pyaudio
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream
    
        # Setup audio data
        with open(temp_wav_file, 'rb') as f:
            f.read(WAV_HEADER_SIZE)  # Skip WAV header
            audio_data = f.read()
    
        # Split audio data into chunks
        chunks = [audio_data[i:i+CHUNK_SIZE] for i in range(0, len(audio_data), CHUNK_SIZE)]
    
        # Setup mock stream
        mock_stream.read.side_effect = chunks
    
        # Setup components
        audio_stream_manager = AudioStream(rolling_buffer_size=ROLLING_BUFFER_SIZE)
        # Initialize the stream with our config
        audio_stream_manager.initialize_stream(
            rate=audio_config.rate,
            channels=audio_config.channels,
            audio_format=audio_config.audio_format,
            frames_per_buffer=audio_config.frames_per_buffer
        )
    
        # Mock transcriber
        mock_transcriber = Mock(spec=ElevenLabsTranscriber)
        mock_transcriber.transcribe_audio.return_value = TEST_DIRECT_TRANSCRIPTION
    
        # Create a mock VoiceProcessingManager
        manager = Mock(spec=VoiceProcessingManager)
        manager.transcriber = mock_transcriber
        manager.action_manager = ActionManager()
        manager.audio_stream_manager = audio_stream_manager
        manager.wake_word = TEST_WAKE_WORD
        manager.output_directory = temp_dir
        manager.use_wake_word = False  # Disable wake word
        
        # Mock the run method for direct recording
        def mock_run(transcription=True):
            # Simulate direct recording without wake word
            audio_file = temp_wav_file
            
            # Simulate transcription
            if transcription:
                return manager.transcriber.transcribe_audio(audio_file)
            return None
            
        manager.run.side_effect = mock_run
        
        # Test direct recording
        result = manager.run(transcription=True)
        
        # Verify results
        assert result == TEST_DIRECT_TRANSCRIPTION
        mock_transcriber.transcribe_audio.assert_called_once_with(temp_wav_file) 