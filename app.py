# -*- coding: utf-8 -*-
# صوتي - استنساخ الصوت (Fish Audio مجاني)
import os,time,json,urllib.request
from pathlib import Path
from fastapi import FastAPI,UploadFile,Form
from fastapi.responses import FileResponse,JSONResponse,HTMLResponse,Response
import zlib,struct
def png(n,rgb):
 row=b"\x00"+bytes(rgb)*n
 raw=row*n
 def ch(t,d):
  c=t+d
  return struct.pack(">I",len(d))+c+struct.pack(">I",zlib.crc32(c))
 return (b"\x89PNG\r\n\x1a\n"+ch(b"IHDR",struct.pack(">IIBBBBB",n,n,8,2,0,0,0))
  +ch(b"IDAT",zlib.compress(raw,9))+ch(b"IEND",b""))
ICON=png(192,(139,233,253))
app=FastAPI(title="صوتي")
BD=Path(__file__).parent
(BD/"samples").mkdir(exist_ok=True)
(BD/"outputs").mkdir(exist_ok=True)
db={}
last={}

INDEX=r"""<!DOCTYPE html>
<html lang="ar" dir="rtl"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🎙️ صوتي</title><link rel="manifest" href="/manifest.json">
<link rel="icon" href="/icon.png"><meta name="theme-color" content="#1e1e2f">
<style>
*{box-sizing:border-box;font-family:Tahoma,sans-serif}
body{background:linear-gradient(135deg,#1e1e2f,#2d2d44);margin:0;padding:16px;color:#eee}
h1{text-align:center;font-size:1.5rem}
.c{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);border-radius:14px;padding:16px;margin-bottom:16px}
h2{margin:0 0 10px;font-size:1.05rem;color:#8be9fd}
input,textarea,select{width:100%;padding:10px;border-radius:10px;border:1px solid #555;background:#2a2a3d;color:#fff;margin-bottom:10px;font-size:1rem}
textarea{min-height:80px}
button{padding:10px;border:none;border-radius:10px;font-size:1rem;font-weight:bold;cursor:pointer;width:100%}
.b1{background:#8be9fd;color:#1e1e2f}.b2{background:#ff5555;color:#fff}.b2r{background:#50fa7b}
.m{margin-top:10px;padding:10px;border-radius:10px;text-align:center;display:none}
.ok{background:rgba(80,250,123,.15);color:#50fa7b;display:block}.er{background:rgba(255,85,85,.15);color:#ff6b6b;display:block}
audio{width:100%;margin-top:10px}
.up{display:block;background:#2a2a3d;border:1px dashed #555;border-radius:10px;padding:12px;text-align:center;cursor:pointer;margin-bottom:10px}
</style></head><body>
<h1>🎙️ صوتي</h1>
<div class="c"><h2>⚙️ الإعدادات</h2>
<input id="k" type="password" placeholder="مفتاح Fish Audio (من fish.audio)">
</div>
<div class="c"><h2>1️⃣ سجّل عينة الصوت</h2>
<input id="n" type="text" placeholder="اسم الصوت (مثال: صوتي)">
<button id="r" class="b2">🔴 ابدأ التسجيل</button>
<div style="text-align:center;color:#aaa;margin:10px 0">— ولا —</div>
<label class="up">📂 اختر ملف صوتي من الهاتف<input id="f" type="file" accept="audio/*" style="display:none"></label>
<button id="s" class="b1" style="margin-top:8px" disabled>💾 حفظ العينة</button>
<div id="m1" class="m"></div></div>
<div class="c"><h2>2️⃣ اكتب رسالتك</h2>
<select id="v"></select>
<input id="h" type="text" placeholder="تلميح النبرة (اختياري) — مثال: بالدارجة المغربية، ببطء">
<textarea id="t" placeholder="اكتب النص هنا..."></textarea>
<button id="g" class="b1">▶️ اقرأ بنبرة صوتي</button>
<div id="m2" class="m"></div>
<a id="dl" class="b1" style="display:none;text-decoration:none;text-align:center;margin-top:8px">⬇️ تحميل الصوت</a>
<audio id="p" controls style="display:none"></audio></div>
<script>
var k=document.getElementById('k'),r=document.getElementById('r'),s=document.getElementById('s'),
g=document.getElementById('g'),v=document.getElementById('v');
k.value=localStorage.getItem('fk')||'';
k.oninput=function(){localStorage.setItem('fk',k.value)};
if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(function(){});
var actx,src,rec,ch=[],bl=null,rc=false,stm;
function wavBlob(){
 var len=0,i,j;for(i=0;i<ch.length;i++)len+=ch[i].length;
 var buf=new ArrayBuffer(44+len*2),d=new DataView(buf);
 function W(o,x){d.setUint8(o,x&255);d.setUint8(o+1,(x>>8)&255);d.setUint8(o+2,(x>>16)&255);d.setUint8(o+3,(x>>24)&255)}
 function S(o,t){for(var i=0;i<t.length;i++)d.setUint8(o+i,t.charCodeAt(i))}
 S(0,'RIFF');W(4,36+len*2);S(8,'WAVE');S(12,'fmt ');W(16,16);W(20,1);W(22,1);W(24,44100);
 W(28,88200);W(32,2);W(34,16);S(36,'data');W(40,len*2);
 var o=44;for(i=0;i<ch.length;i++){var c=ch[i];for(j=0;j<c.length;j++){var x=Math.max(-1,Math.min(1,c[j]));d.setInt16(o,x<0?x*32768:x*32767,true);o+=2}}
 return new Blob([buf],{type:'audio/wav'});
}
r.onclick=async function(){
 if(!rc){try{
  stm=await navigator.mediaDevices.getUserMedia({audio:true});
  actx=new (window.AudioContext||window.webkitAudioContext)({sampleRate:44100});
  src=actx.createMediaStreamSource(stm);rec=actx.createScriptProcessor(4096,1,1);ch=[];
  rec.onaudioprocess=function(e){ch.push(new Float32Array(e.inputBuffer.getChannelData(0)))};
  src.connect(rec);rec.connect(actx.destination);
  rc=true;r.textContent='⏹️ إيقاف';r.classList.add('b2r');msg('m1','جارٍ التسجيل... 🎤',1);
 }catch(e){msg('m1','الميكروفون مرفوض',0)}}
 else{rec.disconnect();src.disconnect();stm.getTracks().forEach(function(t){t.stop()});actx.close();
  bl=wavBlob();rc=false;s.disabled=false;
  r.textContent='🔴 ابدأ التسجيل';r.classList.remove('b2r');msg('m1','تم التسجيل ✅',1)}
};
document.getElementById('f').onchange=function(){
 var file=this.files[0];if(!file)return;
 if(file.size>15*1024*1024){msg('m1','الملف كبير (الحد 15MB)',0);this.value='';return}
 bl=file;s.disabled=false;msg('m1','تم اختيار الملف: '+file.name+' ✅',1);
};
s.onclick=async function(){var n=document.getElementById('n').value.trim();
 if(!n||!bl){msg('m1','اكتب الاسم وسجّل أولاً',0);return}
 var f=new FormData();f.append('name',n);f.append('audio',bl,'a.wav');f.append('api_key',k.value);
 msg('m1','جارٍ الحفظ وإنشاء البصمة... ⏳',1);s.disabled=true;
 var d=await (await fetch('/save-sample',{method:'POST',body:f})).json();
 msg('m1',d.message||d.error,!!d.ok);ld()};
async function ld(){var d=await (await fetch('/voices')).json();v.innerHTML='';
 d.voices.forEach(function(x){var o=document.createElement('option');o.value=o.textContent=x;v.appendChild(o)})}
ld();
g.onclick=async function(){
 var tx=document.getElementById('t').value;
 var hint=document.getElementById('h').value.trim();
 if(hint){tx='['+hint+'] '+tx}
 var f=new FormData();f.append('name',v.value);f.append('text',tx);f.append('api_key',k.value);
 msg('m2','جارٍ التوليد... ⏳',1);g.disabled=true;
 var res=await fetch('/speak',{method:'POST',body:f});g.disabled=false;
 if(res.ok){var u=URL.createObjectURL(await res.blob());var p=document.getElementById('p');
 p.src=u;p.style.display='block';p.play();msg('m2','تم! 🎧',1);
 var a=document.getElementById('dl');a.href='/download/'+encodeURIComponent(v.value);a.style.display='block'}
 else{var d=await res.json();msg('m2','خطأ: '+(d.error||'؟'),0)}};
function msg(id,t,ok){var e=document.getElementById(id);e.textContent=t;e.className='m '+(ok?'ok':'er')}
</script>
<div class="c" style="text-align:center">
<h2>📬 تواصل معنا</h2>
<p style="color:#aaa;font-size:.9rem;margin:0 0 12px">عندك سؤال ولا اقتراح؟ راسلني مباشرة:</p>
<a href="mailto:larache66679@gmail.com" class="b1" style="display:inline-block;width:auto;padding:12px 30px;text-decoration:none;border-radius:12px;font-weight:bold">✉️ larache66679@gmail.com</a>
</div>
</body></html>"""

