# สร้างไฟล์ .env สำหรับบอท - รันไฟล์นี้แล้วใส่ Token ได้เลย
import pathlib

print("=== สร้างไฟล์ .env สำหรับ Granado Boss Bot ===")
print("ไฟล์ .env จะซ่อนใน Windows มองไม่เห็นด้วยตาเปล่าเป็นปกติ")
print()

token = input("ใส่ DISCORD_TOKEN (วางโทเคนบอท): ").strip()
channel = input("ใส่ CHANNEL_ID (ไอดีแชนแนลแจ้งเตือน, ถ้าไม่มีกด Enter ข้าม): ").strip()

env_content = f"DISCORD_TOKEN={token}\nCHANNEL_ID={channel}\n"

p = pathlib.Path(".env")
p.write_text(env_content, encoding="utf-8")
print()
print(f"✅ สร้างไฟล์ {p.absolute()} สำเร็จ!")
print("เนื้อหา:")
print(env_content)
print()
print("ตอนนี้รัน python bot.py ได้เลย มันจะอ่านไฟล์ .env นี้อัตโนมัติ")
input("กด Enter เพื่อปิด...")
