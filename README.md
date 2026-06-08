# idx-free-stock-analyzer-bot

Bot Python untuk screening saham Indonesia/IDX menggunakan data harga harian gratis dari Yahoo Finance melalui `yfinance`. Bot menghitung indikator teknikal, volume, trend, breakout, RSI, MACD, support, resistance, risk plan, dan skor 0-100 untuk membantu membuat watchlist harian.

## Disclaimer

Analisa ini hanya alat bantu screening, bukan rekomendasi beli/jual resmi. Semua keputusan transaksi dan risiko ditanggung masing-masing investor.

## Batasan Data Gratis

- Data berasal dari Yahoo Finance/yfinance dan bisa delay.
- Bukan data real-time resmi IDX.
- Bukan broker summary real-time.
- Bukan data orderbook real-time.
- Bukan data net buy/net sell sekuritas.
- Cocok untuk screening harian, bukan scalping real-time.

## Fitur

- Scan semua saham dari `data/stocks.csv`.
- Otomatis mengubah kode IDX menjadi format Yahoo Finance `.JK`, contoh `BBCA` menjadi `BBCA.JK`.
- Ambil data harga harian minimal 1 tahun. Default kode memakai `2y` agar MA200 lebih stabil.
- Hitung MA5, MA10, MA20, MA50, MA100, MA200, EMA12, EMA26, RSI14, MACD, MACD Signal, MACD Histogram, Volume MA20, Volume Ratio, Support 20H, Resistance 20H, ATR14, perubahan harian, mingguan, dan bulanan.
- Scoring 0-100 dan klasifikasi: Sangat Kuat Dipantau, Menarik Dipantau, Watchlist, Netral, Belum Menarik.
- Analisa breakout, volume, trend, RSI, MACD golden cross, support/resistance, dan risiko.
- Hitung entry area, stop loss, target 1, target 2, dan risk reward.
- Output terminal, laporan TXT, SQLite, export CSV, dan Telegram.
- Tetap lanjut jika satu ticker gagal atau data kosong.

## Struktur Project

```text
idx-free-stock-analyzer-bot/
|-- app/
|   |-- __init__.py
|   |-- config.py
|   |-- data_fetcher.py
|   |-- indicators.py
|   |-- analyzer.py
|   |-- scoring.py
|   |-- risk_manager.py
|   |-- telegram_bot.py
|   |-- database.py
|   |-- report_generator.py
|   `-- scheduler.py
|-- data/
|   |-- stocks.csv
|   `-- watchlist.csv
|-- reports/
|   `-- .gitkeep
|-- logs/
|   `-- .gitkeep
|-- .env.example
|-- requirements.txt
|-- README.md
|-- main.py
`-- install.sh
```

## Upload ke VPS Ubuntu

Contoh lokasi deploy:

```bash
sudo mkdir -p /var/www
cd /var/www
git clone <URL_REPOSITORY_ANDA> idx-free-stock-analyzer-bot
cd idx-free-stock-analyzer-bot
```

Jika upload manual, kirim folder `idx-free-stock-analyzer-bot` ke VPS, misalnya dengan `scp`:

```bash
scp -r idx-free-stock-analyzer-bot user@IP_SERVER:/var/www/
```

## Install di VPS

```bash
cd /var/www/idx-free-stock-analyzer-bot
chmod +x install.sh
./install.sh
```

Setelah install, edit `.env`:

```bash
nano .env
```

## Konfigurasi .env

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
MIN_SCORE=65
TOP_N=10
SCAN_TIME=16:30
TIMEZONE=Asia/Jakarta
```

Keterangan:

- `TELEGRAM_BOT_TOKEN`: token bot Telegram dari BotFather.
- `TELEGRAM_CHAT_ID`: chat ID tujuan pengiriman laporan.
- `MIN_SCORE`: batas skor minimum untuk kebutuhan filter lanjutan.
- `TOP_N`: jumlah saham teratas yang dikirim ke Telegram.
- `SCAN_TIME`: jam scheduler internal Python.
- `TIMEZONE`: zona waktu, default `Asia/Jakarta`.

Jika token Telegram kosong, program tidak error dan akan menampilkan pesan:

```text
Telegram belum dikonfigurasi. Laporan hanya ditampilkan di terminal.
```

## Membuat Telegram Bot

1. Buka Telegram dan cari `@BotFather`.
2. Kirim command `/newbot`.
3. Ikuti instruksi nama bot dan username bot.
4. Salin token yang diberikan BotFather.
5. Masukkan token ke `.env` sebagai `TELEGRAM_BOT_TOKEN`.

## Mendapatkan Chat ID Telegram

Cara sederhana:

