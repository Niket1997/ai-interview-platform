import speech_recognition as sr
import time


def advanced_speech_to_text(silence_duration=2.0):
    """
    Advanced speech-to-text with custom 2-second silence detection.
    More precise than the built-in silence detection.
    """
    recognizer = sr.Recognizer()

    # Fine-tune for better silence detection
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = silence_duration  # Key setting for silence detection!

    with sr.Microphone() as source:
        print("🎤 Advanced Speech-to-Text")
        print(f"🤫 Will stop after {silence_duration} seconds of silence")
        print("🔧 Calibrating microphone...")

        # Longer calibration for better accuracy
        recognizer.adjust_for_ambient_noise(source, duration=2)

        print("🔊 Ready! Start speaking...")

        try:
            # This will automatically stop after silence_duration seconds of silence
            audio = recognizer.listen(
                source,
                timeout=10,  # Wait 10s for speech to start
                phrase_time_limit=None,  # No hard limit, let silence detection handle it
            )

            print("✅ Speech captured! Processing...")

            # Recognize speech
            text = recognizer.recognize_google(audio)
            return text

        except sr.WaitTimeoutError:
            print("⏰ No speech detected within 10 seconds")
            return None

        except sr.UnknownValueError:
            print("❌ Could not understand the audio")
            return None

        except sr.RequestError as e:
            print(f"❌ Recognition error: {e}")
            return None


def simple_speech_to_text():
    """
    Simple speech-to-text with 2-second silence detection.
    Automatically stops recording after 2 seconds of silence.
    """
    # Initialize the recognizer
    recognizer = sr.Recognizer()

    # Configure for better silence detection
    recognizer.energy_threshold = 300  # Adjust based on your microphone
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = 1.5

    # Use the microphone as audio source
    with sr.Microphone() as source:
        print("🎤 Speech-to-Text with Smart Silence Detection")
        print("🔧 Adjusting for ambient noise... (please wait)")

        # Adjust for ambient noise (important for accuracy)
        recognizer.adjust_for_ambient_noise(source, duration=2)

        print("🔊 Listening... Start speaking!")
        print("🤫 Will stop automatically after 2 seconds of silence")

        try:
            # Listen for audio with 2-second silence timeout
            audio = recognizer.listen(
                source,
                timeout=10,  # Wait max 10 seconds for speech to start
                phrase_time_limit=30,  # Max 30 seconds total (but will stop on 2s silence)
                snowboy_configuration=None,
            )

            print("🔄 Processing speech...")

            # Recognize speech using Google's free service
            text = recognizer.recognize_google(audio)

            return text

        except sr.WaitTimeoutError:
            print("⏰ Timeout - no speech detected within 10 seconds")
            return None

        except sr.UnknownValueError:
            print("❌ Could not understand the audio")
            return None

        except sr.RequestError as e:
            print(f"❌ Error with speech recognition service: {e}")
            return None


def offline_speech_to_text():
    """
    Offline speech-to-text using Whisper backend (requires whisper installation).
    100% offline, no internet needed!
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎤 Offline Speech-to-Text (Whisper)")
        print("🔧 Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)

        print("🔊 Listening... Start speaking!")

        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)

            print("🔄 Processing with Whisper (offline)...")

            # Use Whisper for offline recognition
            text = recognizer.recognize_whisper(audio, model="base")

            return text

        except sr.WaitTimeoutError:
            print("⏰ Timeout - no speech detected")
            return None

        except sr.UnknownValueError:
            print("❌ Could not understand the audio")
            return None

        except Exception as e:
            print(f"❌ Error: {e}")
            print("💡 Try installing: pip install openai-whisper")
            return None


def continuous_speech_to_text():
    """
    Continuous speech-to-text - keeps listening until you stop it.
    """
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    print("🎤 Continuous Speech-to-Text")
    print("🔧 Calibrating microphone...")

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)

    print("🔊 Listening continuously... (Press Ctrl+C to stop)")
    print("=" * 50)

    try:
        while True:
            with microphone as source:
                try:
                    # Listen with shorter timeout for continuous mode
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=5)

                    print("🔄 Processing...")
                    text = recognizer.recognize_google(audio)

                    print(f"📝 You said: '{text}'")
                    print("-" * 30)

                except sr.WaitTimeoutError:
                    # Just continue listening, no need to print timeout
                    pass

                except sr.UnknownValueError:
                    print("❓ Could not understand that")

                except sr.RequestError:
                    print("❌ Network error - check internet connection")
                    time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Stopped listening")


if __name__ == "__main__":
    print("🎤 Speech Recognition Options")
    print("1️⃣  Advanced (2-second silence detection)")
    print("2️⃣  Simple (Google - requires internet)")
    print("3️⃣  Offline (Whisper - no internet needed)")
    print("4️⃣  Continuous (keeps listening)")

    choice = input("\nChoose an option (1-4): ").strip()

    if choice == "1":
        result = advanced_speech_to_text(silence_duration=2.0)
    elif choice == "2":
        result = simple_speech_to_text()
    elif choice == "3":
        result = offline_speech_to_text()
    elif choice == "4":
        continuous_speech_to_text()
        result = None
    else:
        print("❌ Invalid choice")
        result = None

    if result:
        print(f"\n✅ Final Result: '{result}'")
