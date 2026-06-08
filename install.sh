#!/usr/bin/env bash
set -e

echo "==> Update package index"
sudo apt update

echo "==> Install Python, pip, venv, dan git"
sudo apt install -y python3 python3-pip python3-venv git

echo "==> Buat virtual environment"
python3 -m venv venv

echo "==> Install dependencies"
./venv/bin/python -m pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "==> Siapkan folder runtime"
mkdir -p reports logs data

if [ ! -f .env ]; then
  echo "==> Membuat .env dari .env.example"
  cp .env.example .env
else
  echo "==> .env sudah ada, tidak ditimpa"
fi

echo ""
echo "Instalasi selesai."
echo "Langkah berikutnya:"
echo "1. Edit file .env dan isi TELEGRAM_BOT_TOKEN serta TELEGRAM_CHAT_ID jika ingin kirim Telegram."
echo "2. Jalankan: ./venv/bin/python main.py scan"
echo "3. Tes Telegram: ./venv/bin/python main.py test-telegram"
echo "4. Untuk otomatis via cron, lihat contoh di README.md."

