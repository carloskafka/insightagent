from typing import Optional

import speech_recognition as sr


def speech_to_text(audio_data: bytes, language: str = "en-US") -> Optional[str]:
    recognizer = sr.Recognizer()

    try:
        audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
        return recognizer.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        return None
    except sr.RequestError as exc:
        print(f"Speech recognition error: {exc}")
        return None


def speech_to_text_from_file(filepath: str, language: str = "en-US") -> Optional[str]:
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(filepath) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        return None
    except sr.RequestError as exc:
        print(f"Speech recognition error: {exc}")
        return None
