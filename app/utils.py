import speech_recognition as sr
from typing import Optional
import io

def speech_to_text(audio_data: bytes, language: str = "en-US") -> Optional[str]:
    """Convert speech to text using Whisper via speech_recognition"""
    recognizer = sr.Recognizer()
    
    try:
        audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
        # Using Google's free speech recognition (can be replaced with Whisper API)
        text = recognizer.recognize_google(audio, language=language)
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"Speech recognition error: {e}")
        return None

def speech_to_text_from_file(filepath: str, language: str = "en-US") -> Optional[str]:
    """Convert speech to text from an audio file"""
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(filepath) as source:
            audio = recognizer.record(source)
        
        text = recognizer.recognize_google(audio, language=language)
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"Speech recognition error: {e}")
        return None
