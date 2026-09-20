# -*- coding: utf-8 -*-
# صوتي 🎙️ — تطبيق استنساخ الصوت (ملف واحد كامل)
import os, time, base64
from pathlib import Path
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, Response

app = FastAPI(title="صوتي - استنساخ الصوت")

BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / "samples"
OUTPUTS_DIR = BASE_DIR / "outputs"
SAMPLES_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

voices_db: dict = {}

INDEX_HTML = r"""PLACEHOLDER_HTML"""

MANIFEST = r"""PLACEHOLDER_MANIFEST"""

SW_JS = r"""PLACEHOLDER_SW"""

ICON_192 = base64.b64decode("PLACEHOLDER_192")
ICON_512 = base64.b64decode("PLACEHOLDER_512")


@app.get("/", response_class=HTMLResponse)
def home():
    return INDEX_HTML


@app.get("/manifest.json")
def manifest():
    return Response(MANIFEST, media_type="application/json")


@app.get("/sw.js")
def sw():
    return Response(SW_JS, media_type="application/javascript")


@app.get("/icon-192.png")
def i192():
    return Response(ICON_192, media_type="image/png")


@app.get("/icon-512.png")
def i512():
    return Response(ICON_512, media_type="image/png")


@app.post("/save-sample")
async def save_sample(name: str = Form(...), audio: UploadFile = Form(...)):
    safe = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
    if not safe:
        return JSONResponse(status_code=400, content={"error": "الاسم غير صالح"})
    path = SAMPLES_DIR / f"{safe}.webm"
    path.write_bytes(await audio.read())
    voices_db[safe] = str(path)
    return {"ok": True, "message": f"تم حفظ العينة «{safe}» ✅"}


@app.get("/voices")
def list_voices():
    return {"voices": list(voices_db.keys())}


@app.post("/speak")
async def speak(name: str = Form(...), text: str = Form(...), eleven_key: str = Form("")):
    if name not in voices_db:
        return JSONResponse(status_code=404, content={"error": "احفظ عينة أولاً"})
    api_key = eleven_key.strip() or os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key:
        return JSONResponse(status_code=400, content={"error": "أدخل مفتاح ElevenLabs في الإعدادات"})
    try:
        from elevenlabs import ElevenLabs
        client = ElevenLabs(api_key=api_key)
        voice = client.voices.ivc.create(name=f"{name}_{int(time.time())}", files=[voices_db[name]])
        audio = client.text_to_speech.convert(voice_id=voice.voice_id, text=text, model_id="eleven_multilingual_v2")
        out = OUTPUTS_DIR / f"{name}_{int(time.time())}.mp3"
        out.write_bytes(b"".join(audio))
        return FileResponse(out, media_type="audio/mpeg", filename=out.name)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"حدث خطأ: {e}"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
