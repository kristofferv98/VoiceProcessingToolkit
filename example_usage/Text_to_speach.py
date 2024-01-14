from VoiceProcessingToolkit.VoiceProcessingManager import text_to_speech_stream
from dotenv import load_dotenv

import os
import logging

# logging.basicConfig(level=logging.INFO)
load_dotenv()

# Set environment variables for API keys
os.getenv('PICOVOICE_APIKEY')
os.getenv('OPENAI_API_KEY')
elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')



def main():
    """
    This example demonstrates the text to speech functionality with text as input.

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

    text = "Hello, my name is Dorothy. I am a voice assistant. How can I help you?"
    voice_id = "ThT5KcBeYPX3keUQqHPh"
    api_key = elevenlabs_api_key

    # uncomment the following line to use text_to_speech instead of text_to_speech_stream
    # text_to_speech(text=text, api_key=api_key, voice_id=voice_id)

    text = text_to_speech_stream(text=text, api_key=api_key, voice_id=voice_id)

    print(text)


if __name__ == '__main__':
    main()
