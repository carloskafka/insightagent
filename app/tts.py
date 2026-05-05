from gtts import gTTS
import io
from typing import Optional

def text_to_speech(text: str, lang: str = "en") -> bytes:
    """Convert text to speech using gTTS"""
    tts = gTTS(text=text, lang=lang)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.read()

def save_tts_to_file(text: str, filepath: str, lang: str = "en") -> str:
    """Save TTS audio to a file"""
    tts = gTTS(text=text, lang=lang)
    tts.save(filepath)
    return filepath
