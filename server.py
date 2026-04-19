import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from g2p_id.scripts.tts import tts
import uvicorn
from fastapi.responses import FileResponse
from uuid import uuid4

app = FastAPI(title="TTS Indonesia Gratis API")

# Ensure output directory exists
output_dir = "outputs"
os.makedirs(output_dir, exist_ok=True)

class TTSRequest(BaseModel):
    text: str
    speaker: str = "ardi"

@app.post("/generate")
async def generate_tts(request: TTSRequest):
    """
    Generates TTS audio and returns the WAV file.
    The model is kept in memory for instant subsequent requests.
    """
    filename = f"api_{request.speaker}_{str(uuid4())[:8]}.wav"
    output_path = os.path.join(output_dir, filename)
    
    # Using the optimized in-process tts function
    result = tts(request.text, speaker=request.speaker, output_file=output_path)
    
    if result != 0:
        raise HTTPException(status_code=500, detail="TTS Generation failed")
    
    return FileResponse(output_path, media_type="audio/wav", filename=filename)

@app.get("/health")
async def health_check():
    return {"status": "ready"}

if __name__ == "__main__":
    print("Starting TTS Server... (Loading models might take a few seconds)")
    uvicorn.run(app, host="127.0.0.1", port=8000)
