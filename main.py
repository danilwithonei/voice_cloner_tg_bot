from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import shutil
import os
import uuid
from services.transcriber import Transcriber
from services.cloner import VoiceCloner

app = FastAPI()

# Temporary directory for audio processing
TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.post("/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """Transcribes reference audio into text using Whisper."""
    temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_{audio_file.filename}")
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        text = Transcriber.transcribe(temp_path)
        return {"text": text}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/clone")
async def clone_voice(
    background_tasks: BackgroundTasks,
    ref_audio: UploadFile = File(...),
    target_text: str = Form(...),
    ref_text: str = Form(None)
):
    """Clones a voice from reference audio. Transcribes ref_audio if ref_text is not provided."""
    ref_path = os.path.join(TEMP_DIR, f"ref_{uuid.uuid4()}_{ref_audio.filename}")
    out_path = os.path.join(TEMP_DIR, f"out_{uuid.uuid4()}.wav")

    try:
        # Save reference audio
        with open(ref_path, "wb") as buffer:
            shutil.copyfileobj(ref_audio.file, buffer)

        # Transcribe if ref_text is missing
        if not ref_text:
            ref_text = Transcriber.transcribe(ref_path)

        # Generate cloned voice
        VoiceCloner.generate(
            text=target_text,
            ref_audio_path=ref_path,
            ref_text=ref_text,
            output_path=out_path
        )

        background_tasks.add_task(remove_file, out_path)
        return FileResponse(out_path, media_type="audio/wav", filename="cloned_voice.wav")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Cleanup of ref_path (out_path will be sent as response)
    finally:
        if os.path.exists(ref_path):
            os.remove(ref_path)

@app.on_event("startup")
def preload_models():
    """Preloads the models to avoid delay on first request."""
    Transcriber.get_model()
    VoiceCloner.get_model()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
