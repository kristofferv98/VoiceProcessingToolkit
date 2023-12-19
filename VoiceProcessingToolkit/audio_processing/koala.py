import logging

logger = logging.getLogger(__name__)
import struct
import wave

from pvkoala import create, KoalaActivationLimitError


class KoalaAudioProcessor:
    """
    KoalaAudioProcessor handles audio processing using the Koala engine.
    """

    def __init__(self, access_key: str = None, library_path: str = None, model_path: str = None) -> None:
        self.koala = create(access_key=access_key, model_path=model_path, library_path=library_path)

    def process_audio(self, input_filename: str, output_filename: str) -> None:
        # Define the directory relative to the current script's location
        if not input_filename.lower().endswith('.wav'):
            raise ValueError('Given argument input_filename must have WAV file extension')

        if not output_filename.lower().endswith('.wav'):
            raise ValueError('Given argument output_filename must have WAV file extension')

        if input_filename == output_filename:
            raise ValueError('The script cannot overwrite its input filename')

        koala = self.koala
        length_sec = 0.0

        logger.info("Starting audio processing for %s", input_filename)
        try:

            with wave.open(input_filename, 'rb') as input_file:
                if input_file.getframerate() != koala.sample_rate:
                    raise ValueError(f'Invalid sample rate of {input_file.getframerate()}. Koala only accepts '
                                     f'{koala.sample_rate}')
                if input_file.getnchannels() != 1:
                    raise ValueError('This script can only process single-channel WAV files')
                if input_file.getsampwidth() != 2:
                    raise ValueError('This script can only process WAV files with 16-bit PCM encoding')
                input_length = input_file.getnframes()

                with wave.open(output_filename, 'wb') as output_file:
                    output_file.setnchannels(1)
                    output_file.setsampwidth(2)
                    output_file.setframerate(koala.sample_rate)

                    start_sample = 0
                    while start_sample < input_length + koala.delay_sample:
                        end_sample = start_sample + koala.frame_length
                        frame_buffer = input_file.readframes(koala.frame_length)
                        num_samples_read = len(frame_buffer) // struct.calcsize('h')
                        input_frame = struct.unpack('%dh' % num_samples_read, frame_buffer)
                        if num_samples_read < koala.frame_length:
                            input_frame = input_frame + (0,) * (koala.frame_length - num_samples_read)

                        output_frame = koala.process(input_frame)

                        if end_sample > koala.delay_sample:
                            if end_sample > input_length + koala.delay_sample:
                                output_frame = output_frame[:input_length + koala.delay_sample - start_sample]
                            if start_sample < koala.delay_sample:
                                output_frame = output_frame[koala.delay_sample - start_sample:]
                            output_file.writeframes(struct.pack('%dh' % len(output_frame), *output_frame))

                        start_sample = end_sample

                    logging.info(f'Audio processed and saved as {output_filename}')

        except FileNotFoundError as e:
            logging.exception("The input file was not found: %s", e)
        except PermissionError as e:
            logging.exception("Permission denied when accessing the input file: %s", e)
        except KoalaActivationLimitError as e:
            logging.exception('Koala activation limit error: %s', e)
        except wave.Error as e:
            logging.exception("Wave file error: %s", e)
        except Exception as e:
            logging.exception("An unexpected error occurred during audio processing: %s", e)
        finally:
            if length_sec > 0:
                logging.info('%.2f seconds of audio have been written to %s', length_sec, output_filename)

            self.cleanup()

    def cleanup(self) -> None:
        """
        Clean up the processor by deleting the Koala handle.
        """
        self.koala.delete()


if __name__ == '__main__':
    input_audio_path = "path_to_input.wav"
    output_audio_path = "path_to_output.wav"
    api_access_key = "your_koala_access_key"
    processor = KoalaAudioProcessor(api_access_key)
    processor.process_audio(input_audio_path, output_audio_path)
    processor.cleanup()
