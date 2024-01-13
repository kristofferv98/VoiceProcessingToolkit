import os

import autogen
from dotenv import load_dotenv
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent
from VoiceProcessingManager import text_to_speech_stream, VoiceProcessingManager

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
os.getenv("ELEVENLABS_API_KEY")
os.getenv("PICOVOICE_APIKEY")

config_list = [
    {
        "model": "gpt-4-1106-preview",
        "api_key": openai_api_key
    },
    {
        "model": "gpt-3.5-turbo-1106-preview",
        "api_key": openai_api_key
    },
]
llm_config = {
    "config_list": config_list,
    "cache_seed": 42,
}

# Create the agent that uses the LLM.
assistant = GPTAssistantAgent(
    name="agent",
    instructions="""You are a personal assistant named Jarvis.
    
    You are designed to assist the user with their tasks, 
    Refine dialogue comprehension to capture subtleties and implicit cues, ensuring responses are 
    not only accurate but also contextually enriched. Evolve to predict and suggest actions not 
    only based on explicit commands but also from inferred intentions, enhancing the support 
    offered. As for your character traits, you should be helpful, attentive, and efficient while 
    extremly inteligent. You should have a professional yet friendly tone, much like a dedicated 
    personal assistant, unless asked not too. You should be able to engage in casual conversation 
    but also provide detailed assistance when needed. Reflecting on your personality, you should 
    be extremely intelligent, with a hint of dry humor. You should respond in a concise manner, 
    always within three sentences unless a comprehecive answer is asked for. "Example: (Good day, 
    Kristoffer. How can I assist you today? TERMINATE)"
    
    Jarvis is designed to interpret and respond to transcribed audio, treating them as direct 
    textual inputs during interactions. This includes instances when the user instructs Jarvis 
    to 'listen to' or similar phrases. The subsequent text provided by user will be treated 
    as transcribed audio. In order to maintain the illusion of a voice-based assistant, 
    Jarvis is set not to explicitly refer to these inputs as transcriptions. Instead, 
    it will process and respond to them as if they were direct audio inputs, despite being 
    received in text form. This aspect represents an essential part of the system design in 
    delivering a seamless and immersive user experience, where the user interacts with Jarvis 
    as if it was dialoguing with a voice-activated assistant. All audio inputs thus 'heard' by Jarvis 
    will actually be transcribed text provided by user.Reply then say TERMINATE to 
    indicate your message is finished but in the same message.""",
    llm_config=llm_config)

# Create the agent that represents the user in the conversation.
user_proxy = autogen.UserProxyAgent(
    "user_proxy",
    max_consecutive_auto_reply=10,
    human_input_mode="NEVER",
    system_message=f"""A human admin for Jarvis""",
    is_termination_msg=lambda x: "content" in x and x["content"] is not None and x["content"].rstrip().endswith(
        "TERMINATE" or "TERMINATE."),
)


def get_user_input():
    # Create a VoiceProcessingManager instance with default settings
    vpm = VoiceProcessingManager.create_default_instance(use_wake_word=True, play_notification_sound=True,
                                                         wake_word='jarvis', min_recording_length=2)

    # Run the voice processing manager with transcription and text-to-speech
    print("Say something to Jarvis")
    transcription = vpm.run(transcription=True, tts=False)
    # cleanup
    return transcription


def initiate_jarvis():
    transcription = get_user_input()

    user_proxy.initiate_chat(
        recipient=assistant,
        message=transcription,
        clear_history=False,

    )

    # Get and print the latest message
    latest_message = assistant.last_message()["content"]
    stipped_answer = latest_message.replace("TERMINATE", "").strip()
    final_answer = text_to_speech_stream(text=stipped_answer)
    print("Jarvis said: ", final_answer)

def initiate_jarvis_loop():
    while True:
        initiate_jarvis()


if __name__ == '__main__':
    initiate_jarvis_loop()
