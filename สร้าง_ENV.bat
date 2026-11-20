@echo off
echo === สร้างไฟล์ .env ===
set /p TOKEN=ใส่ DISCORD_TOKEN: 
set /p CHANNEL=ใส่ CHANNEL_ID (ว่างได้): 
echo DISCORD_TOKEN=%TOKEN%> .env
echo CHANNEL_ID=%CHANNEL%>> .env
echo.
echo สร้าง .env สำเร็จ!
type .env
echo.
echo กดอะไรก็ได้เพื่อปิดและรัน bot.py
pause
python bot.py
