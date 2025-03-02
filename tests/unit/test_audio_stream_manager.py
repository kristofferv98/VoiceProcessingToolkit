"""
Unit tests for the AudioStream class.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from VoiceProcessingToolkit.wake_word_detector.AudioStreamManager import AudioStream


class TestAudioStream:
    """Test cases for the AudioStream class."""

    @patch('VoiceProcessingToolkit.wake_word_detector.AudioStreamManager.pyaudio.PyAudio')
    def test_initialization(self, mock_pyaudio_class):
        """Test that the manager initializes with the correct parameters."""
        # Setup
        mock_pyaudio = Mock()
        mock_pyaudio_class.return_value = mock_pyaudio
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream
        
        # Create instance
        manager = AudioStream(rolling_buffer_size=1024)
        
        # Initialize the stream
        manager.initialize_stream(
            rate=16000,
            channels=1,
            audio_format=8,  # Representing paInt16
            frames_per_buffer=512
        )
        
        # Verify
        assert manager.rolling_buffer_size == 1024
        mock_pyaudio.open.assert_called_once_with(
            format=8,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=512
        )

    @patch('VoiceProcessingToolkit.wake_word_detector.AudioStreamManager.pyaudio.PyAudio')
    def test_read(self, mock_pyaudio_class):
        """Test the read method."""
        # Setup
        mock_pyaudio = Mock()
        mock_pyaudio_class.return_value = mock_pyaudio
        mock_stream = Mock()
        mock_stream.read.return_value = b'audio_data'
        mock_pyaudio.open.return_value = mock_stream
        
        # Create instance
        manager = AudioStream()
        manager.initialize_stream(
            rate=16000,
            channels=1,
            audio_format=8,
            frames_per_buffer=1024
        )
        
        # Test
        result = manager.read()
        
        # Verify
        assert result == b'audio_data'
        mock_stream.read.assert_called_once_with(1024, exception_on_overflow=False)

    @patch('VoiceProcessingToolkit.wake_word_detector.AudioStreamManager.pyaudio.PyAudio')
    def test_get_stream(self, mock_pyaudio_class):
        """Test the get_stream method."""
        # Setup
        mock_pyaudio = Mock()
        mock_pyaudio_class.return_value = mock_pyaudio
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream
        
        # Create instance
        manager = AudioStream()
        manager.initialize_stream(
            rate=16000,
            channels=1,
            audio_format=8,
            frames_per_buffer=512
        )
        
        # Test
        result = manager.get_stream()
        
        # Verify
        assert result == mock_stream

    @patch('VoiceProcessingToolkit.wake_word_detector.AudioStreamManager.pyaudio.PyAudio')
    def test_cleanup(self, mock_pyaudio_class):
        """Test the cleanup method."""
        # Setup
        mock_pyaudio = Mock()
        mock_pyaudio_class.return_value = mock_pyaudio
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream
        
        # Create instance
        manager = AudioStream()
        manager.initialize_stream(
            rate=16000,
            channels=1,
            audio_format=8,
            frames_per_buffer=512
        )
        
        # Test
        manager.cleanup()
        
        # Verify
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
        mock_pyaudio.terminate.assert_called_once()

    @patch('VoiceProcessingToolkit.wake_word_detector.AudioStreamManager.pyaudio.PyAudio')
    def test_is_stream_closed(self, mock_pyaudio_class):
        """Test the is_stream_closed method."""
        # Setup
        mock_pyaudio = Mock()
        mock_pyaudio_class.return_value = mock_pyaudio
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream
        
        # Create instance
        manager = AudioStream()
        
        # Test initial state (should be closed)
        assert manager.is_stream_closed() is True
        
        # Initialize and test again
        manager.initialize_stream(
            rate=16000,
            channels=1,
            audio_format=8,
            frames_per_buffer=512
        )
        
        # Should not be closed after initialization
        assert manager.is_stream_closed() is False
        
        # Clean up and test again
        manager.cleanup()
        assert manager.is_stream_closed() is True
        
    @patch('VoiceProcessingToolkit.wake_word_detector.AudioStreamManager.pyaudio.PyAudio')
    def test_rolling_buffer(self, mock_pyaudio_class):
        """Test the rolling buffer functionality."""
        # Setup
        mock_pyaudio = Mock()
        mock_pyaudio_class.return_value = mock_pyaudio
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream
        
        # Create instance with small buffer size
        buffer_size = 10
        manager = AudioStream(rolling_buffer_size=buffer_size)
        
        # Test initial buffer
        assert manager.get_rolling_buffer() == b''
        
        # Add data shorter than buffer size
        test_data = b'12345'
        manager.update_rolling_buffer(test_data)
        assert manager.get_rolling_buffer() == test_data
        
        # Add more data to exceed buffer size
        more_data = b'abcdefghij'
        manager.update_rolling_buffer(more_data)
        
        # Buffer should contain the most recent 10 bytes
        expected = test_data + more_data
        expected = expected[-buffer_size:]
        assert manager.get_rolling_buffer() == expected