MANIFEST=r"""{"name":"صوتي","short_name":"صوتي","start_url":"/","display":"standalone","dir":"rtl","lang":"ar","background_color":"#1e1e2f","theme_color":"#1e1e2f","icons":[{"src":"/icon.png","sizes":"192x192","type":"image/png"},{"src":"/icon.png","sizes":"512x512","type":"image/png"}]}"""

SW=r"""self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>e.waitUntil(clients.claim()));self.addEventListener('fetch',e=>e.respondWith(fetch(e.request)));"""

def fish_create_voice(key,wav_path):
 import uuid
 b="----sawti"+uuid.uuid4().hex
 wav=open(wav_path,"rb").read()
 def fld(n,v): return ("--"+b+"\r\nContent-Disposition: form-data; name=\""+n+"\"\r\n\r\n"+v+"\r\n").encode()
 body=fld("type","tts")+fld("title","sawti"+str(int(time.time())))+fld("train_mode","fast")+fld("visibility","private")
 body+=("--"+b+"\r\nContent-Disposition: form-data; name=\"voices\"; filename=\"ref.wav\"\r\nContent-Type: audio/wav\r\n\r\n").encode()
 body+=wav+b"\r\n--"+b.encode()+b"--\r\n"
 req=urllib.request.Request("https://api.fish.audio/model",data=body,headers={
  "Authorization":"Bearer "+key,"Content-Type":"multipart/form-data; boundary="+b})
 resp=json.loads(urllib.request.urlopen(req,timeout=180).read().decode())
 return resp.get("_id") or resp.get("id") or str(resp).strip('"')

