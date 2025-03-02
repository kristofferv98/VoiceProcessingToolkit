#!/usr/bin/env python3
import logging
import os
import time
import requests
from typing import Optional, Dict, Any, Union
import uuid

from VoiceProcessingToolkit.interfaces import TranscriberInterface
from VoiceProcessingToolkit.config import default_config

logger = logging.getLogger(__name__)

class ElevenLabsTranscriber(TranscriberInterface):
    """
    A transcriber that uses ElevenLabs Speech-to-Text API to convert audio to text.
    
    Attributes:
        api_key (str): The API key for the ElevenLabs API.
        base_url (str): The base URL for the ElevenLabs API.
        logger (logging.Logger): Logger for this class.
        max_retries (int): Maximum number of retries for API calls.
        retry_delay (float): Delay between retries in seconds.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 max_retries: int = None, 
                 retry_delay: float = None):
        """
        Initialize the ElevenLabs transcriber.
        
        Args:
            api_key: ElevenLabs API key. If not provided, will try to get from environment variable
            max_retries: Maximum number of retries for API calls
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY") or default_config.transcriber.api_key
        self.base_url = "https://api.elevenlabs.io/v1/speech-to-text"
        self.logger = logger
        
        # Set retry parameters
        transcriber_config = default_config.transcriber
        self.max_retries = max_retries if max_retries is not None else transcriber_config.max_retries
        self.retry_delay = retry_delay if retry_delay is not None else transcriber_config.retry_delay
        
        if not self.api_key:
            self.logger.warning("No ElevenLabs API key provided. Transcription will not work.")
        
    def transcribe_audio(self, audio_file_path: str, language: str = "en") -> str:
        """
        Transcribe an audio file using ElevenLabs Speech-to-Text API.
        
        Args:
            audio_file_path: Path to the audio file to transcribe
            language: Language code (default: 'en' for English)
            
        Returns:
            String containing transcription results or empty string if error
        """
        result = self.transcribe_file(audio_file_path, language)
        if result and result.get("status") == "success":
            return result.get("text", "")
        
        # Log error if transcription failed
        error_message = result.get("error", "Unknown error")
        self.logger.error(f"Transcription failed: {error_message}")
        return ""
        
    def transcribe_file(self, audio_file_path: str, language: str = "en") -> Dict[str, Any]:
        """
        Transcribe an audio file using ElevenLabs Speech-to-Text API.
        
        Args:
            audio_file_path: Path to the audio file to transcribe
            language: Language code (default: 'en' for English)
            
        Returns:
            Dictionary containing transcription results or error information
        """
        if not self.api_key:
            return {"status": "error", "error": "No API key provided"}
        
        if not os.path.exists(audio_file_path):
            self.logger.error(f"Audio file not found: {audio_file_path}")
            return {"status": "error", "error": f"Audio file not found: {audio_file_path}"}
        
        # Generate a unique identifier for this transcription request
        request_id = str(uuid.uuid4())
        self.logger.info(f"Starting transcription request {request_id} for file: {audio_file_path}")
        
        # Attempt transcription with retry logic
        retry_count = 0
        while retry_count <= self.max_retries:
            try:
                start_time = time.time()
                self.logger.info(f"Starting transcription of {audio_file_path}")
                
                # Prepare headers with API key
                headers = {
                    "xi-api-key": self.api_key,
                    "Accept": "application/json"
                }
                
                # Create multipart form data
                with open(audio_file_path, "rb") as audio_file:
                    files = {
                        "file": (os.path.basename(audio_file_path), audio_file, "audio/wav")
                    }
                    
                    data = {
                        "model_id": default_config.transcriber.model_id
                    }
                    
                    if language != "en":
                        data["language"] = language
                    
                    self.logger.debug(f"Request {request_id}: Sending transcription request to ElevenLabs API")
                    response = requests.post(
                        self.base_url,
                        headers=headers,
                        files=files,
                        data=data
                    )
                
                # Check for successful response
                if response.status_code == 200:
                    result = response.json()
                    elapsed_time = time.time() - start_time
                    transcript = result.get("text", "")
                    
                    self.logger.info(
                        f"Request {request_id}: Transcription completed in {elapsed_time:.2f}s: "
                        f"{transcript[:50]}{'...' if len(transcript) > 50 else ''}"
                    )
                    
                    return {
                        "status": "success",
                        "text": transcript,
                        "metadata": {
                            "request_id": request_id,
                            "language": language,
                            "file_path": audio_file_path
                        }
                    }
                else:
                    error_msg = f"API request failed with status code {response.status_code}: {response.text}"
                    self.logger.warning(f"Request {request_id}: {error_msg} (Attempt {retry_count + 1}/{self.max_retries + 1})")
                    
                    # For certain status codes, retrying won't help
                    if response.status_code in [400, 401, 403]:
                        break
            
            except Exception as e:
                error_msg = f"Exception during transcription: {str(e)}"
                self.logger.warning(f"Request {request_id}: {error_msg} (Attempt {retry_count + 1}/{self.max_retries + 1})")
            
            # Increment retry count and delay before retrying
            retry_count += 1
            if retry_count <= self.max_retries:
                time.sleep(self.retry_delay)
        
        # If we've exhausted all retries or encountered a non-retryable error
        self.logger.error(f"Request {request_id}: Transcription failed after {retry_count} attempts")
        return {
            "status": "error",
            "error": error_msg if 'error_msg' in locals() else "Unknown error",
            "metadata": {
                "request_id": request_id,
                "language": language,
                "file_path": audio_file_path,
                "attempts": retry_count
            }
        }
        
    def transcribe_bytes(self, audio_bytes: bytes, language: str = "en") -> Dict[str, Any]:
        """
        Transcribe audio from bytes using ElevenLabs Speech-to-Text API.
        
        Args:
            audio_bytes: Audio data as bytes
            language: Language code (default: 'en' for English)
            
        Returns:
            Dictionary containing transcription results or error information
        """
        if not self.api_key:
            return {"status": "error", "error": "No API key provided"}
        
        if not audio_bytes:
            error_msg = "No audio data provided"
            self.logger.error(error_msg)
            return {"status": "error", "error": error_msg}
        
        # Generate a unique identifier for this transcription request
        request_id = str(uuid.uuid4())
        self.logger.info(f"Starting transcription request {request_id} for audio bytes")
        
        # Attempt transcription with retry logic
        retry_count = 0
        while retry_count <= self.max_retries:
            try:
                start_time = time.time()
                self.logger.info("Starting transcription of audio bytes")
                
                # Prepare headers with API key
                headers = {
                    "xi-api-key": self.api_key,
                    "Accept": "application/json"
                }
                
                # Create multipart form data
                files = {
                    "file": ("audio.wav", audio_bytes, "audio/wav")
                }
                
                data = {
                    "model_id": default_config.transcriber.model_id
                }
                
                if language != "en":
                    data["language"] = language
                
                self.logger.debug(f"Request {request_id}: Sending transcription request to ElevenLabs API")
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    files=files,
                    data=data
                )
                
                # Check for successful response
                if response.status_code == 200:
                    result = response.json()
                    elapsed_time = time.time() - start_time
                    transcript = result.get("text", "")
                    
                    self.logger.info(
                        f"Request {request_id}: Transcription completed in {elapsed_time:.2f}s: "
                        f"{transcript[:50]}{'...' if len(transcript) > 50 else ''}"
                    )
                    
                    return {
                        "status": "success",
                        "text": transcript,
                        "metadata": {
                            "request_id": request_id,
                            "language": language
                        }
                    }
                else:
                    error_msg = f"API request failed with status code {response.status_code}: {response.text}"
                    self.logger.warning(f"Request {request_id}: {error_msg} (Attempt {retry_count + 1}/{self.max_retries + 1})")
                    
                    # For certain status codes, retrying won't help
                    if response.status_code in [400, 401, 403]:
                        break
            
            except Exception as e:
                error_msg = f"Exception during transcription: {str(e)}"
                self.logger.warning(f"Request {request_id}: {error_msg} (Attempt {retry_count + 1}/{self.max_retries + 1})")
            
            # Increment retry count and delay before retrying
            retry_count += 1
            if retry_count <= self.max_retries:
                time.sleep(self.retry_delay)
        
        # If we've exhausted all retries or encountered a non-retryable error
        self.logger.error(f"Request {request_id}: Transcription failed after {retry_count} attempts")
        return {
            "status": "error",
            "error": error_msg if 'error_msg' in locals() else "Unknown error",
            "metadata": {
                "request_id": request_id,
                "language": language,
                "attempts": retry_count
            }
        }

if __name__ == '__main__':
    audio_path = "path_to_audio.wav"
    transcriber = ElevenLabsTranscriber()
    transcription = transcriber.transcribe_audio(audio_path)
    if transcription:
        logging.info(f"Transcription: {transcription}") 