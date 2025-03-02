"""
Unit tests for the ElevenLabsTranscriber class.
"""
import os
import pytest
from unittest.mock import patch, Mock, mock_open, call

from VoiceProcessingToolkit.transcription.elevenlabs import ElevenLabsTranscriber


class TestElevenLabsTranscriber:
    """Unit tests for the ElevenLabsTranscriber class."""

    def test_initialization(self):
        """Test that the transcriber initializes with the correct parameters."""
        # With API key in environment
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test_api_key"}):
            transcriber = ElevenLabsTranscriber()
            assert transcriber.api_key == "test_api_key"

        # With API key provided directly
        transcriber = ElevenLabsTranscriber(api_key="direct_api_key")
        assert transcriber.api_key == "direct_api_key"

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
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "text": "This is a sample transcription."
        }
        mock_post.return_value = mock_response
        
        # Mock file existence check
        mock_exists.return_value = True

        # Create transcriber with max_retries=0 to simplify testing
        transcriber = ElevenLabsTranscriber(api_key="test_key", max_retries=0)
        
        # Mock the file opening
        with patch("builtins.open", mock_open(read_data=b"audio data")):
            # Test transcription
            result = transcriber.transcribe_audio("test.wav")
            
            # Verify results
            assert result == "This is a sample transcription."
            mock_post.assert_called_once()
            mock_exists.assert_called_once_with("test.wav")

    @patch('VoiceProcessingToolkit.transcription.elevenlabs.requests.post')
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.os.path.exists')
    def test_transcribe_audio_error(self, mock_exists, mock_post):
        """Test error handling during transcription."""
        # Setup mock response for error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Error transcribing audio"
        mock_post.return_value = mock_response
        
        # Mock file existence check
        mock_exists.return_value = True

        # Create transcriber with max_retries=0 to simplify testing
        transcriber = ElevenLabsTranscriber(api_key="test_key", max_retries=0)
        
        # Mock the file opening
        with patch("builtins.open", mock_open(read_data=b"audio data")):
            # Test transcription with error
            result = transcriber.transcribe_audio("test.wav")
            
            # Verify results
            assert result == ""  # Should return empty string on error
            mock_post.assert_called_once()
            mock_exists.assert_called_once_with("test.wav")

    @patch('VoiceProcessingToolkit.transcription.elevenlabs.requests.post')
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.os.path.exists')
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.time.sleep')
    def test_transcribe_audio_server_error_with_retries(self, mock_sleep, mock_exists, mock_post):
        """Test handling of server errors during transcription with retries."""
        # Setup mock response for server error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        # Mock file existence check
        mock_exists.return_value = True

        # Create transcriber with 1 retry
        max_retries = 1
        transcriber = ElevenLabsTranscriber(api_key="test_key", max_retries=max_retries, retry_delay=0.1)
        
        # Mock the file opening
        with patch("builtins.open", mock_open(read_data=b"audio data")):
            # Test transcription with server error
            result = transcriber.transcribe_audio("test.wav")
            
            # Verify results
            assert result == ""  # Should return empty string on error
            # Should be called initial + max_retries times
            assert mock_post.call_count == max_retries + 1
            mock_sleep.assert_called_once()
            mock_exists.assert_called_once_with("test.wav")

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
        max_retries = 1
        transcriber = ElevenLabsTranscriber(api_key="test_key", max_retries=max_retries, retry_delay=0.1)
        
        # Mock the file opening
        with patch("builtins.open", mock_open(read_data=b"audio data")):
            # Test transcription with connection error
            result = transcriber.transcribe_audio("test.wav")
            
            # Verify results
            assert result == ""  # Should return empty string on error
            # Should be called initial + max_retries times
            assert mock_post.call_count == max_retries + 1
            mock_sleep.assert_called_once()
            mock_exists.assert_called_once_with("test.wav")
            
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.os.path.exists')
    def test_transcribe_audio_file_not_found(self, mock_exists):
        """Test handling of file not found error."""
        # Mock file existence check to return False
        mock_exists.return_value = False
        
        # Create transcriber
        transcriber = ElevenLabsTranscriber(api_key="test_key")
        
        # Test transcription with file not found
        result = transcriber.transcribe_audio("nonexistent.wav")
        
        # Verify results
        assert result == ""  # Should return empty string on error
        mock_exists.assert_called_once_with("nonexistent.wav")
    
    @patch('VoiceProcessingToolkit.transcription.elevenlabs.requests.post')
    def test_transcribe_bytes(self, mock_post):
        """Test transcription from bytes."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "text": "This is a bytes transcription."
        }
        mock_post.return_value = mock_response
        
        # Create transcriber with max_retries=0 to simplify testing
        transcriber = ElevenLabsTranscriber(api_key="test_key", max_retries=0)
        
        # Test transcription from bytes
        audio_bytes = b"audio data in bytes"
        result = transcriber.transcribe_bytes(audio_bytes)
        
        # Verify results
        assert result.get("status") == "success"
        assert result.get("text") == "This is a bytes transcription."
        mock_post.assert_called_once() 