import logging
import os
import sys
import signal

import autogen
from dotenv import load_dotenv
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent
from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from VoiceProcessingToolkit.VoiceProcessingManager import text_to_speech_stream

def setup_logging():
    # Configure logging
    logging.basicConfig(level=logging.INFO)

def load_environment_variables():
    # Load environment variables
    load_dotenv()

# Retrieve API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
picovoice_api_key = os.getenv("PICOVOICE_APIKEY")

# Define configuration for language models
config_list = [
    {"model": "gpt-4-1106-preview", "api_key": openai_api_key},
    {"model": "gpt-3.5-turbo-1106-preview", "api_key": openai_api_key},
]
llm_config = {"config_list": config_list, "cache_seed": 42}

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

# Initialize the User Proxy Agent to represent the user in the conversation
user_proxy = autogen.UserProxyAgent(
    "user_proxy",
    max_consecutive_auto_reply=10,
    human_input_mode="NEVER",
    system_message="A human admin for Jarvis",
    is_termination_msg=lambda x: "content" in x and x["content"] is not None and x["content"].rstrip().endswith("TERMINATE" or "TERMINATE."),
)

def get_user_input():
    """
    Captures user input via voice, transcribes it, and returns the transcription.
    """
    vpm = VoiceProcessingManager.create_default_instance(
        use_wake_word=True,
        play_notification_sound=True,
        wake_word="jarvis",
        min_recording_length=2,
    )

    logging.info("Say something to Jarvis")

    # Run the voice processing manager to capture and transcribe user input
    transcription = vpm.run(tts=False, streaming=False)
    logging.info(f"Processed text: {transcription}")

    return transcription


def initiate_jarvis(transcription):
    user_proxy.initiate_chat(
        recipient=assistant,
        message=transcription,
        clear_history=False,

    )
    # Retrieve the latest response from Jarvis
    latest_message = assistant.last_message().get("content", "")
    stripped_answer = latest_message.replace("TERMINATE", "").strip()

    # Convert Jarvis's response to speech and stream it
    text_to_speech_stream(text=stripped_answer, api_key=elevenlabs_api_key)
    logging.info(f"Jarvis said: {stripped_answer}")


def initiate_jarvis_loop():
    """
    Continuously interacts with Jarvis by capturing user input, transcribing it, and obtaining responses.
    """
    while True:
        transcription = get_user_input()
        initiate_jarvis(transcription)


if __name__ == '__main__':
    initiate_jarvis_loop()

def get_user_input(vpm):
    """
    Captures user input via voice, transcribes it, and returns the transcription.

    Args:
        vpm (VoiceProcessingManager): Instance of VoiceProcessingManager to capture and transcribe user input.

    Returns:
        str or None: Transcribed text or None if transcription fails.
    """
    logging.info("Say something to Jarvis")

    # Run the voice processing manager to capture and transcribe user input
    transcription = vpm.run(tts=False, streaming=False)
    logging.info(f"Processed text: {transcription}")

    return transcription

def initiate_jarvis(transcription, assistant, user_proxy):
    """
    Sends the transcribed user input to Jarvis and handles the response.

    Args:
        transcription (str): Transcribed user input.
        assistant (GPTAssistantAgent): Instance of GPTAssistantAgent to process the input.
        user_proxy (autogen.UserProxyAgent): Instance of UserProxyAgent representing the user.
    """
    if transcription is None:
        logging.warning("No transcription received.")
        return

    user_proxy.initiate_chat(
        recipient=assistant,
        message=transcription,
        clear_history=False,
    )
    # Retrieve the latest response from Jarvis
    latest_message = assistant.last_message().get("content", "")
    stripped_answer = latest_message.replace("TERMINATE", "").strip()

    # Convert Jarvis's response to speech and stream it
    text_to_speech_stream(text=stripped_answer, api_key=elevenlabs_api_key)
    logging.info(f"Jarvis said: {stripped_answer}")

def initiate_jarvis_loop(vpm, assistant, user_proxy):
    """
    Continuously interacts with Jarvis by capturing user input, transcribing it, and obtaining responses.
    """
    try:
        while True:
            transcription = get_user_input(vpm)
            initiate_jarvis(transcription, assistant, user_proxy)
    except KeyboardInterrupt:
        logging.info("Exiting the Jarvis loop.")
        sys.exit(0)

def main():
    setup_logging()
    load_environment_variables()

    # Initialize the VoiceProcessingManager
    vpm = VoiceProcessingManager.create_default_instance(
        use_wake_word=True,
        play_notification_sound=True,
        wake_word="jarvis",
        min_recording_length=2,
    )

    # Initialize the GPTAssistantAgent and UserProxyAgent
    assistant = create_assistant()
    user_proxy = create_user_proxy()

    # Start the Jarvis interaction loop
    initiate_jarvis_loop(vpm, assistant, user_proxy)

if __name__ == '__main__':
    main()
