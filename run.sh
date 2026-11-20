#!/bin/bash
echo "=== Granado Espada M Boss Bot ==="
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  echo "ไม่พบ .env เรียกตัวช่วยสร้าง..."
  python3 setup_env.py
fi

echo "เริ่มรันบอท + เว็บที่ http://localhost:5000"
python3 bot.py
