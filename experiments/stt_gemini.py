import asyncio
from google.genai import types
from google import genai
from dotenv import load_dotenv
import os
import pyaudio
import wave
import threading

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Audio configuration for microphone input
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # 16kHz for speech input
CHUNK = 1024


async def speech_to_text_demo():
    """
    Demonstrates Gemini Live API speech-to-text capabilities.
    Shows both transcription and understanding of spoken input.
    """

    model = "gemini-2.0-flash-live-001"
    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],
        input_audio_transcription={},  # Enable transcription of input
        realtime_input_config={
            "automatic_activity_detection": {
                "disabled": False,
                "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_HIGH,
                "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_HIGH,
            }
        },
    )

    print("🎤 Speech-to-Text Demo with Gemini Live API")
    print("📝 This will transcribe your speech AND respond to it")
    print("🔴 Recording audio... (speak now)")

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            # Simulate sending audio (you'd capture real audio here)
            # For demo, we'll send a pre-recorded file if available

            audio_file_path = "sample_audio.wav"  # You can record this

            try:
                # Try to load a sample audio file and convert to PCM
                pcm_data = convert_wav_to_pcm(audio_file_path)

                await session.send_realtime_input(
                    audio=types.Blob(data=pcm_data, mime_type="audio/pcm;rate=16000")
                )

                print("🎵 Audio sent! Processing...")

            except FileNotFoundError:
                # If no audio file, send a text message instead
                print("📝 No audio file found, sending text instead...")
                await session.send_client_content(
                    turns={
                        "role": "user",
                        "parts": [{"text": "Hello, can you hear me?"}],
                    },
                    turn_complete=True,
                )

            # Listen for responses
            async for response in session.receive():
                # Input transcription (what you said)
                if (
                    response.server_content
                    and response.server_content.input_transcription
                ):
                    print(
                        f"🎤 You said: '{response.server_content.input_transcription.text}'"
                    )

                # Gemini's text response
                if response.text is not None:
                    print(f"🤖 Gemini responds: {response.text}")

                # Check if done
                if (
                    response.server_content
                    and response.server_content.generation_complete
                ):
                    break

    except Exception as e:
        print(f"❌ Error: {e}")


def convert_wav_to_pcm(wav_file_path):
    """
    Converts WAV file to raw PCM data for Gemini Live API.
    """
    with wave.open(wav_file_path, "rb") as wav_file:
        frames = wav_file.readframes(wav_file.getnframes())
        return frames


def record_audio(duration=5, filename="recorded_audio.wav"):
    """
    Records audio from microphone and saves to file.
    """
    print(f"🎤 Recording for {duration} seconds...")

    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )

    frames = []

    for i in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save to file
    wf = wave.open(filename, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()

    print(f"✅ Audio saved to {filename}")
    return filename


async def live_microphone_to_text():
    """
    Real-time microphone input to text conversion using Gemini Live API.
    """
    print("🎤 Live Microphone to Text Demo")
    print("🔴 Starting real-time transcription...")

    model = "gemini-2.0-flash-live-001"
    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],
        input_audio_transcription={},
        realtime_input_config={
            "automatic_activity_detection": {
                "disabled": False,
                "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_HIGH,
                "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_HIGH,
            }
        },
    )

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            # Record a short audio clip
            print("📢 Speak now (5 seconds)...")
            audio_file = record_audio(duration=5, filename="live_recording.wav")

            # Convert WAV to PCM and send
            pcm_data = convert_wav_to_pcm(audio_file)

            await session.send_realtime_input(
                audio=types.Blob(data=pcm_data, mime_type="audio/pcm;rate=16000")
            )

            print("🔄 Processing your speech...")

            # Get transcription and response
            async for response in session.receive():
                if (
                    response.server_content
                    and response.server_content.input_transcription
                ):
                    print(
                        f"📝 Transcription: '{response.server_content.input_transcription.text}'"
                    )

                if response.text is not None:
                    print(f"🤖 AI Response: {response.text}")

                if (
                    response.server_content
                    and response.server_content.generation_complete
                ):
                    break

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure your microphone is working and try again")


async def continuous_speech_recognition():
    """
    Continuous speech recognition - keeps listening and transcribing.
    """
    print("🎙️  Continuous Speech Recognition")
    print("🔴 This will continuously listen and transcribe your speech")
    print("⚠️  Press Ctrl+C to stop")

    model = "gemini-2.0-flash-live-001"
    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],
        input_audio_transcription={},
    )

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            chunk_count = 0

            while True:
                try:
                    # Record short chunks continuously
                    chunk_filename = f"audio_chunk_{chunk_count}.wav"
                    print(f"🎤 Listening... (chunk {chunk_count})")

                    record_audio(duration=3, filename=chunk_filename)

                    # Convert to PCM and send audio chunk
                    pcm_data = convert_wav_to_pcm(chunk_filename)

                    await session.send_realtime_input(
                        audio=types.Blob(
                            data=pcm_data, mime_type="audio/pcm;rate=16000"
                        )
                    )

                    # Get transcription
                    async for response in session.receive():
                        if (
                            response.server_content
                            and response.server_content.input_transcription
                        ):
                            transcription = (
                                response.server_content.input_transcription.text
                            )
                            if (
                                transcription.strip()
                            ):  # Only print non-empty transcriptions
                                print(f"📝 [{chunk_count}] You said: '{transcription}'")

                        # Break after getting transcription for this chunk
                        if (
                            response.server_content
                            and response.server_content.input_transcription
                        ):
                            break

                    chunk_count += 1

                except KeyboardInterrupt:
                    print("\n🛑 Stopping continuous recognition...")
                    break

    except Exception as e:
        print(f"❌ Error: {e}")


async def transcribe_audio_file():
    """
    Transcribe a specific audio file using Gemini Live API.
    """
    audio_file = input("Enter audio file path (or press Enter for default): ").strip()

    if not audio_file:
        audio_file = "sample_audio.wav"

    print(f"📁 Transcribing file: {audio_file}")

    model = "gemini-2.0-flash-live-001"
    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],
        input_audio_transcription={},
    )

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            try:
                # Convert audio file to PCM format
                pcm_data = convert_wav_to_pcm(audio_file)

                await session.send_realtime_input(
                    audio=types.Blob(data=pcm_data, mime_type="audio/pcm;rate=16000")
                )

                print("🔄 Transcribing...")

                async for response in session.receive():
                    if (
                        response.server_content
                        and response.server_content.input_transcription
                    ):
                        print(
                            f"📝 Transcription: '{response.server_content.input_transcription.text}'"
                        )

                    if response.text is not None:
                        print(f"💬 Summary/Response: {response.text}")

                    if (
                        response.server_content
                        and response.server_content.generation_complete
                    ):
                        break

            except FileNotFoundError:
                print(f"❌ Audio file '{audio_file}' not found!")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🎤 Gemini Live API - Speech-to-Text Demo")
    print("=" * 50)
    print("Choose an option:")
    print("1. Speech-to-Text Demo (with sample file)")
    print("2. Live Microphone Recording")
    print("3. Continuous Speech Recognition")
    print("4. Transcribe Audio File")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        asyncio.run(speech_to_text_demo())
    elif choice == "2":
        asyncio.run(live_microphone_to_text())
    elif choice == "3":
        asyncio.run(continuous_speech_recognition())
    elif choice == "4":
        asyncio.run(transcribe_audio_file())
    else:
        print("❌ Invalid choice!")

    print("\n✅ Speech-to-Text demo completed!")
