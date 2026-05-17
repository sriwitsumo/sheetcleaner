# Sheet Cleaner (Gemini Version)

แอปลบลายมือออกจากชีทเรียน ใช้ Google Gemini AI (ฟรี)

## วิธี Deploy บน Render

### ขั้นที่ 1 — สร้าง API Key ใหม่ (ปลอดภัย)
1. ไปที่ https://aistudio.google.com/apikey
2. คลิก Create API Key
3. **เก็บ key ไว้ในที่ปลอดภัย ห้ามแชร์ใน chat หรือ code**

### ขั้นที่ 2 — อัปโหลดขึ้น GitHub
1. สมัคร https://github.com (ถ้ายังไม่มี)
2. สร้าง repository ใหม่ชื่อ sheet-cleaner → Private
3. Add file → Upload files → ลากไฟล์ทั้งหมดขึ้นไป
4. Commit changes

### ขั้นที่ 3 — Deploy บน Render
1. สมัคร https://render.com ด้วย GitHub
2. New → Web Service → เลือก repo sheet-cleaner
3. ตั้งค่า:
   - Runtime: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
4. Environment Variables → Add:
   - Key: GEMINI_API_KEY
   - Value: (วาง API key ที่ได้จากขั้นที่ 1)
5. Create Web Service → รอ 3-5 นาที

## รันบนเครื่องเพื่อทดสอบ

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=AIza....(key ของคุณ)
uvicorn main:app --reload
# เปิด http://localhost:8000
```
