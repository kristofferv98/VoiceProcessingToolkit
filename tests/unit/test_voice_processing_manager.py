"""
Unit tests for the VoiceProcessingManager class.
"""
import os
import pytest
import tempfile
import numpy as np
from unittest.mock import Mock, patch, MagicMock, call

from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager


class TestVoiceProcessingManager:
    """Test cases for the VoiceProcessingManager class."""

    def test_initialization(self, voice_processing_manager):
        """Test that the manager initializes with the correct parameters."""
        assert voice_processing_manager.wake_word == 'test'
        assert voice_processing_manager.sensitivity == 0.75
        assert voice_processing_manager.output_directory == 'test_output'
        assert voice_processing_manager.voice_threshold == 0.8
        assert voice_processing_manager.silence_limit == 2.0
        assert voice_processing_manager.inactivity_limit == 2.0
        assert voice_processing_manager.min_recording_length == 2.0
        assert voice_processing_manager.buffer_length == 2.0
        assert voice_processing_manager.use_wake_word is True
        assert voice_processing_manager.save_wake_word_recordings is False
        assert voice_processing_manager.play_notification_sound is False

    def test_create_output_directory(self, voice_processing_manager):
        """Test that the output directory is created."""
        voice_processing_manager.create_output_directory()
        voice_processing_manager.create_output_directory.assert_called_once()

    @patch('numpy.frombuffer')
    @patch('numpy.mean')
    def test_is_silent(self, mock_mean, mock_frombuffer, voice_processing_manager):
        """Test the is_silent method."""
        # Setup mocks
        mock_frombuffer.return_value = np.array([0.5, 0.6, 0.7])
        mock_mean.return_value = 0.6
        
        # Test not silent
        voice_processing_manager.voice_threshold = 0.5
        voice_processing_manager.is_silent.return_value = False
        assert not voice_processing_manager.is_silent(b'audio_data')
        
        # Test silent
        voice_processing_manager.voice_threshold = 0.7
        voice_processing_manager.is_silent.return_value = True
        assert voice_processing_manager.is_silent(b'audio_data')
        
        # Verify calls
        voice_processing_manager.is_silent.assert_called_with(b'audio_data')

    @patch('time.time')
    def test_listen_for_wake_word(self, mock_time, voice_processing_manager, mock_audio_stream_manager):
        """Test the listen_for_wake_word method."""
        # Setup
        mock_time.return_value = 100.0
        mock_audio_stream_manager.read.return_value = b'audio_data'
        voice_processing_manager.is_silent.return_value = True
        voice_processing_manager.wake_word_detected.return_value = True
        
        # Test with wake word detected
        result = voice_processing_manager.listen_for_wake_word()
        assert result is True
        
        # Verify calls
        voice_processing_manager.listen_for_wake_word.assert_called_once()

    def test_wake_word_detected(self, voice_processing_manager):
        """Test the wake_word_detected method."""
        # Setup
        voice_processing_manager.get_prediction.return_value = 0.8
        voice_processing_manager.sensitivity = 0.7
        
        # Test with wake word detected
        result = voice_processing_manager.wake_word_detected(b'audio_data')
        assert result is True
        
        # Test with wake word not detected
        voice_processing_manager.wake_word_detected.return_value = False
        result = voice_processing_manager.wake_word_detected(b'audio_data')
        assert result is False

    @patch('time.time')
    def test_record_phrase(self, mock_time, voice_processing_manager, mock_audio_stream_manager):
        """Test the record_phrase method."""
        # Setup
        mock_time.side_effect = [100.0, 101.0, 102.0, 103.0]
        mock_audio_stream_manager.read.return_value = b'audio_data'
        voice_processing_manager.is_silent.side_effect = [False, False, True, True]
        
        # Test recording
        result = voice_processing_manager.record_phrase()
        
        # Verify result
        assert isinstance(result, list)
        assert result == [b'audio_data']
        
        # Verify calls
        voice_processing_manager.record_phrase.assert_called_once()

    def test_save_audio(self, voice_processing_manager, temp_dir):
        """Test the save_audio method."""
        # Setup
        voice_processing_manager.output_directory = temp_dir
        voice_processing_manager.create_output_directory()
        
        # Test
        audio_data = [b'data1', b'data2']
        result = voice_processing_manager.save_audio(audio_data)
        
        # Verify
        assert isinstance(result, str)
        voice_processing_manager.save_audio.assert_called_once_with(audio_data)

    def test_run_with_transcription(self, voice_processing_manager, mock_transcriber):
        """Test the run method with transcription enabled."""
        # Setup
        voice_processing_manager.listen_for_wake_word = Mock(return_value=True)
        voice_processing_manager.record_phrase = Mock(return_value=[b'audio_data'])
        voice_processing_manager.save_audio = Mock(return_value='test.wav')
        
        # Test
        result = voice_processing_manager.run(transcription=True)
        
        # Verify
        assert result == "Sample transcription"
        mock_transcriber.transcribe_audio.assert_called_once_with('test.wav')

    def test_run_without_transcription(self, voice_processing_manager, mock_transcriber):
        """Test the run method without transcription."""
        # Setup
        voice_processing_manager.listen_for_wake_word = Mock(return_value=True)
        voice_processing_manager.record_phrase = Mock(return_value=[b'audio_data'])
        voice_processing_manager.save_audio = Mock(return_value='test.wav')
        
        # Test
        result = voice_processing_manager.run(transcription=False)
        
        # Verify
        assert result is None
        mock_transcriber.transcribe_audio.assert_not_called()

    def test_run_no_wake_word(self, voice_processing_manager):
        """Test the run method when wake word is not detected."""
        # Setup
        voice_processing_manager.listen_for_wake_word = Mock(return_value=False)
        
        # Test
        result = voice_processing_manager.run()
        
        # Verify
        assert result is None
        voice_processing_manager.listen_for_wake_word.assert_called_once()

    def test_run_with_keyboard_interrupt(self, voice_processing_manager):
        """Test the run method when a KeyboardInterrupt occurs."""
        # Setup
        voice_processing_manager.listen_for_wake_word = Mock(side_effect=KeyboardInterrupt())
        
        # Test and verify
        with pytest.raises(KeyboardInterrupt):
            voice_processing_manager.run() 