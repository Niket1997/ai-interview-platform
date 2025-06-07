from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import pyaudio
from google.genai.types import Blob
import threading
import queue
import time

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# Non-streaming version (current)
def simple_tts(text_input):
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text_input,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Kore",
                    )
                )
            ),
        ),
    )

    data = response.candidates[0].content.parts[0].inline_data.data
    return data


# Streaming version for longer text
def streaming_tts(long_text):
    """
    For longer text, you'd want to:
    1. Split text into chunks (sentences/phrases)
    2. Generate audio for each chunk
    3. Play audio while generating the next chunk
    """

    # Split text into sentences for streaming
    sentences = long_text.split(". ")
    audio_queue = queue.Queue()

    def generate_audio_chunks():
        """Generate audio for each sentence and put in queue"""
        for sentence in sentences:
            if sentence.strip():
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash-preview-tts",
                        contents=f"Say: {sentence}",
                        config=types.GenerateContentConfig(
                            response_modalities=["AUDIO"],
                            speech_config=types.SpeechConfig(
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name="Kore",
                                    )
                                )
                            ),
                        ),
                    )

                    audio_data = (
                        response.candidates[0].content.parts[0].inline_data.data
                    )
                    audio_queue.put(audio_data)
                    print(f"Generated audio for: '{sentence[:50]}...'")

                except Exception as e:
                    print(f"Error generating audio for sentence: {e}")

        # Signal end of generation
        audio_queue.put(None)

    return audio_queue, generate_audio_chunks


FORMAT = pyaudio.paInt16
CHANNELS = 1
RECEIVE_SAMPLE_RATE = 24000

p = pyaudio.PyAudio()


def test_audio_parameters():
    """Test different audio parameters to find the best sound quality"""

    print("=== Testing Audio Parameters ===")

    # Get sample audio
    simple_audio = simple_tts("Say cheerfully: Have a wonderful day!")

    # Common sample rates for TTS
    sample_rates = [16000, 22050, 24000, 44100, 48000]

    for rate in sample_rates:
        print(f"\n--- Testing sample rate: {rate} Hz ---")
        print("Press Enter after listening to continue to next rate...")

        try:
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=rate, output=True)

            stream.write(simple_audio)
            stream.stop_stream()
            stream.close()

            input()  # Wait for user input

        except Exception as e:
            print(f"Error with rate {rate}: {e}")


def play_with_rate(audio_data, sample_rate):
    """Play audio with specific sample rate"""
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=sample_rate, output=True)

    stream.write(audio_data)
    stream.stop_stream()
    stream.close()


# Default stream (you can modify this rate based on testing)
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RECEIVE_SAMPLE_RATE, output=True)


def play_audio(audio_data):
    # Write the raw audio data directly to the stream
    stream.write(audio_data)


def play_streaming_audio(audio_queue, generator_func):
    """Play audio chunks as they become available"""

    # Start generation in background thread
    generator_thread = threading.Thread(target=generator_func)
    generator_thread.start()

    print("Starting streaming playback...")

    while True:
        try:
            # Get next audio chunk (blocks until available)
            audio_data = audio_queue.get(timeout=30)  # 30 second timeout

            if audio_data is None:  # End signal
                break

            print("Playing audio chunk...")
            play_audio(audio_data)

        except queue.Empty:
            print("Timeout waiting for audio data")
            break
        except Exception as e:
            print(f"Error playing audio: {e}")

    generator_thread.join()
    print("Streaming complete!")


# True streaming version using Google's Live API
async def true_streaming_tts(text_input):
    """
    Uses Google's Live API for true streaming TTS.
    Chunks are generated automatically by the model - no manual splitting needed!
    """

    model = "gemini-2.5-flash-preview-native-audio-dialog"
    config = types.LiveConnectConfig(response_modalities=["AUDIO"])

    print("🎵 Starting true streaming TTS with Live API...")

    try:
        # Use the Live API for true streaming
        async with client.aio.live.connect(model=model, config=config) as session:
            # Send the text
            await session.send_client_content(
                turns={"role": "user", "parts": [{"text": text_input}]},
                turn_complete=True,
            )

            print("🔊 Audio chunks arriving...")

            # Receive and play chunks as they arrive
            async for response in session.receive():
                if response.data is not None:
                    # Play each chunk immediately as it arrives
                    stream.write(response.data)
                    print("🎶 Playing chunk...")

                # Check if generation is complete
                if hasattr(response, "server_content") and response.server_content:
                    if (
                        hasattr(response.server_content, "generation_complete")
                        and response.server_content.generation_complete
                    ):
                        print("✅ Streaming complete!")
                        break

    except Exception as e:
        print(f"❌ Error with Live API: {e}")
        print("💡 Falling back to manual chunking method...")
        return await manual_streaming_fallback(text_input)


async def manual_streaming_fallback(text_input):
    """Fallback to manual chunking if Live API fails"""
    audio_queue, generator_func = streaming_tts(text_input)
    play_streaming_audio(audio_queue, generator_func)


# Example usage
if __name__ == "__main__":
    print("Choose an option:")
    print("1. Test audio parameters (find correct sample rate)")
    print("2. Simple TTS")
    print("3. Manual streaming TTS (sentence-by-sentence)")
    print("4. True streaming TTS (Google Live API)")

    choice = input("Enter choice (1-4): ").strip()

    if choice == "1":
        test_audio_parameters()
    elif choice == "2":
        print("=== Simple TTS (Current settings) ===")
        text_to_speak = input("Enter text to convert to speech: ")
        simple_audio = simple_tts(text_to_speak)
        play_audio(simple_audio)
    elif choice == "3":
        print("=== Manual Streaming TTS Demo ===")
        long_text = """Hello there! This is a longer piece of text that demonstrates streaming audio. 
        Each sentence will be converted to audio separately. 
        This allows for real-time playback as the audio is being generated. 
        Pretty cool, right?"""

        audio_queue, generator_func = streaming_tts(long_text)
        play_streaming_audio(audio_queue, generator_func)
    elif choice == "4":
        print("=== True Streaming TTS (Live API) ===")
        # text_to_stream = input("Enter text for true streaming TTS: ")
        text_to_stream = """Speak in a cheerful and positive tone.
        Hello there! This is a longer piece of text that demonstrates streaming audio. 
        Each sentence will be converted to audio separately. 
        This allows for real-time playback as the audio is being generated. 
        Pretty cool, right?
        """

        import asyncio

        try:
            asyncio.run(true_streaming_tts(text_to_stream))
        except Exception as e:
            print(f"Live API not available: {e}")
            print("Falling back to manual streaming...")
            audio_queue, generator_func = streaming_tts(text_to_stream)
            play_streaming_audio(audio_queue, generator_func)
    else:
        print("Invalid choice!")

stream.stop_stream()
stream.close()
p.terminate()
