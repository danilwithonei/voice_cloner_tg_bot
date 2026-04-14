from omnivoice import OmniVoice
import torch
import torchaudio
import os

class VoiceCloner:
    _model = None
    _device = "cuda:0" if torch.cuda.is_available() else "cpu"

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = OmniVoice.from_pretrained(
                "k2-fsa/OmniVoice",
                device_map=cls._device,
                dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
        return cls._model

    @classmethod
    def generate(cls, text: str, ref_audio_path: str, ref_text: str, output_path: str):
        model = cls.get_model()
        
        # Generate audio
        audio = model.generate(
            text=text,
            ref_audio=ref_audio_path,
            ref_text=ref_text,
        ) # audio is a list of `torch.Tensor` with shape (1, T) at 24 kHz.

        # Save the first item in the list
        torchaudio.save(output_path, audio[0], 24000)
        return output_path
