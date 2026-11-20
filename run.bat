@echo off
echo === Granado Espada M Boss Bot - Full Ready ===
echo.

echo [1/2] ติดตั้งไลบรารี่...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [2/2] ตรวจสอบไฟล์ .env...
if not exist .env (
  echo ไม่พบไฟล์ .env จะเปิดตัวช่วยสร้าง...
  python setup_env.py
)

echo.
echo === เริ่มรันบอท + เว็บ ===
echo เว็บจะอยู่ที่ http://localhost:5000
echo กด Ctrl+C เพื่อหยุด
echo.
python bot.py
pause
