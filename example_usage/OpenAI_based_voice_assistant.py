import logging
import os

from dotenv import load_dotenv

from VoiceProcessingManager import text_to_speech, text_to_speech_stream, VoiceProcessingManager
from openai import OpenAI

client = OpenAI()

# os.environ['ELEVENLABS_API_KEY'] = 'your-elevenlabs-api-key'
elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')


class ChatBot():

    def __init__(self, connection):
        self.llm = client
        self.connection = connection
        self.system_message = {"role": "system", "content": """Jarvis is designed to interpret and respond to transcribed audio, treating them as direct 
                        textual inputs during interactions. This includes instances when the user instructs Jarvis 
                        to 'listen to' or similar phrases. The subsequent text provided by user will be treated 
                        as transcribed audio. In order to maintain the illusion of a voice-based assistant, 
                        Jarvis is set not to explicitly refer to these inputs as transcriptions. Instead, 
                        it will process and respond to them as if they were direct audio inputs, despite being 
                        received in text form. This aspect represents an essential part of the system design in 
                        delivering a seamless and immersive user experience, where the user interacts with Jarvis 
                        as if it was dialoguing with a voice-activated assistant. All audio inputs thus 'heard' by Jarvis 
                        will actually be transcribed text provided by user."""},
        self.history = []

    def ask(self, query):
        message = {"role": "User", "content": query}
        self.history.append(message)
        full_chat = [self.system_message] + self.history
        answer = self.llm.prompt(full_chat).choices[0]
        message_answer = {"role": "Assistant", "content": answer.text}
        self.history.append(message_answer)
        print(f"Assistant: {answer.text}")


def on_connect(user_id, connection):
    sessions[user_id] = Chatbot(connection)


def on_message(user_id, query):
    sessions[user_id].ask(query)


def main():


    # Create a VoiceProcessingManager instance with default settings
    vpm = VoiceProcessingManager.create_default_instance(use_wake_word=True, play_notification_sound=True,
                                                         wake_word='computer')

    while:
        try:
            # Run the voice processing manager with transcription and text-to-speech
            transcription = vpm.run(transcription=True, tts=True)

            # Send the transcription to the chatbot
            chatbot = ChatBot(transcription)
            chatbot.ask(transcription)

            text = text_to_speech_stream(text=transcription)

            print(text)


if __name__ == '__main__':
    main()
