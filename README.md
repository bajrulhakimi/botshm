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

- Scan 300 saham IDX lintas sektor dari `data/stocks.csv`.
- Pilih universe/group saham seperti `all`, `lq45`, `idx30`, `idx80`, `kompas100`, `jii`, `high-dividend`, `esg`, `msci`, `banking`, `energy`, `mining`, `consumer`, `telecom`, `property`, dan `technology`.
- Otomatis mengubah kode IDX menjadi format Yahoo Finance `.JK`, contoh `BBCA` menjadi `BBCA.JK`.
- Ambil data harga harian minimal 1 tahun. Default kode memakai `2y` agar MA200 lebih stabil.
- Hitung MA5, MA10, MA20, MA50, MA100, MA200, EMA12, EMA26, RSI14, MACD, MACD Signal, MACD Histogram, Volume MA20, Volume Ratio, Support 20H, Resistance 20H, ATR14, perubahan harian, mingguan, dan bulanan.
- Scoring 0-100 dan klasifikasi: Sangat Kuat Dipantau, Menarik Dipantau, Watchlist, Netral, Belum Menarik.
- Analisa breakout, volume, trend, RSI, MACD golden cross, support/resistance, dan risiko.
- Hitung entry area, stop loss, target 1, target 2, dan risk reward.
- Output terminal, laporan TXT, SQLite, export CSV, dan Telegram.
- Laporan terstruktur menjadi informasi scan, ringkasan skor, peringkat hasil, sinyal pasar, support/resistance, rencana transaksi, alasan skor, dan peringatan risiko.
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
|   |-- groups/
|   |   |-- all.csv
|   |   |-- lq45.csv
|   |   |-- idx30.csv
|   |   `-- ...
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
python main.py scan --group lq45
python main.py send
python main.py send --group idx30
python main.py stock BBCA
python main.py export
python main.py export --group msci
python main.py groups
python main.py schedule
python main.py telegram
python main.py test-telegram
```

Di VPS, gunakan:

```bash
./venv/bin/python main.py scan
./venv/bin/python main.py scan --group lq45
./venv/bin/python main.py send
./venv/bin/python main.py send --group idx30
./venv/bin/python main.py stock BBCA
./venv/bin/python main.py export
./venv/bin/python main.py export --group msci
./venv/bin/python main.py groups
./venv/bin/python main.py telegram
./venv/bin/python main.py test-telegram
```

Default:

- `python main.py scan` sama dengan `python main.py scan --group all`.
- `python main.py send` sama dengan `python main.py send --group all`.
- `python main.py export` sama dengan `python main.py export --group all`.

Jika group salah, program menampilkan:

```text
Group tidak ditemukan. Gunakan python main.py groups untuk melihat daftar group.
```

## Group Saham

Daftar group tersedia:

```bash
python main.py groups
```

Output:

```text
Available groups:
- all
- lq45
- idx30
- idx80
- kompas100
- jii
- high-dividend
- esg
- msci
- banking
- energy
- mining
- consumer
- telecom
- property
- technology
```

File group ada di `data/groups/`:

```text
data/groups/
|-- all.csv
|-- lq45.csv
|-- idx30.csv
|-- idx80.csv
|-- kompas100.csv
|-- jii.csv
|-- high-dividend.csv
|-- esg.csv
|-- msci.csv
|-- banking.csv
|-- energy.csv
|-- mining.csv
|-- consumer.csv
|-- telecom.csv
|-- property.csv
`-- technology.csv
```

Format CSV:

```csv
symbol,name
BBCA,Bank Central Asia Tbk
BBRI,Bank Rakyat Indonesia Tbk
BMRI,Bank Mandiri Tbk
```

Catatan penting:

- `all` tetap membaca semua saham dari `data/stocks.csv`.
- File `data/groups/all.csv` disediakan sebagai referensi manual.
- Daftar indeks seperti LQ45, IDX30, IDX80, Kompas100, JII, High Dividend, ESG, dan MSCI bisa berubah berkala.
- Karena bot ini memakai data gratis dan tidak memakai API premium IDX/MSCI, isi `data/groups/*.csv` dibuat manual dan perlu diupdate berkala.

Cara menambah saham ke group:

1. Buka file group, contoh `data/groups/lq45.csv`.
2. Tambahkan baris baru:

```csv
BBTN,Bank Tabungan Negara Tbk
```

3. Simpan file, lalu jalankan:

```bash
python main.py scan --group lq45
```

Cara menghapus saham dari group:

1. Buka file group.
2. Hapus baris saham yang tidak ingin discan.
3. Simpan file.

Cara update daftar LQ45/IDX30/MSCI manual:

1. Cek pengumuman indeks terbaru dari BEI/IDX, Kustodian, manajer investasi indeks, atau penyedia indeks terkait.
2. Edit file group yang sesuai, contoh `data/groups/lq45.csv`, `data/groups/idx30.csv`, atau `data/groups/msci.csv`.
3. Pastikan kolom pertama adalah kode saham tanpa `.JK`.
4. Jalankan scan ulang:

```bash
python main.py scan --group lq45
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
/scan lq45
/send
/send idx30
/export msci
/groups
/disclaimer
```

Keterangan:

- `/stock BBCA` menganalisa satu saham dan membalas laporan lengkap.
- `/scan` atau `/send` scan group `all`, simpan TXT/SQLite, lalu kirim top hasil ke Telegram.
- `/scan lq45` atau `/send idx30` scan group tertentu.
- `/export msci` scan group tertentu, simpan TXT/SQLite/CSV, lalu mengirim file CSV ke Telegram.
- `/groups` menampilkan daftar group yang tersedia.
- Bot hanya menerima command dari `TELEGRAM_CHAT_ID` yang ada di `.env`.

Catatan: command `/scan`, `/send`, dan `/export` bisa memakan waktu beberapa menit karena mengambil data dari yfinance.

## Output

- Laporan TXT: `reports/report_GROUP_YYYY-MM-DD.txt`
- Export CSV: `reports/screening_GROUP_YYYY-MM-DD.csv`
- Database SQLite: `data/scan_results.sqlite3`
- Log cron: `logs/cron.log`

Contoh:

```text
reports/report_lq45_YYYY-MM-DD.txt
reports/report_idx30_YYYY-MM-DD.txt
reports/report_msci_YYYY-MM-DD.txt
reports/report_all_YYYY-MM-DD.txt
reports/screening_lq45_YYYY-MM-DD.csv
```

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
