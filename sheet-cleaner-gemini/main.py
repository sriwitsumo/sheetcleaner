import os
import base64
import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import urllib.request
import urllib.error

app = FastAPI(title="Sheet Cleaner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

SYSTEM_PROMPT = """คุณคือ AI ที่วิเคราะห์ชีทเรียน ลบลายมือออก และแปลงเนื้อหาเป็น clean structured format

กฎ:
- ข้อความที่พิมพ์ (ไม่ใช่ลายมือ) ให้แปลงเป็น text ที่สะอาด
- ลายมือที่เขียนไว้ในชีท ให้ละเว้นทั้งหมด ไม่ต้องแปลง
- รูปภาพหรือ diagram ที่พิมพ์มา ให้ระบุตำแหน่งและอธิบายว่าคือรูปอะไร
- จัดเรียง element ตามลำดับจากบนลงล่างให้เหมือนต้นฉบับ
- สูตรคณิตศาสตร์ให้แปลงเป็น LaTeX ถ้าทำได้
- ตอบเป็น JSON เท่านั้น ไม่มี preamble ไม่มี markdown backtick

Format ที่ต้องตอบ:
{
  "title": "ชื่อหัวข้อของชีท (ถ้ามี)",
  "elements": [
    { "type": "heading", "content": "ข้อความหัวข้อ", "level": 1 },
    { "type": "text", "content": "ข้อความปกติ" },
    { "type": "image", "description": "อธิบายว่ารูปคือรูปอะไร", "position": "กลางหน้า" },
    { "type": "formula", "content": "สูตร", "latex": "LaTeX" },
    { "type": "table", "headers": ["หัวข้อ1","หัวข้อ2"], "rows": [["ข้อมูล1","ข้อมูล2"]] }
  ]
}"""


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/process")
async def process_sheets(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="ไม่มีไฟล์")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ไม่พบ GEMINI_API_KEY")

    results = []
    for file in files:
        if not file.content_type.startswith("image/"):
            continue

        content = await file.read()
        b64 = base64.standard_b64encode(content).decode("utf-8")
        media_type = file.content_type

        try:
            payload = {
                "system_instruction": {
                    "parts": [{"text": SYSTEM_PROMPT}]
                },
                "contents": [{
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": media_type,
                                "data": b64
                            }
                        },
                        {
                            "text": "วิเคราะห์ชีทนี้และส่งคืนเป็น JSON ตาม format ที่กำหนด"
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 2000
                }
            }

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            raw = data["candidates"][0]["content"]["parts"][0]["text"]
            clean = raw.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean)
            parsed["filename"] = file.filename
            results.append(parsed)

        except json.JSONDecodeError:
            results.append({
                "filename": file.filename,
                "title": file.filename,
                "elements": [{"type": "text", "content": raw}]
            })
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise HTTPException(status_code=502, detail=f"Gemini API error: {err_body}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content={"pages": results})
