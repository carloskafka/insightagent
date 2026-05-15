from typing import Optional
import io
import os
import tempfile

_whisper_model = None

def _get_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        _whisper_model = whisper.load_model("tiny")
    return _whisper_model

def speech_to_text(audio_data: bytes, language: str = "en-US") -> Optional[str]:
    try:
        from pydub import AudioSegment
        segment = AudioSegment.from_file(io.BytesIO(audio_data))
        segment = segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            segment.export(f.name, format="wav")
            tmp = f.name

        try:
            model = _get_model()
            lang_code = language.split("-")[0]  # "en-US" -> "en"
            result = model.transcribe(tmp, language=lang_code, fp16=False)
            text = result.get("text", "").strip()
            return text if text else None
        finally:
            os.unlink(tmp)

    except Exception as e:
        print(f"Whisper transcription error: {e}")
        return None

def speech_to_text_from_file(filepath: str, language: str = "en-US") -> Optional[str]:
    try:
        model = _get_model()
        result = model.transcribe(filepath, language=language.split("-")[0], fp16=False)
        text = result.get("text", "").strip()
        return text if text else None
    except Exception as e:
        print(f"Whisper error: {e}")
        return None
