import whisper
import os

class Transcriber:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            # Using 'base' model for a balance between speed and accuracy
            cls._model = whisper.load_model("base")
        return cls._model

    @classmethod
    def transcribe(cls, audio_path: str) -> str:
        model = cls.get_model()
        result = model.transcribe(audio_path)
        return result["text"].strip()
