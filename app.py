# -*- coding: utf-8 -*-
"""
صوتي 🎙️ — تطبيق استنساخ الصوت للمبتدئين
تشغيل:  uvicorn app:app --reload
"""

import os
import time
import base64
from pathlib import Path
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="صوتي - استنساخ الصوت")

BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / "samples"   # هنا تُحفظ عينات الصوت
OUTPUTS_DIR = BASE_DIR / "outputs"   # هنا تُحفظ النتائج
SAMPLES_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# اسم الملف => مسار العينة المحفوظة
voices_db: dict[str, str] = {}


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


# ---------- ملفات مضمّنة (كلش داخل app.py) ----------
INDEX_HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="manifest" href="/manifest.json">
<link rel="icon" href="/icon-192.png">
<meta name="theme-color" content="#1e1e2f">
<meta name="mobile-web-app-capable" content="yes">
<title>🎙️ صوتي — استنساخ الصوت</title>
<style>
  * { box-sizing: border-box; font-family: 'Segoe UI', Tahoma, sans-serif; }
  body { background: linear-gradient(135deg,#1e1e2f,#2d2d44); min-height:100vh; margin:0; color:#eee; display:flex; justify-content:center; padding:20px; }
  .container { max-width: 640px; width:100%; }
  h1 { text-align:center; font-size:1.8rem; }
  .card { background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); border-radius:16px; padding:20px; margin-bottom:20px; }
  h2 { margin-top:0; font-size:1.2rem; color:#8be9fd; }
  input, textarea { width:100%; padding:10px; border-radius:10px; border:1px solid #555; background:#2a2a3d; color:#fff; margin-bottom:12px; font-size:1rem; }
  textarea { min-height:90px; resize:vertical; }
  button { padding:10px 18px; border:none; border-radius:10px; font-size:1rem; cursor:pointer; font-weight:bold; }
  .btn-main { background:#8be9fd; color:#1e1e2f; width:100%; }
  .btn-record { background:#ff5555; color:#fff; width:100%; }
  .btn-record.recording { background:#50fa7b; }
  .msg { margin-top:12px; padding:10px; border-radius:10px; text-align:center; display:none; }
  .msg.ok { background:rgba(80,250,123,0.15); color:#50fa7b; display:block; }
  .msg.err { background:rgba(255,85,85,0.15); color:#ff6b6b; display:block; }
  audio { width:100%; margin-top:12px; }
  .hint { font-size:0.85rem; color:#aaa; margin-top:6px; }
</style>
</head>
<body>
<div class="container">
  <div style="display:flex;justify-content:space-between;align-items:center;">
  <h1 style="margin:0;">🎙️ صوتي</h1>
  <button id="installBtn" style="display:none;background:#50fa7b;color:#1e1e2f;padding:8px 14px;font-size:0.9rem;">📲 ثبّت التطبيق</button>
</div>

  <div class="card">
    <h2>⚙️ الإعدادات</h2>
    <input id="apiKey" type="password" placeholder="مفتاح ElevenLabs (مجاني من elevenlabs.io)">
    <div class="hint">سُجّل حسابًا مجانيًا في <b>elevenlabs.io</b> ← Profile ← API Key، ثم الصق المفتاح هنا.</div>
  </div>

  <div class="card">
    <h2>الخطوة 1: سجّل عينة صوتك</h2>
    <input id="voiceName" type="text" placeholder="اسم الصوت (مثال: صوتي)">
    <button id="recordBtn" class="btn-record">🔴 ابدأ التسجيل</button>
    <div class="hint">سجّل 30 ثانية إلى دقيقة بصوت واضح وهادئ، بعيدًا عن الضوضاء.</div>
    <button id="saveBtn" class="btn-main" style="margin-top:12px" disabled>💾 حفظ العينة</button>
    <div id="recMsg" class="msg"></div>
  </div>

  <div class="card">
    <h2>الخطوة 2: اكتب رسالتك</h2>
    <select id="voiceSelect" style="width:100%;padding:10px;border-radius:10px;margin-bottom:12px;background:#2a2a3d;color:#fff;border:1px solid #555;"></select>
    <textarea id="textInput" placeholder="اكتب النص الذي تريد سماعه بصوتك..."></textarea>
    <button id="speakBtn" class="btn-main">▶️ اقرأ بنبرة صوتي</button>
    <div id="speakMsg" class="msg"></div>
    <audio id="player" controls style="display:none"></audio>
  </div>
</div>

<script>
const recordBtn = document.getElementById('recordBtn');
const saveBtn = document.getElementById('saveBtn');
const speakBtn = document.getElementById('speakBtn');
const voiceSelect = document.getElementById('voiceSelect');

// حفظ المفتاح محليًا
const apiKeyInput = document.getElementById('apiKey');
apiKeyInput.value = localStorage.getItem('eleven_key') || '';
apiKeyInput.addEventListener('input', () => localStorage.setItem('eleven_key', apiKeyInput.value));

let mediaRecorder, chunks = [], recordedBlob = null, recording = false;

// ---------- التسجيل ----------
recordBtn.addEventListener('click', async () => {
  if (!recording) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      chunks = [];
      mediaRecorder.ondataavailable = e => chunks.push(e.data);
      mediaRecorder.onstop = () => {
        recordedBlob = new Blob(chunks, { type: mediaRecorder.mimeType });
        saveBtn.disabled = false;
        showMsg('recMsg', 'تم التسجيل! اضغط «حفظ العينة» ✅', true);
      };
      mediaRecorder.start();
      recording = true;
      recordBtn.textContent = '⏹️ إيقاف التسجيل';
      recordBtn.classList.add('recording');
      showMsg('recMsg', 'جارٍ التسجيل... تحدث الآن 🎤', true);
    } catch (e) {
      showMsg('recMsg', 'تعذّر الوصول للميكروفون: ' + e.message, false);
    }
  } else {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
    recording = false;
    recordBtn.textContent = '🔴 ابدأ التسجيل';
    recordBtn.classList.remove('recording');
  }
});

// ---------- حفظ العينة ----------
saveBtn.addEventListener('click', async () => {
  const name = document.getElementById('voiceName').value.trim();
  if (!name) { showMsg('recMsg', 'اكتب اسمًا للصوت أولاً', false); return; }
  if (!recordedBlob) { showMsg('recMsg', 'سجّل عينة أولاً', false); return; }

  const fd = new FormData();
  fd.append('name', name);
  fd.append('audio', recordedBlob, 'sample.webm');

  showMsg('recMsg', 'جارٍ الحفظ... ⏳', true);
  const res = await fetch('/save-sample', { method: 'POST', body: fd });
  const data = await res.json();
  if (res.ok) {
    showMsg('recMsg', data.message, true);
    await loadVoices();
  } else {
    showMsg('recMsg', 'خطأ: ' + (data.error || 'غير معروف'), false);
  }
});

// ---------- تحميل قائمة الأصوات ----------
async function loadVoices() {
  const res = await fetch('/voices');
  const data = await res.json();
  voiceSelect.innerHTML = '';
  data.voices.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v; opt.textContent = v;
    voiceSelect.appendChild(opt);
  });
}
loadVoices();

// ---------- توليد الكلام ----------
speakBtn.addEventListener('click', async () => {
  const name = voiceSelect.value;
  const text = document.getElementById('textInput').value.trim();
  if (!name) { showMsg('speakMsg', 'احفظ عينة صوت أولاً', false); return; }
  if (!text) { showMsg('speakMsg', 'اكتب النص أولاً', false); return; }

  const fd = new FormData();
  fd.append('name', name);
  fd.append('text', text);
  fd.append('eleven_key', apiKeyInput.value);

  showMsg('speakMsg', 'جارٍ توليد الصوت... قد يستغرق ثوانٍ ⏳', true);
  speakBtn.disabled = true;
  const res = await fetch('/speak', { method: 'POST', body: fd });
  speakBtn.disabled = false;

  if (res.ok) {
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const player = document.getElementById('player');
    player.src = url;
    player.style.display = 'block';
    player.play();
    showMsg('speakMsg', 'تم! استمع للنتيجة 🎧', true);
  } else {
    const data = await res.json();
    showMsg('speakMsg', 'خطأ: ' + (data.error || 'غير معروف'), false);
  }
});

// تسجيل Service Worker (للتثبيت على أندرويد)
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(()=>{});
}

// زر تثبيت التطبيق على الشاشة الرئيسية
let installPrompt = null;
window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  installPrompt = e;
  document.getElementById('installBtn').style.display = 'inline-block';
});
document.getElementById('installBtn').addEventListener('click', async () => {
  if (installPrompt) { installPrompt.prompt(); installPrompt = null; }
});

function showMsg(id, text, ok) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = 'msg ' + (ok ? 'ok' : 'err');
}
</script>
</body>
</html>
"""

MANIFEST_JSON = r"""{
  "name": "صوتي — استنساخ الصوت",
  "short_name": "صوتي",
  "start_url": "/",
  "display": "standalone",
  "dir": "rtl",
  "lang": "ar",
  "background_color": "#1e1e2f",
  "theme_color": "#1e1e2f",
  "icons": [
    {
      "src": "/static/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}"""

SW_JS = r"""// Service Worker لجعل التطبيق يعمل كتطبيق مثبّت
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(clients.claim()));
self.addEventListener('fetch', e => {
  // لا نخزّن شيئًا — كل الطلبات تمر مباشرة للخادم
  e.respondWith(fetch(e.request));
});
"""

ICON_192 = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAIAAADdvvtQAAAEj0lEQVR4nO3dWU7cQBRG4SLKOnoLSEgsi9WwLCTWlAdHVtM2U/93qrrne0wicKpOX7sHzMPl8jiAe/3JPgDMjYAgISBICAgSAoKEgCAhIEgICBICgoSAICEgSAgIEgKChIAgISBICAgSAoKEgCAhIEgICBICgoSAICEgSP5mH8CnXt7esw+hltfnp+xDOPFQ6gcLieaH6sRUIiC6uVt6SckBkY6JxIzSAiIdcykZ5TwLox4PKasaPYFIJ0DkKAqdQNQTI3Kd4wKinkhhqx0UEPXEi1nziICoJ0vAyrsHRD25vNffNyDqqcB1FxwDop46/PaCj3NA4hUQ46capx1xCYh6avLYF05hkNgHxPipzHx3mECQGAfE+KnPdo+YQJAQECSWAXH+moXhTjGBICEgSAgIErOAuACai9V+MYEgISBICAgSAoKEgCAhIEgICBICgoSAIKl7k81cp3dI4dX2IwL64Os76+x/S0k7AvrvVzdl2v4xGQ2ugTb33dIr/Q6pFXSfQGIEjKLWE8hqhHQeRa0Dgq5vQLZjo+0QahqQx373bKhpQLDSMSC/UdFwCHUMCIYICJJ2AXmfZbqdxdoFBFsEBAkBQUJAkBAQJAQECQFBQkCQEBAkBAQJAUFCQJAQECQEBAkBQUJAkBAQJAQECQFBQkCQEBAkBAQJAUFCQJAQECQEBAkBQUJAkBAQJAQECQFBQkCQtAvI+67y3e5a3y4g2CIgSDoG5HeW6Xb+Gj0DgqGmAXmMiobjZ7QNaFjvd896RueAYKJ1QFZjo+34GfzKy23v7769fOd0Nq0n0O6+DqhnMIF2vxpFpLMjoA/2Mk5LopsjTmHnXt7eb3KhnlMEBMn0p7Drc81EQ2LSwz5iAkFCQJAQECQEBAkBQTJ9QNdPYWb5jcnLPAUbCwSEXAQECQFBskJAc10GrXQBNNYICIkWDKjyEKp8bPdZJKAZzwUzHvPRIgEhyzoB1b+UXuzyebNOQDeqNVTteKwsFdAsD+tZjvMnpv9E4hden5/ErbLa6VXHz1hsAo3DllfYuZtjWGn8DMOAKmzVplRDZeuxWpbVJhCCrRlQkSFUdvwYWjOgcdZQZEbHb7dkPcM2oDqXQZvjnsUc4fG7VKvHcB2WnUCb+Ibq12Nr8YDGJw15ZHT6ZdeuZ4zxcLk82n7Fskvmd8ONuW7lYfvgWfmV6Bsvb+/Htdv/5I79/mInytZjzn4CjdrL9+3j79uD179CIvNzd6MJtPn2TmTKEldOx4nLBBqTLKXhw7Hb/3fnFdCYZE03He7S6vT6RbtT2KlffZpxomgCOE6gwVqX4ffyqe8LidXe3OjJdRfcX4mmoVze6x/xVgYNZQlY+aD3wmgoXsyax72ZSkORwlY79N14GooRuc6+T+M/w9N7J/EP0ZzPAzGKPKSsas4E2jGKTCQ+IJMD2pDR3dJneYmAdpT0Q+nd7GoFdI2YbtSJ5lrdgDCF9X8qA64ICBICgoSAICEgSAgIEgKChIAgISBICAgSAoKEgCAhIEgICBICgoSAICEgSAgIEgKChIAgISBICAiSf/MdSPBuOAbnAAAAAElFTkSuQmCC")
ICON_512 = base64.b64decode("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")


@app.get("/", response_class=HTMLResponse)
def home():
    return INDEX_HTML


@app.get("/sw.js")
def sw():
    return Response(SW_JS, media_type="application/javascript")


@app.get("/manifest.json")
def manifest():
    return Response(MANIFEST_JSON, media_type="application/json")


@app.get("/icon-192.png")
def icon192():
    return Response(ICON_192, media_type="image/png")


@app.get("/icon-512.png")
def icon512():
    return Response(ICON_512, media_type="image/png")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
