#!/usr/bin/env python3
import logging
import os
import time
import requests
from typing import Optional, Dict, Any, Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (requests.exceptions.RequestException,)
) -> Callable:
    """
    Decorator that retries a function on specified exceptions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry on
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed. Last error: {str(e)}")
                        raise last_exception
            
            raise last_exception
        return wrapper
    return decorator

class ElevenLabsTranscriber:
    """
    A transcriber that uses ElevenLabs Speech-to-Text API to convert audio to text.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ElevenLabs transcriber.
        
        Args:
            api_key: ElevenLabs API key. If not provided, will try to get from environment variable
        """
        self._logger = logger
        self._api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        
        if not self._api_key:
            self._logger.warning("No ElevenLabs API key provided. Transcription will not work.")
        
        self._api_url = "https://api.elevenlabs.io/v1/speech-to-text"
        
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
        return result.get("text", "")
        
    @retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
    def transcribe_file(self, audio_file_path: str, language: str = "en") -> Dict[str, Any]:
        """
        Transcribe an audio file using ElevenLabs Speech-to-Text API.
        
        Args:
            audio_file_path: Path to the audio file to transcribe
            language: Language code (default: 'en' for English)
            
        Returns:
            Dictionary containing transcription results or error information
        """
        if not self._api_key:
            return {"error": "No API key provided", "text": ""}
        
        if not os.path.exists(audio_file_path):
            self._logger.error(f"Audio file not found: {audio_file_path}")
            return {"error": f"Audio file not found: {audio_file_path}", "text": ""}
        
        try:
            start_time = time.time()
            self._logger.info(f"Starting transcription of {audio_file_path}")
            
            # Prepare headers with API key
            headers = {
                "xi-api-key": self._api_key,
                "Accept": "application/json"
            }
            
            # Create multipart form data
            with open(audio_file_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(audio_file_path), audio_file, "audio/wav")
                }
                
                data = {
                    "model_id": "scribe_v1",
                    "language_code": language
                }
                
                # Make API request
                response = requests.post(
                    self._api_url,
                    headers=headers,
                    files=files,
                    data=data
                )
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                elapsed_time = time.time() - start_time
                transcript = result.get("text", "")
                
                self._logger.info(
                    f"Transcription completed in {elapsed_time:.2f}s: "
                    f"{transcript[:50]}{'...' if len(transcript) > 50 else ''}"
                )
                
                return {
                    "text": transcript,
                    "elapsed_time": elapsed_time,
                    "raw_response": result
                }
            else:
                self._logger.error(
                    f"Transcription failed with status {response.status_code}: {response.text}"
                )
                return {
                    "error": f"API error: {response.status_code}",
                    "text": "",
                    "raw_response": response.text
                }
                
        except Exception as e:
            self._logger.error(f"Error during transcription: {str(e)}")
            return {"error": str(e), "text": ""}
        
    @retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
    def transcribe_bytes(self, audio_bytes: bytes, language: str = "en") -> Dict[str, Any]:
        """
        Transcribe audio from bytes using ElevenLabs Speech-to-Text API.
        
        Args:
            audio_bytes: Audio data as bytes
            language: Language code (default: 'en' for English)
            
        Returns:
            Dictionary containing transcription results or error information
        """
        if not self._api_key:
            return {"error": "No API key provided", "text": ""}
        
        try:
            start_time = time.time()
            self._logger.info("Starting transcription of audio bytes")
            
            # Prepare headers with API key
            headers = {
                "xi-api-key": self._api_key,
                "Accept": "application/json"
            }
            
            # Create multipart form data
            files = {
                "file": ("audio.wav", audio_bytes, "audio/wav")
            }
            
            data = {
                "model_id": "scribe_v1",
                "language_code": language
            }
            
            # Make API request
            response = requests.post(
                self._api_url,
                headers=headers,
                files=files,
                data=data
            )
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                elapsed_time = time.time() - start_time
                transcript = result.get("text", "")
                
                self._logger.info(
                    f"Transcription completed in {elapsed_time:.2f}s: "
                    f"{transcript[:50]}{'...' if len(transcript) > 50 else ''}"
                )
                
                return {
                    "text": transcript,
                    "elapsed_time": elapsed_time,
                    "raw_response": result
                }
            else:
                self._logger.error(
                    f"Transcription failed with status {response.status_code}: {response.text}"
                )
                return {
                    "error": f"API error: {response.status_code}",
                    "text": "",
                    "raw_response": response.text
                }
                
        except Exception as e:
            self._logger.error(f"Error during transcription: {str(e)}")
            return {"error": str(e), "text": ""}

if __name__ == '__main__':
    audio_path = "path_to_audio.wav"
    transcriber = ElevenLabsTranscriber()
    transcription = transcriber.transcribe_audio(audio_path)
    if transcription:
        logging.info(f"Transcription: {transcription}") 