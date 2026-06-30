import os, io
from flask import Flask, render_template_string, request, Response, stream_with_context
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image
import torch

AI_NAME = "NileMind AI"
DEV_CHANNEL = "https://whatsapp.com/channel/0029Vb8vFQw2kNFqPIWe3B3H"

print(f"⏳ جاري تشغيل {AI_NAME}...")
model_id = "Qwen/Qwen2-VL-2B-Instruct"
model = Qwen2VLForConditionalGeneration.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto")
processor = AutoProcessor.from_pretrained(model_id)
print(f"✅ {AI_NAME} جاهز")

app = Flask(__name__)

HTML = f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><title>{AI_NAME}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
<style>:root{{--bg:#0d1117;--card:#161b22;--border:#30363d;--text:#c9d1d9;--accent:#58a6ff;--user:#21262d;--green:#25D366;}}
body{{background:var(--bg);color:var(--text);font-family:'Cairo';margin:0;display:flex;flex-direction:column;height:100vh;}}
header{{display:flex;justify-content:space-between;align-items:center;padding:12px 20px;border-bottom:1px solid var(--border);}}
.logo{{font-size:22px;font-weight:700;color:var(--accent);}}.logo span{{font-size:14px;display:block;font-weight:400;color:#8b949e;}}
.dev-btn{{background:var(--green);color:white;text-decoration:none;padding:10px 16px;border-radius:10px;font-weight:700;font-size:14px;}}
#chat{{flex:1;overflow-y:auto;padding:20px;}}.msg{{max-width:700px;margin:12px auto;padding:14px 18px;border-radius:14px;white-space:pre-wrap;}}
.user{{background:var(--user);text-align:right;}}.ai{{background:var(--card);border:1px solid var(--border);}}
#input{{display:flex;flex-direction:column;padding:15px;gap:10px;border-top:1px solid var(--border);}}
.row{{display:flex;gap:10px;}}#input input,#input textarea{{flex:1;padding:14px;border-radius:10px;border:1px solid var(--border);background:var(--card);color:var(--text);}}
#input button{{padding:14px 24px;border:none;border-radius:10px;background:#238636;color:white;font-weight:700;cursor:pointer;}}
#preview img{{max-width:150px;border-radius:8px;}}.loading::after{{content:'...';animation:dots 1.5s steps(3,end) infinite;}}@keyframes dots{{0%,20%{{content:'.';}}40%{{content:'..';}}60%,100%{{content:'...';}}}}
</style></head><body>
<header><div class="logo">🤖 {AI_NAME}<span>يرى الصور + يقرأ الملفات</span></div><a href="{DEV_CHANNEL}" target="_blank" class="dev-btn">قناة المطور 🕊️</a></header>
<div id="chat"><div class="msg ai">سلام 👋\nانا {AI_NAME} عقل النيل.\nارسل صورة، PDF، او اسألني.</div></div>
<div id="input"><div class="row"><input type="file" id="file" accept="image/*,.pdf,.txt,.py,.js,.docx"><textarea id="q" rows="1" placeholder="اسأل..."></textarea><button onclick="send()">إرسال</button></div><div id="preview"></div></div>
<script>
document.getElementById('file').onchange=e=>{{let f=e.target.files[0];if(!f)return;document.getElementById('preview').innerHTML=f.type.startsWith('image/')?`<img src="${{URL.createObjectURL(f)}}">`:`📎 ${{f.name}}`;}}
async function send(){{let q=document.getElementById('q'),f=document.getElementById('file').files[0];if(!q.value.trim()&&!f)return;let chat=document.getElementById('chat');chat.innerHTML+=`<div class="msg user">${{f?`📎 ${{f.name}}<br>`:''}}${{q.value}}</div>`;let aiDiv=document.createElement('div');aiDiv.className='msg ai loading';aiDiv.textContent='عقل النيل ببني الرد';chat.appendChild(aiDiv);chat.scrollTop=chat.scrollHeight;let fd=new FormData();fd.append('q',q.value);if(f)fd.append('file',f);let res=await fetch('/ask',{{method:'POST',body:fd}});let reader=res.body.getReader();aiDiv.classList.remove('loading');aiDiv.textContent='';while(true){{let {{value,done}}=await reader.read();if(done)break;aiDiv.textContent+=new TextDecoder().decode(value);chat.scrollTop=chat.scrollHeight;}}q.value='';document.getElementById('file').value='';document.getElementById('preview').innerHTML='';}}
document.getElementById('q').addEventListener('keypress',e=>{{if(e.key==='Enter'&&!e.shiftKey){{e.preventDefault();send()}}}});
</script></body></html>"""

def read_file(file):
    if file.mimetype.startswith('image/'): return Image.open(file.stream).convert("RGB")
    else: return file.stream.read().decode('utf-8', errors='ignore')[:2000]

@app.route("/")
def home(): return render_template_string(HTML)

@app.route("/ask", methods=["POST"])
def ask():
    q = request.form.get("q", ""); file = request.files.get("file")
    messages = [{"role": "system", "content": f"انت {AI_NAME}. ذكاء اصطناعي سوداني. ردك مختصر وباللهجة السودانية."}]
    content = []; if q: content.append({"type": "text", "text": q})
    if file:
        data = read_file(file)
        if isinstance(data, Image.Image): content.append({"type": "image", "image": data});
        if not q: q = "اوصف لي الصورة دي بالسوداني"
        else: content.append({"type": "text", "text": f"محتوى الملف:\n{data}\n\nسؤال: {q}"})
    messages.append({"role": "user", "content": content})
    def generate():
        inputs = processor.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(model.device)
        output_ids = model.generate(**inputs, max_new_tokens=256, do_sample=True, temperature=0.8)
        output = processor.batch_decode(output_ids[:, inputs['input_ids'].shape[1]:], skip_special_tokens=True)[0]
        for word in output.split(): yield word + " "; import time; time.sleep(0.02)
    return Response(stream_with_context(generate()), mimetype='text/plain')

if __name__ == "__main__": app.run(host="0.0.0.0", port=7860)
