"""
Unit tests for the ElevenLabsTranscriber class.
"""
import os
import pytest
from unittest.mock import patch, Mock, mock_open, call

from VoiceProcessingToolkit.transcription.elevenlabs import ElevenLabsTranscriber

# Test constants
TEST_API_KEY = "test_api_key"
TEST_DIRECT_API_KEY = "direct_api_key"
TEST_AUDIO_FILE = "test.wav"
TEST_AUDIO_DATA = b"audio data"
TEST_TRANSCRIPTION = "This is a sample transcription."
TEST_BYTES_TRANSCRIPTION = "This is a bytes transcription."

# HTTP status codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_SERVER_ERROR = 500

# Retry settings
MAX_RETRIES = 1
RETRY_DELAY = 0.1

class TestElevenLabsTranscriber:
    """Unit tests for the ElevenLabsTranscriber class."""

    def test_initialization(self):
        """Test that the transcriber initializes with the correct parameters."""
        # With API key in environment
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": TEST_API_KEY}):
            transcriber = ElevenLabsTranscriber()
            assert transcriber.api_key == TEST_API_KEY

        # With API key provided directly
        transcriber = ElevenLabsTranscriber(api_key=TEST_DIRECT_API_KEY)
        assert transcriber.api_key == TEST_DIRECT_API_KEY

        # With no API key
        with patch.dict(os.environ, {}, clear=True):
            with patch('VoiceProcessingToolkit.transcription.elevenlabs.logger') as mock_logger:
                transcriber = ElevenLabsTranscriber()
                assert transcriber.api_key is None
                mock_logger.warning.assert_called_once()

    @patch('VoiceProcessingToolkit.transcription.elevenlabs.requests.post')
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.os.path.exists')
    def test_transcribe_audio_success(self, mock_exists, mock_post):
        """Test successful audio transcription."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = HTTP_OK
        mock_response.json.return_value = {
            "text": TEST_TRANSCRIPTION
        }
        mock_post.return_value = mock_response
        
        # Mock file existence check
        mock_exists.return_value = True

        # Create transcriber with max_retries=0 to simplify testing
        transcriber = ElevenLabsTranscriber(api_key=TEST_API_KEY, max_retries=0)
        
        # Mock the file opening
        with patch("builtins.open", mock_open(read_data=TEST_AUDIO_DATA)):
            # Test transcription
            result = transcriber.transcribe_audio(TEST_AUDIO_FILE)
            
            # Verify results
            assert result == TEST_TRANSCRIPTION
            mock_post.assert_called_once()
            mock_exists.assert_called_once_with(TEST_AUDIO_FILE)

    @patch('VoiceProcessingToolkit.transcription.elevenlabs.requests.post')
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.os.path.exists')
    def test_transcribe_audio_error(self, mock_exists, mock_post):
        """Test error handling during transcription."""
        # Setup mock response for error
        mock_response = Mock()
        mock_response.status_code = HTTP_BAD_REQUEST
        mock_response.text = "Error transcribing audio"
        mock_post.return_value = mock_response
        
        # Mock file existence check
        mock_exists.return_value = True

        # Create transcriber with max_retries=0 to simplify testing
        transcriber = ElevenLabsTranscriber(api_key=TEST_API_KEY, max_retries=0)
        
        # Mock the file opening
        with patch("builtins.open", mock_open(read_data=TEST_AUDIO_DATA)):
            # Test transcription with error
            result = transcriber.transcribe_audio(TEST_AUDIO_FILE)
            
            # Verify results
            assert result == ""  # Should return empty string on error
            mock_post.assert_called_once()
            mock_exists.assert_called_once_with(TEST_AUDIO_FILE)

    @patch('VoiceProcessingToolkit.transcription.elevenlabs.requests.post')
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.os.path.exists')
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.time.sleep')
    def test_transcribe_audio_server_error_with_retries(self, mock_sleep, mock_exists, mock_post):
        """Test handling of server errors during transcription with retries."""
        # Setup mock response for server error
        mock_response = Mock()
        mock_response.status_code = HTTP_SERVER_ERROR
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        # Mock file existence check
        mock_exists.return_value = True

        # Create transcriber with 1 retry
        transcriber = ElevenLabsTranscriber(
            api_key=TEST_API_KEY,
            max_retries=MAX_RETRIES,
            retry_delay=RETRY_DELAY
        )
        
        # Mock the file opening
        with patch("builtins.open", mock_open(read_data=TEST_AUDIO_DATA)):
            # Test transcription with server error
            result = transcriber.transcribe_audio(TEST_AUDIO_FILE)
            
            # Verify results
            assert result == ""  # Should return empty string on error
            # Should be called initial + max_retries times
            assert mock_post.call_count == MAX_RETRIES + 1
            mock_sleep.assert_called_once()
            mock_exists.assert_called_once_with(TEST_AUDIO_FILE)

    @patch('VoiceProcessingToolkit.transcription.elevenlabs.requests.post')
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.os.path.exists')
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.time.sleep')
    def test_transcribe_audio_connection_error_with_retries(self, mock_sleep, mock_exists, mock_post):
        """Test handling of connection errors during transcription with retries."""
        # Setup mock to raise connection error
        mock_post.side_effect = ConnectionError("Connection failed")
        
        # Mock file existence check
        mock_exists.return_value = True

        # Create transcriber with 1 retry
        transcriber = ElevenLabsTranscriber(
            api_key=TEST_API_KEY,
            max_retries=MAX_RETRIES,
            retry_delay=RETRY_DELAY
        )
        
        # Mock the file opening
        with patch("builtins.open", mock_open(read_data=TEST_AUDIO_DATA)):
            # Test transcription with connection error
            result = transcriber.transcribe_audio(TEST_AUDIO_FILE)
            
            # Verify results
            assert result == ""  # Should return empty string on error
            # Should be called initial + max_retries times
            assert mock_post.call_count == MAX_RETRIES + 1
            mock_sleep.assert_called_once()
            mock_exists.assert_called_once_with(TEST_AUDIO_FILE)
            
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.os.path.exists')
    def test_transcribe_audio_file_not_found(self, mock_exists):
        """Test handling of file not found error."""
        # Mock file existence check to return False
        mock_exists.return_value = False
        
        # Create transcriber
        transcriber = ElevenLabsTranscriber(api_key=TEST_API_KEY)
        
        # Test transcription with file not found
        result = transcriber.transcribe_audio(TEST_AUDIO_FILE)
        
        # Verify results
        assert result == ""  # Should return empty string on error
        mock_exists.assert_called_once_with(TEST_AUDIO_FILE)
    
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.requests.post')
    def test_transcribe_bytes(self, mock_post):
        """Test transcription from bytes."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = HTTP_OK
        mock_response.json.return_value = {
            "text": TEST_BYTES_TRANSCRIPTION
        }
        mock_post.return_value = mock_response
        
        # Create transcriber with max_retries=0 to simplify testing
        transcriber = ElevenLabsTranscriber(api_key=TEST_API_KEY, max_retries=0)
        
        # Test transcription from bytes
        result = transcriber.transcribe_bytes(TEST_AUDIO_DATA)
        
        # Verify results
        assert result.get("text") == TEST_BYTES_TRANSCRIPTION
        mock_post.assert_called_once() 