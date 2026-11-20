# Granado Espada M - Boss Bot ตัวเต็มพร้อมรัน

## 📦 มีอะไรในโฟลเดอร์นี้
- bot.py - บอทหลัก (แก้บัค timezone-aware + waitress แล้ว)
- bosses.json - 12 บอสเวลาจริงเซิฟไทย 30/60/90/120/180น
- templates/index.html - เว็บแดชบอร์ดลิงก์ถาวรกับบอท
- requirements.txt - discord.py, flask, waitress, python-dotenv
- setup_env.py / สร้าง_ENV.bat - ตัวช่วยสร้างไฟล์ .env ที่ซ่อนใน Windows
- run.bat / run.sh - ดับเบิลคลิกรันได้เลย

## 🚀 วิธีรันเร็วสุด (Windows)

1. แตกไฟล์ zip นี้ไปที่ไหนก็ได้ เช่น Desktop
2. ดับเบิลคลิก `run.bat`
   - มันจะติดตั้งไลบรารี่ให้อัตโนมัติ
   - ถ้าไม่มี .env มันจะเปิดให้ใส่ Token เอง
3. ใส่:
   DISCORD_TOKEN= เอามาจาก https://discord.com/developers/applications > Bot > Token
   CHANNEL_ID= คลิกขวาที่แชนแนลใน Discord > Copy ID (เปิด Developer Mode ก่อน)
4. รอขึ้น:
   🌐 Web server running (PRODUCTION) on http://localhost:5000
   ✅ Logged in as ชื่อบอท

เสร็จแล้ว! บอทจะออนไลน์ใน Discord + เว็บที่ http://localhost:5000

## 💬 คำสั่งใน Discord

/boss list - ดูบอส 12 ตัว เรียงตามเวลาเหลือ
/boss info boss:ชื่อบอส - ดูตัวเดียวละเอียด
/boss kill boss:ชื่อบอส - แจ้งฆ่าแล้วรีเซ็ตเวลา (ลิงก์กับเว็บถาวร)

Prefix ก็ยังใช้ได้:
!kill ฮิลล์
!bosses

## 🌐 เว็บ

- http://localhost:5000 - เว็บหลักลิงก์ถาวรกับบอท
- กดปุ่ม Kill บนเว็บ = รีเซ็ตเวลาในดิสด้วย (ผ่าน boss_timers.json เดียวกัน)

## ⚠️ ถ้ามองไม่เห็น .env

ไฟล์ .env เป็นไฟล์ซ่อน Windows จะไม่โชว์
- เปิด File Explorer > View > ติ๊ก Hidden items
- หรือรัน setup_env.py เพื่อสร้างใหม่
- หรือพิมพ์ dir /a ใน cmd จะเห็น

## 🔧 แก้เวลาบอส

เปิด bosses.json แก้ respawn_min ได้เลย (นาที)
