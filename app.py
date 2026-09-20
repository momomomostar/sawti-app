# -*- coding: utf-8 -*-
# صوتي - تحويل الصوت الحقيقي (Kits.AI)
import os,time,json,urllib.request
from pathlib import Path
from fastapi import FastAPI,UploadFile,Form,Query
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
app=FastAPI(title="صوتي - تحويل الصوت")
BD=Path(__file__).parent
(BD/"outputs").mkdir(exist_ok=True)
db={}

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
input,select{width:100%;padding:10px;border-radius:10px;border:1px solid #555;background:#2a2a3d;color:#fff;margin-bottom:10px;font-size:1rem}
button{padding:10px;border:none;border-radius:10px;font-size:1rem;font-weight:bold;cursor:pointer;width:100%}
.b1{background:#8be9fd;color:#1e1e2f}.b2{background:#ff5555;color:#fff}.b2r{background:#50fa7b}
.m{margin-top:10px;padding:10px;border-radius:10px;text-align:center;display:none}
.ok{background:rgba(80,250,123,.15);color:#50fa7b;display:block}.er{background:rgba(255,85,85,.15);color:#ff6b6b;display:block}
audio{width:100%;margin-top:10px}
.up{display:block;background:#2a2a3d;border:1px dashed #555;border-radius:10px;padding:12px;text-align:center;cursor:pointer;margin-bottom:10px}
</style></head><body>
<h1>🎙️ صوتي</h1>
<div class="c"><h2>⚙️ الإعدادات</h2>
<input id="k" type="password" placeholder="مفتاح Kits.AI (من app.kits.ai/api-access)">
</div>
<div class="c"><h2>1️⃣ سجّل صوت الهدف</h2>
<input id="n" type="text" placeholder="اسم الصوت (مثال: صديقي)">
<input id="mid" type="number" placeholder="رقم الموديل من Kits (مثال: 12345)">
<button id="s" class="b1">💾 حفظ الصوت</button>
<div id="m1" class="m"></div></div>
<div class="c"><h2>2️⃣ 🎤 هضر وتحوّل</h2>
<select id="v2"></select>
<button id="r2" class="b2">🔴 سجّل رسالتك</button>
<div style="text-align:center;color:#aaa;margin:10px 0">— ولا —</div>
<label class="up">📂 اختر تسجيل جاهز<input id="f2" type="file" accept="audio/*" style="display:none"></label>
<button id="c2" class="b1" style="margin-top:8px" disabled>🔄 حوّل لصوت الهدف</button>
<div id="m3" class="m"></div>
<audio id="p" controls style="display:none"></audio></div>
<script>
var $=function(id){return document.getElementById(id)};
var k=$('k');k.value=localStorage.getItem('kk')||'';
k.oninput=function(){localStorage.setItem('kk',k.value)};
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
$('r2').onclick=async function(){
 if(!rc){try{
  stm=await navigator.mediaDevices.getUserMedia({audio:true});
  actx=new (window.AudioContext||window.webkitAudioContext)({sampleRate:44100});
  src=actx.createMediaStreamSource(stm);rec=actx.createScriptProcessor(4096,1,1);ch=[];
  rec.onaudioprocess=function(e){ch.push(new Float32Array(e.inputBuffer.getChannelData(0)))};
  src.connect(rec);rec.connect(actx.destination);
  rc=true;this.textContent='⏹️ إيقاف';this.classList.add('b2r');
 }catch(e){msg('m3','الميكروفون مرفوض',0)}}
 else{rec.disconnect();src.disconnect();stm.getTracks().forEach(function(t){t.stop()});actx.close();
  bl=wavBlob();rc=false;this.textContent='🔴 سجّل رسالتك';this.classList.remove('b2r');
  $('c2').disabled=false;msg('m3','تم التسجيل ✅',1)}
};
$('f2').onchange=function(){var file=this.files[0];if(!file)return;
 if(file.size>90*1024*1024){msg('m3','الملف كبير (الحد 90MB)',0);this.value='';return}
 bl=file;$('c2').disabled=false;msg('m3','تم اختيار الملف ✅',1)};
$('s').onclick=async function(){
 var n=$('n').value.trim(),mid=$('mid').value.trim();
 if(!n||!mid){msg('m1','اكتب الاسم ورقم الموديل',0);return}
 var f=new FormData();f.append('name',n);f.append('model_id',mid);f.append('api_key',k.value);
 var d=await (await fetch('/save-voice',{method:'POST',body:f})).json();
 msg('m1',d.message||d.error,!!d.ok);ld()};
async function ld(){var d=await (await fetch('/voices')).json();$('v2').innerHTML='';
 d.voices.forEach(function(x){var o=document.createElement('option');o.value=o.textContent=x;$('v2').appendChild(o)})}
ld();
$('c2').onclick=async function(){
 var f=new FormData();
 f.append('name',$('v2').value);f.append('audio',bl,'msg.wav');f.append('api_key',k.value);
 msg('m3','جارٍ إرسال التحويل... ⏳',1);$('c2').disabled=true;
 try{
  var d=await (await fetch('/convert',{method:'POST',body:f})).json();
  if(!d.job){msg('m3','خطأ: '+(d.error||'؟'),0);$('c2').disabled=false;return}
  msg('m3','التحويل قيد المعالجة... استنى ⏳',1);
  for(var i=0;i<48;i++){
   await new Promise(function(r){setTimeout(r,5000)});
   var res=await fetch('/job/'+d.job+'?api_key='+encodeURIComponent(k.value));
   if(res.status===202){msg('m3','لسّا كيخدم... ('+(i+1)+') ⏳',1);continue}
   if(res.ok){var u=URL.createObjectURL(await res.blob());var p=$('p');
    p.src=u;p.style.display='block';p.play();msg('m3','تم التحويل! 🎧',1);$('c2').disabled=false;return}
   var e=await res.json();msg('m3','خطأ: '+(e.error||'؟'),0);$('c2').disabled=false;return;
  }
  msg('m3','طال الانتظار — عاود من جديد',0);
 }catch(err){msg('m3','خطأ: '+err,0)}
 $('c2').disabled=false;
};
function msg(id,t,ok){var e=$(id);e.textContent=t;e.className='m '+(ok?'ok':'er')}
</script></body></html>"""

MANIFEST=r"""{"name":"صوتي","short_name":"صوتي","start_url":"/","display":"standalone","dir":"rtl","lang":"ar","background_color":"#1e1e2f","theme_color":"#1e1e2f","icons":[{"src":"/icon.png","sizes":"192x192","type":"image/png"},{"src":"/icon.png","sizes":"512x512","type":"image/png"}]}"""

SW=r"""self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>e.waitUntil(clients.claim()));self.addEventListener('fetch',e=>e.respondWith(fetch(e.request)));"""

KITS="https://arpeggi.io/api/kits/v1"
def _auth(key): return {"Authorization":"Bearer "+key}
def _fld(b,n,v): return ("--"+b+"\r\nContent-Disposition: form-data; name=\""+n+"\"\r\n\r\n"+v+"\r\n").encode()

def kits_create_job(key,model_id,data):
 import uuid
 b="----sawti"+uuid.uuid4().hex
 body=_fld(b,"voiceModelId",str(model_id))
 body+=("--"+b+"\r\nContent-Disposition: form-data; name=\"soundFile\"; filename=\"msg.wav\"\r\nContent-Type: audio/wav\r\n\r\n").encode()
 body+=data+b"\r\n--"+b.encode()+b"--\r\n"
 req=urllib.request.Request(KITS+"/voice-conversions",data=body,
  headers=dict(_auth(key),**{"Content-Type":"multipart/form-data; boundary="+b}))
 return json.loads(urllib.request.urlopen(req,timeout=120).read())

def kits_fetch_job(key,jid):
 req=urllib.request.Request(KITS+"/voice-conversions/"+str(jid),headers=_auth(key))
 return json.loads(urllib.request.urlopen(req,timeout=60).read())


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

@app.post("/save-voice")
async def save_voice(name:str=Form(...),model_id:str=Form(...),api_key:str=Form("")):
 s=clean(name)
 if not s: return JSONResponse(status_code=400,content={"error":"اسم غير صالح"})
 try: mid=int(model_id)
 except: return JSONResponse(status_code=400,content={"error":"رقم الموديل خاصو يكون رقم (مثال: 12345)"})
 key=api_key.strip() or os.getenv("KITS_API_KEY","")
 if not key: return JSONResponse(status_code=400,content={"error":"أدخل مفتاح Kits.AI فالإعدادات"})
 db[s]=mid
 return {"ok":True,"message":"تم حفظ الصوت ✅"}

@app.get("/voices")
def vs(): return {"voices":list(db.keys())}

@app.post("/convert")
async def convert(name:str=Form(...),audio:UploadFile=Form(...),api_key:str=Form("")):
 if name not in db: return JSONResponse(status_code=404,content={"error":"سجّل الصوت أولاً (الخطوة 1)"})
 key=api_key.strip() or os.getenv("KITS_API_KEY","")
 if not key: return JSONResponse(status_code=400,content={"error":"أدخل مفتاح Kits.AI"})
 data=await audio.read()
 try:
  job=kits_create_job(key,db[name],data)
  return {"job":job["id"]}
 except Exception as e:
  return JSONResponse(status_code=500,content={"error":"خطأ: "+str(e)})

@app.get("/job/{jid}")
def job(jid:int,api_key:str=Query("")):
 key=api_key.strip() or os.getenv("KITS_API_KEY","")
 if not key: return JSONResponse(status_code=400,content={"error":"أدخل المفتاح"})
 try:
  j=kits_fetch_job(key,jid)
  st=j.get("status")
  if st=="running": return JSONResponse(status_code=202,content={"status":"running"})
  if st=="success":
   url=j.get("outputFileUrl") or j.get("lossyOutputFileUrl")
   if not url: return JSONResponse(status_code=500,content={"error":"ما كاينش رابط النتيجة"})
   data=urllib.request.urlopen(url,timeout=120).read()
   o=BD/"outputs"/("out"+str(int(time.time()))+".wav"); o.write_bytes(data)
   return FileResponse(o,media_type="audio/wav",filename=o.name)
  return JSONResponse(status_code=500,content={"error":"فشل التحويل: "+str(st)})
 except Exception as e:
  return JSONResponse(status_code=500,content={"error":"خطأ: "+str(e)})
