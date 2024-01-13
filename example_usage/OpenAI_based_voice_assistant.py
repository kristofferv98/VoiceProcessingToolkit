

from VoiceProcessingManager import VoiceProcessingManager
from openai import OpenAI




class ChatBot():

    def __init__(self, connection):
        self.llm = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.connection = connection
        self.system_message = {"role": "system", "content": "Jarvis is designed to interpret and respond to transcribed audio, treating them as direct 
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
    global sessions
    if 'sessions' not in globals():
        sessions = {}
    sessions[user_id] = ChatBot(connection)


def on_message(user_id, query):
    sessions[user_id].ask(query)


def main():

    global sessions
    sessions = {}

    # Create a VoiceProcessingManager instance with default settings
    vpm = VoiceProcessingManager.create_default_instance(use_wake_word=True, play_notification_sound=True,
                                                         wake_word='computer')

    while:
        try:
            # Run the voice processing manager with transcription and text-to-speech
            transcription = vpm.run(transcription=True)

            # Send the transcription to the chatbot
            user_id = 'default_user'  # This should be replaced with actual user identification logic
            if user_id not in sessions:
                on_connect(user_id, None)
            sessions[user_id].ask(transcription)

            # Assuming the text_to_speech functionality is part of the VoiceProcessingManager
            vpm.text_to_speech(text=transcription)

            print(text)


if __name__ == '__main__':
    main()
