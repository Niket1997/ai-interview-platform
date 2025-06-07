import speech_recognition as sr

silence_duration = 2.0


# speech_to_text: generate text from microphone input using google speech to text
def speech_to_text():
    """
    Finely-tuned speech-to-text that stops precisely when you stop speaking.
    Handles natural speech patterns with pauses, breaths, and thinking time.
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        # Calibrate for ambient noise - crucial for accurate detection
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        # Get baseline energy after calibration
        print("📊 Analyzing your speaking pattern...")

        # Fine-tuned parameters for natural speech detection
        recognizer.energy_threshold = max(
            300, recognizer.energy_threshold * 1.2
        )  # Slightly above ambient
        recognizer.dynamic_energy_threshold = True  # Adapt as you speak
        recognizer.dynamic_energy_adjustment_damping = 0.15  # Smooth adjustment
        recognizer.dynamic_energy_ratio = 1.3  # Sensitivity to energy changes

        # The magic setting - tune this for your speech pattern
        recognizer.pause_threshold = (
            silence_duration  # Wait this long after energy drops
        )

        # Additional fine-tuning
        recognizer.operation_timeout = None  # No operation timeout
        recognizer.phrase_timeout = None  # No phrase timeout
        recognizer.non_speaking_duration = (
            0.5  # Min silence before considering speech start/end
        )

        print("🔊 Ready! Start speaking naturally...")

        try:
            # Listen with smart detection
            audio = recognizer.listen(
                source,
                timeout=15,  # Wait up to 15s for you to start
                phrase_time_limit=None,  # No time limit - only silence detection
            )

            print("✅ Captured your complete thought! Processing...")

            # Recognize speech
            text = recognizer.recognize_google(audio)
            return text

        except sr.WaitTimeoutError:
            print("⏰ No speech detected - try speaking closer to microphone")
            return None

        except sr.UnknownValueError:
            print("❌ Audio captured but couldn't understand - try speaking clearer")
            return None

        except sr.RequestError as e:
            print(f"❌ Recognition service error: {e}")
            print("💡 Check your internet connection")
            return None


if __name__ == "__main__":
    # Run speech recognition
    result = speech_to_text()

    if result:
        print(f"\n🎯 You said: '{result}'")
    else:
        print("\n❌ No speech captured")
