import asyncio
import logging
import time

from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager

# Basic configuration
logging.basicConfig(level=logging.INFO)

def main():
    """
    Demonstrates the basic usage of the VoiceProcessingManager.

    This script initializes the VoiceProcessingManager with default settings and runs it to process a voice command.
    It also demonstrates how to register actions with the VoiceProcessingManager that will be triggered when the
    wake word is detected. The processed text is printed to the console. The script uses text-to-speech
    functionality without streaming a custom voice id.

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
    vpm = VoiceProcessingManager.create_default_instance(use_wake_word=True, play_notification_sound=True)

    # Run the voice processing manager with text-to-speech but without streaming
    text = vpm.run(tts=True, voice_id="XB0fDUnXU5powFXDhCwa", streaming=False)

    print(f"Processed text: {text}")


if __name__ == '__main__':
    main()
