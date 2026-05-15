import io

from gtts import gTTS


def text_to_speech(text: str, lang: str = "en") -> bytes:
    tts = gTTS(text=text, lang=lang)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.read()


def save_tts_to_file(text: str, filepath: str, lang: str = "en") -> str:
    tts = gTTS(text=text, lang=lang)
    tts.save(filepath)
    return filepath
