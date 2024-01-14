import logging
import os

from VoiceProcessingManager import VoiceProcessingManager


os.environ['PICOVOICE_APIKEY'] = 'your-picovoice-api-key'
os.environ['OPENAI_API_KEY'] = 'your-openai-api-key'
os.environ['ELEVENLABS_API_KEY'] = 'your-elevenlabs-api-key'

def main():
    """
    This example demonstrates the basic setup and usage of the VoiceProcessingManager.

    The script initializes the VoiceProcessingManager with default settings, and runs the manager to process voice
    commands. The processed text is printed to the console. It showcases the use of text-to-speech functionality
    without streaming.

    Some basic voice ids can be found here:
    Adam: pNInz6obpgDQGcFmaJgB
    Antoni: ErXwobaYiN019PkySvjV
    Arnold: VR6AewLTigWG4xSOukaG
    Bella: EXAVITQu4vr4xnSDxMaL
    Callum: N2lVS1w4EtoT3dr4eOWO
    Charlie: IKne3meq5aSn9XLyUdCD
    Charlotte: XB0fDUnXU5powFXDhCwa
    Clyde: 2EiwWnXFnvU5JabPnv8n
    Daniel: onwK4e9ZLuTAKqWW03F9
    Dave: CYw3kZ02Hs0563khs1Fj
    Domi: AZnzlk1XvdvUeBnXmlld
    Dorothy: ThT5KcBeYPX3keUQqHPh
    Elli: MF3mGyEYCl7XYWbV9V6O
    Emily: LcfcDJNUP1GQjkzn1xUU
    Ethan: g5CIjZEefAph4nQFvHAz
    Fin: D38z5RcWu1voky8WS1ja
    Freya: jsCqWAovK2LkecY7zXl4
    Gigi: jBpfuIE2acCO8z3wKNLl
    Giovanni: zcAOhNBS3c14rBihAFp1
    Glinda: z9fAnlkpzviPz146aGWa
    Grace: oWAxZDx7w5VEj9dCyTzz
    Harry: SOYHLrjzK2X1ezoPC6cr
    James: ZQe5CZNOzWyzPSCn5a3c
    Jeremy: bVMeCyTHy58xNoL34h3p
    Jessie: t0jbNlBVZ17f02VDIeMI
    Joseph: Zlb1dXrM653N07WRdFW3
    Josh: TxGEqnHWrfWFTfGW9XjX
    Liam: TX3LPaxmHKxFdv7VOQHJ
    Matilda: XrExE9yKIg1WjnnlVkGX
    Matthew: Yko7PKHZNXotIFUBG7I9
    Michael: flq6f7yk4E4fJM5XTYuZ
    Mimi: zrHiDhphv9ZnVXBqCLjz
    Nicole: piTKgcLEGmPE4e6mEKli
    Patrick: ODq5zmih8GrVes37Dizd
    Rachel: 21m00Tcm4TlvDq8ikWAM
    Ryan: wViXBPUzp2ZZixB1xQuM
    Sam: yoZ06aMxZJJ28mfd3POQ
    Serena: pMsXgVXv3BLzUgSXRplE
    Thomas: GBv7mTt0atIp3Br8iCZE

    """
    # Create a VoiceProcessingManager instance with default settings
    vpm = VoiceProcessingManager.create_default_instance(use_wake_word=True, play_notification_sound=True,
                                                         wake_word='jarvis')

    # Run the voice processing manager with transcription and text-to-speech
    text = vpm.run(transcription=True, tts=True)
    print(f"Processed text: {text}")






if __name__ == '__main__':
    while True:
        main()
