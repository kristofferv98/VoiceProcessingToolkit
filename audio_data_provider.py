# === INTERFACES / ABSTRACT CLASSES SECTION ===
class AudioDataProvider:
    """
    Interface for providing audio data to the VAD.

    Implement this interface in a separate module or file where the actual audio data handling is defined.
    """

    def get_audio_frame(self):
        """
        Should be implemented to return a single frame of audio data.
        """
        raise NotImplementedError
