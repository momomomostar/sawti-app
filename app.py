# -*- coding: utf-8 -*-
"""
صوتي 🎙️ — تطبيق استنساخ الصوت للمبتدئين
تشغيل:  uvicorn app:app --reload
"""

import os
import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="صوتي - استنساخ الصوت")

BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / "samples"   # هنا تُحفظ عينات الصوت
OUTPUTS_DIR = BASE_DIR / "outputs"   # هنا تُحفظ النتائج
SAMPLES_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# اسم الملف => مسار العينة المحفوظة
voices_db: dict[str, str] = {}


# ---------- الصفحة الرئيسية ----------
@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


# ---------- حفظ عينة الصوت ----------
@app.post("/save-sample")
async def save_sample(name: str = Form(...), audio: UploadFile = Form(...)):
    safe = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
    if not safe:
        return JSONResponse(status_code=400, content={"error": "الاسم غير صالح"})

    path = SAMPLES_DIR / f"{safe}.webm"
    path.write_bytes(await audio.read())
    voices_db[safe] = str(path)

    return {"ok": True, "message": f"تم حفظ عينة الصوت باسم «{safe}» ✅"}


# ---------- قائمة الأصوات المحفوظة ----------
@app.get("/voices")
def list_voices():
    return {"voices": list(voices_db.keys())}


# ---------- قراءة النص بصوت محفوظ ----------
@app.post("/speak")
async def speak(name: str = Form(...), text: str = Form(...), eleven_key: str = Form("")):
    if name not in voices_db:
        return JSONResponse(status_code=404, content={"error": "هذا الصوت غير موجود، احفظ عينة أولاً"})

    api_key = eleven_key.strip() or os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key:
        return JSONResponse(status_code=400, content={
            "error": "أدخل مفتاح ElevenLabs في الإعدادات (مجاني من elevenlabs.io)"
        })

    sample_path = voices_db[name]

    try:
        from elevenlabs import ElevenLabs
        client = ElevenLabs(api_key=api_key)

        # 1) إنشاء نسخة صوتية من العينة
        voice = client.voices.ivc.create(
            name=f"{name}_{int(time.time())}",
            files=[sample_path],
        )

        # 2) توليد الكلام بنفس الصوت
        audio = client.text_to_speech.convert(
            voice_id=voice.voice_id,
            text=text,
            model_id="eleven_multilingual_v2",  # يدعم العربية
        )

        out_path = OUTPUTS_DIR / f"{name}_{int(time.time())}.mp3"
        out_path.write_bytes(b"".join(audio))
        return FileResponse(out_path, media_type="audio/mpeg", filename=out_path.name)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"حدث خطأ: {e}"})


# ملفات PVA يجب أن تكون في الجذر (scope)
@app.get("/sw.js")
def sw():
    return FileResponse(BASE_DIR / "static" / "sw.js", media_type="application/javascript")


@app.get("/manifest.json")
def manifest():
    return FileResponse(BASE_DIR / "static" / "manifest.json", media_type="application/json")


# تشغيل ملفات ثابتة (الواجهة)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
