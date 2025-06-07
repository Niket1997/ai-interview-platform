import asyncio
from google.genai import types
from google import genai
from dotenv import load_dotenv
import os
import pyaudio

load_dotenv()


# audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RECEIVE_SAMPLE_RATE = 24000

# pyaudio: audio stream
p = pyaudio.PyAudio()

# default stream
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RECEIVE_SAMPLE_RATE, output=True)

# gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# streaming_tts: generate audio from text using google tts
async def streaming_tts(text_input):
    """
    Uses Google's Live API for true streaming TTS.
    Chunks are generated automatically by the model - no manual splitting needed!
    """

    model = "gemini-2.5-flash-preview-native-audio-dialog"
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction="Speak in a cheerful and positive tone.",
    )

    print("🎵 Starting true streaming TTS with Live API...")

    try:
        # Use the Live API for true streaming
        async with client.aio.live.connect(model=model, config=config) as session:
            # Send the text
            await session.send_client_content(
                turns={"role": "user", "parts": [{"text": text_input}]},
                turn_complete=True,
            )

            # Receive and play chunks as they arrive
            async for response in session.receive():
                if response.data is not None:
                    # Play each chunk immediately as it arrives
                    stream.write(response.data)

                # Check if generation is complete
                if hasattr(response, "server_content") and response.server_content:
                    if (
                        hasattr(response.server_content, "generation_complete")
                        and response.server_content.generation_complete
                    ):
                        print("✅ Streaming complete!")
                        break

    except Exception as e:
        print(f"❌ Error Generating Audio: {e}")


if __name__ == "__main__":
    text_to_stream = """
    Hello there! This is a longer piece of text that demonstrates streaming audio. 
    Each sentence will be converted to audio separately. 
    This allows for real-time playback as the audio is being generated. 
    Pretty cool, right?
    """
    asyncio.run(streaming_tts(text_to_stream))