1. Kirim pesan apa saja ke bot Telegram Anda.
2. Buka URL berikut di browser, ganti `<TOKEN>` dengan token bot:

```text
https://api.telegram.org/bot<TOKEN>/getUpdates
```

3. Cari bagian `chat`, lalu ambil nilai `id`.
4. Masukkan nilai tersebut ke `.env` sebagai `TELEGRAM_CHAT_ID`.

Untuk grup, masukkan bot ke grup terlebih dahulu, kirim pesan di grup, lalu cek `getUpdates`.

## Menjalankan Manual

Aktifkan virtual environment atau panggil Python dari venv langsung:

```bash
cd /var/www/idx-free-stock-analyzer-bot
./venv/bin/python main.py scan
```

Command yang tersedia:

```bash
python main.py scan
python main.py send
python main.py stock BBCA
python main.py export
python main.py schedule
python main.py telegram
python main.py test-telegram
```

Di VPS, gunakan:

```bash
./venv/bin/python main.py scan
./venv/bin/python main.py send
./venv/bin/python main.py stock BBCA
./venv/bin/python main.py export
./venv/bin/python main.py telegram
./venv/bin/python main.py test-telegram
```

## Menjalankan dari Telegram

Bot bisa menerima command langsung dari chat Telegram. Pastikan `.env` sudah berisi:

```env
TELEGRAM_BOT_TOKEN=token_bot_anda
TELEGRAM_CHAT_ID=chat_id_anda
```

Jalankan listener:

```bash
./venv/bin/python main.py telegram
```

Di Windows PowerShell:

```powershell
.\.venv\Scripts\python main.py telegram
```

Selama proses ini hidup, kirim command berikut dari Telegram:

```text
/help
/status
/stock BBCA
/scan
/send
/export
/disclaimer
```

Keterangan:

- `/stock BBCA` menganalisa satu saham dan membalas laporan lengkap.
- `/scan` atau `/send` scan semua saham, simpan TXT/SQLite, lalu kirim top hasil ke Telegram.
- `/export` scan semua saham, simpan TXT/SQLite/CSV, lalu mengirim file CSV ke Telegram.
- Bot hanya menerima command dari `TELEGRAM_CHAT_ID` yang ada di `.env`.

Catatan: command `/scan`, `/send`, dan `/export` bisa memakan waktu beberapa menit karena mengambil data dari yfinance.

## Output

- Laporan TXT: `reports/report_YYYY-MM-DD.txt`
- Export CSV: `reports/screening_YYYY-MM-DD.csv`
- Database SQLite: `data/scan_results.sqlite3`
- Log cron: `logs/cron.log`

## Menjalankan Otomatis dengan Cron

Buka crontab:

```bash
crontab -e
```

Tambahkan:

```cron
30 16 * * 1-5 cd /var/www/idx-free-stock-analyzer-bot && /var/www/idx-free-stock-analyzer-bot/venv/bin/python main.py send >> /var/www/idx-free-stock-analyzer-bot/logs/cron.log 2>&1
```

Cron ini menjalankan bot Senin-Jumat jam 16:30 WIB jika timezone server sudah diatur ke WIB.

Cek timezone server:

```bash
timedatectl
```

Atur ke WIB:

```bash
sudo timedatectl set-timezone Asia/Jakarta
```

## Scheduler Internal Python

Alternatif selain cron:

```bash
./venv/bin/python main.py schedule
```

Command ini menjalankan scan Senin-Jumat sesuai `SCAN_TIME` di `.env`. Untuk produksi, cron atau systemd lebih stabil.

## Contoh Systemd Service

Buat file:

```bash
sudo nano /etc/systemd/system/idx-stock-bot.service
```

Isi:

```ini
[Unit]
Description=IDX Free Stock Analyzer Bot Scheduler
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/var/www/idx-free-stock-analyzer-bot
ExecStart=/var/www/idx-free-stock-analyzer-bot/venv/bin/python main.py schedule
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Aktifkan:

```bash
sudo systemctl daemon-reload
sudo systemctl enable idx-stock-bot
sudo systemctl start idx-stock-bot
sudo systemctl status idx-stock-bot
```

## Menambah atau Mengubah Daftar Saham

Edit `data/stocks.csv`, satu kode saham per baris tanpa `.JK`:

```text
BBCA
BBRI
BMRI
ANTM
```

Program akan otomatis memakai format Yahoo Finance, contoh `ANTM.JK`.

## Catatan Error Handling

- Jika satu ticker gagal, scan tetap lanjut.
- Jika data kosong, ticker dilewati.
- Jika internet bermasalah, pesan error ditampilkan jelas.
- Jika Telegram gagal, laporan TXT dan SQLite tetap tersimpan.
- Folder `reports/` dan `logs/` dibuat otomatis jika belum ada.