def fish_tts(key,vid,text):
 body=json.dumps({"text":text,"reference_id":vid,"format":"mp3"}).encode()
 req=urllib.request.Request("https://api.fish.audio/v1/tts",data=body,headers={
  "Authorization":"Bearer "+key,"Content-Type":"application/json","model":"s2.1-pro-free"})
 return urllib.request.urlopen(req,timeout=180).read()


@app.get("/",response_class=HTMLResponse)
def home(): return INDEX

@app.get("/manifest.json")
def m(): return Response(MANIFEST,media_type="application/json")

@app.get("/sw.js")
def w(): return Response(SW,media_type="application/javascript")

@app.get("/icon.png")
def i(): return Response(ICON,media_type="image/png")

def clean(n):
 return "".join(c for c in n if c.isalnum() or c in (" ","_","-")).strip()

@app.post("/save-sample")
async def save(name:str=Form(...),audio:UploadFile=Form(...),api_key:str=Form("")):
 s=clean(name)
 if not s: return JSONResponse(status_code=400,content={"error":"اسم غير صالح"})
 key=api_key.strip() or os.getenv("FISH_API_KEY","")
 if not key: return JSONResponse(status_code=400,content={"error":"أدخل مفتاح Fish Audio فالإعدادات أولاً"})
 p=BD/"samples"/(s+".wav"); p.write_bytes(await audio.read())
 try:
  vid=fish_create_voice(key,str(p))
  db[s]={"wav":str(p),"vid":vid}
  return {"ok":True,"message":"تم حفظ العينة ✅"}
 except Exception as e:
  return JSONResponse(status_code=500,content={"error":"خطأ: "+str(e)})


@app.get("/download/{vname}")
def download(vname:str):
 if vname not in last: return JSONResponse(status_code=404,content={"error":"ولّد الصوت أولاً"})
 f=BD/"outputs"/last[vname]
 if not f.exists(): return JSONResponse(status_code=404,content={"error":"الملف اتحذف — ولّد من جديد"})
 return FileResponse(f,media_type="audio/mpeg",filename="sawti-"+vname+".mp3")

@app.get("/voices")
def vs(): return {"voices":list(db.keys())}

@app.post("/speak")
async def speak(name:str=Form(...),text:str=Form(...),api_key:str=Form("")):
 if name not in db: return JSONResponse(status_code=404,content={"error":"احفظ عينة أولاً"})
 key=api_key.strip() or os.getenv("FISH_API_KEY","")
 if not key: return JSONResponse(status_code=400,content={"error":"أدخل مفتاح Fish Audio"})
 if not text.strip(): return JSONResponse(status_code=400,content={"error":"اكتب نص أولاً"})
 try:
  audio=fish_tts(key,db[name]["vid"],text)
  o=BD/"outputs"/(name+str(int(time.time()))+".mp3"); o.write_bytes(audio)
  last[name]=o.name
  return FileResponse(o,media_type="audio/mpeg",filename=o.name)
 except Exception as e: return JSONResponse(status_code=500,content={"error":"خطأ: "+str(e)})
