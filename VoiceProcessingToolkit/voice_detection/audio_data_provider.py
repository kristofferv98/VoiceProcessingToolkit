# === INTERFACES / ABSTRACT CLASSES SECTION ===
class AudioDataProvider:
    """
    Interface for providing audio data to the VAD.
    Responsibilities:
    - Provide a consistent method to supply audio data frames to the VAD.
    """

    def get_audio_frame(self):
        """
        Should be implemented to return a single frame of audio data.
        """
        raise NotImplementedError
