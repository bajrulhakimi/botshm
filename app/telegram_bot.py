from __future__ import annotations

import time
from typing import TYPE_CHECKING

import requests

from app.config import ensure_directories, settings
from app.report_generator import (
    DATA_LIMITATION,
    DISCLAIMER,
    format_pct,
    format_price,
    format_ratio,
    format_risk_reward,
    summarize_results,
    today_string,
)
from app.stock_universe import (
    DEFAULT_GROUP,
    GROUP_NOT_FOUND_MESSAGE,
    format_group_label,
    format_groups_list,
    get_available_groups,
    load_group_symbols,
    validate_group,
)

if TYPE_CHECKING:
    from app.analyzer import StockAnalysis


MAX_TELEGRAM_MESSAGE_LENGTH = 3900
OFFSET_FILE = settings.data_dir / "telegram_offset.txt"


HELP_MESSAGE = """
BOT ANALISA SAHAM IDX GRATIS

Command:
/help - tampilkan bantuan
/status - cek bot aktif
/stock BBCA - analisa satu saham
/scan - scan semua saham dan kirim top hasil
/scan lq45 - scan group tertentu
/send idx30 - sama seperti /scan untuk group tertentu
/export lq45 - scan group lalu kirim file CSV
/groups - tampilkan daftar group
/disclaimer - tampilkan disclaimer

Catatan: data dari yfinance bisa delay dan bukan data real-time resmi IDX.
""".strip()


def is_configured() -> bool:
    return bool(settings.telegram_bot_token and settings.telegram_chat_id)


def split_message(text: str, max_length: int = MAX_TELEGRAM_MESSAGE_LENGTH) -> list[str]:
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    current = ""
    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}".strip() if current else block
        if len(candidate) <= max_length:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = block
    if current:
        chunks.append(current)
    return chunks


def _telegram_url(method: str) -> str:
    return f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"


def send_message(text: str, chat_id: str | None = None) -> bool:
    target_chat_id = str(chat_id or settings.telegram_chat_id).strip()
    if not settings.telegram_bot_token or not target_chat_id:
        print("Telegram belum dikonfigurasi. Laporan hanya ditampilkan di terminal.")
        return False

    ok = True
    for chunk in split_message(text):
        try:
            response = requests.post(
                _telegram_url("sendMessage"),
                json={
                    "chat_id": target_chat_id,
                    "text": chunk,
                    "disable_web_page_preview": True,
                },
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            ok = False
            print(f"Gagal mengirim Telegram: {exc}")
    return ok


def send_document(file_path: str, caption: str = "", chat_id: str | None = None) -> bool:
    target_chat_id = str(chat_id or settings.telegram_chat_id).strip()
    if not settings.telegram_bot_token or not target_chat_id:
        print("Telegram belum dikonfigurasi. File tidak dikirim.")
        return False

    try:
        with open(file_path, "rb") as document:
            response = requests.post(
                _telegram_url("sendDocument"),
                data={"chat_id": target_chat_id, "caption": caption},
                files={"document": document},
                timeout=60,
            )
            response.raise_for_status()
    except (OSError, requests.RequestException) as exc:
        print(f"Gagal mengirim file Telegram: {exc}")
        return False
    return True


def build_top_results_message(
    results: list[StockAnalysis],
    top_n: int | None = None,
    group_name: str = DEFAULT_GROUP,
) -> str:
    shown_results = results[: top_n or settings.top_n]
    try:
        universe_size = len(load_group_symbols(group_name))
    except (FileNotFoundError, ValueError):
        universe_size = len(results)
    summary = summarize_results(results)
    skipped = max(0, universe_size - len(results))
    lines = [
        "HASIL SCREENING SAHAM IDX",
        "",
        "[INFORMASI SCAN]",
        f"Group: {format_group_label(group_name)}",
        f"Anggota: {universe_size} | Dianalisa: {len(results)} | Dilewati: {skipped}",
        f"Tanggal: {today_string()}",
        "",
        "[RINGKASAN SKOR]",
        f"Kandidat >= {settings.min_score}: {summary['qualified']}",
        f"Sangat Kuat: {summary['strong']} | Menarik: {summary['interesting']} | Watchlist: {summary['watchlist']}",
        f"Netral: {summary['neutral']} | Belum Menarik: {summary['not_interesting']}",
        "",
        f"[TOP {len(shown_results)} HASIL]",
        "",
    ]

    if not shown_results:
        lines.append("Tidak ada saham yang berhasil dianalisa.")

    for index, item in enumerate(shown_results, start=1):
        lines.extend(
            [
                f"#{index} {item.stock_code} | {item.score}/100 | {item.status}",
                f"Sinyal: {item.trend_status} | MACD {item.macd_status} | RSI {item.rsi:.2f}",
                f"Harga: {format_price(item.last_price)} | Harian {format_pct(item.daily_change)} | Volume {format_ratio(item.volume_ratio)}",
                f"Entry: {format_price(item.entry_low)} - {format_price(item.entry_high)}",
                f"SL: {format_price(item.stop_loss)} | T1: {format_price(item.target_1)} | T2: {format_price(item.target_2)} | RR {format_risk_reward(item.risk_reward)}",
                "",
            ]
        )

    lines.extend(["[BATASAN DATA]", DATA_LIMITATION, "", "[DISCLAIMER]", DISCLAIMER])
    return "\n".join(lines).strip()


def send_top_results(
    results: list[StockAnalysis],
    top_n: int | None = None,
    group_name: str = DEFAULT_GROUP,
) -> bool:
    return send_message(build_top_results_message(results, top_n=top_n, group_name=group_name))


def test_telegram() -> bool:
    return send_message(
        "Test Telegram idx-free-stock-analyzer-bot berhasil.\n\n"
        f"Disclaimer: {DISCLAIMER}"
    )


def _read_offset() -> int | None:
    if not OFFSET_FILE.exists():
        return None
    try:
        raw_value = OFFSET_FILE.read_text(encoding="utf-8").strip()
        return int(raw_value) if raw_value else None
    except (OSError, ValueError):
        return None


def _write_offset(offset: int) -> None:
    ensure_directories()
    OFFSET_FILE.write_text(str(offset), encoding="utf-8")


def _get_updates(offset: int | None) -> list[dict]:
    params = {"timeout": 30}
    if offset is not None:
        params["offset"] = offset
    response = requests.get(_telegram_url("getUpdates"), params=params, timeout=40)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram getUpdates gagal: {payload}")
    return payload.get("result", [])


def _normalize_command(text: str) -> tuple[str, list[str]]:
    parts = text.strip().split()
    if not parts:
        return "", []
    command = parts[0].split("@", 1)[0].lower()
    return command, parts[1:]


def _parse_group_arg(args: list[str]) -> str:
    if not args:
        return DEFAULT_GROUP
    if args[0] == "--group" and len(args) > 1:
        return args[1]
    return args[0]


def _is_authorized(chat_id: str) -> bool:
    return str(chat_id) == str(settings.telegram_chat_id)


def _handle_stock_command(args: list[str], chat_id: str) -> None:
    if not args:
        send_message("Format: /stock BBCA", chat_id=chat_id)
        return

    code = args[0].upper().replace(".JK", "")
    send_message(f"Menganalisa {code}, mohon tunggu...", chat_id=chat_id)

    from app.analyzer import analyze_stock
    from app.database import save_scan_results
    from app.report_generator import generate_text_report

    try:
        result = analyze_stock(code)
    except Exception as exc:
        send_message(f"Gagal menganalisa {code}: {exc}", chat_id=chat_id)
        return

    if not result:
        send_message(f"{code}: tidak ada hasil analisa.", chat_id=chat_id)
        return

    save_scan_results([result])
    send_message(generate_text_report([result]), chat_id=chat_id)


def _handle_scan_command(args: list[str], chat_id: str) -> None:
    try:
        group_name = validate_group(_parse_group_arg(args))
    except ValueError:
        send_message(GROUP_NOT_FOUND_MESSAGE, chat_id=chat_id)
        return

    send_message(
        f"Scan group {format_group_label(group_name)} sedang diproses. Ini bisa butuh beberapa menit.",
        chat_id=chat_id,
    )

    from app.analyzer import scan_all_stocks
    from app.database import save_scan_results
    from app.report_generator import save_text_report

    try:
        results = scan_all_stocks(group_name)
        saved_rows = save_scan_results(results)
        report_path = save_text_report(results, group_name=group_name)
        send_message(
            build_top_results_message(results, top_n=settings.top_n, group_name=group_name),
            chat_id=chat_id,
        )
        send_message(
            f"Scan selesai. {saved_rows} baris tersimpan ke SQLite.\n"
            f"Laporan TXT tersimpan di server: {report_path}",
            chat_id=chat_id,
        )
    except Exception as exc:
        send_message(f"Scan gagal: {exc}", chat_id=chat_id)


def _handle_export_command(args: list[str], chat_id: str) -> None:
    try:
        group_name = validate_group(_parse_group_arg(args))
    except ValueError:
        send_message(GROUP_NOT_FOUND_MESSAGE, chat_id=chat_id)
        return

    send_message(
        f"Export CSV group {format_group_label(group_name)} sedang diproses. Mohon tunggu...",
        chat_id=chat_id,
    )

    from app.analyzer import scan_all_stocks
    from app.database import save_scan_results
    from app.report_generator import export_csv, save_text_report

    try:
        results = scan_all_stocks(group_name)
        save_scan_results(results)
        save_text_report(results, group_name=group_name)
        csv_path = export_csv(results, group_name=group_name)
        send_message(
            build_top_results_message(results, top_n=settings.top_n, group_name=group_name),
            chat_id=chat_id,
        )
        send_document(
            str(csv_path),
            caption=f"Export screening {format_group_label(group_name)} {today_string()}",
            chat_id=chat_id,
        )
    except Exception as exc:
        send_message(f"Export gagal: {exc}", chat_id=chat_id)


def handle_telegram_message(message: dict) -> None:
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    text = str(message.get("text", "")).strip()
    if not chat_id or not text:
        return

    if not _is_authorized(chat_id):
        send_message("Akses ditolak. Chat ID ini tidak terdaftar di .env.", chat_id=chat_id)
        return

    command, args = _normalize_command(text)
    if command in {"/start", "/help"}:
        send_message(HELP_MESSAGE, chat_id=chat_id)
    elif command == "/status":
        send_message(
            f"Bot aktif dan siap menerima command.\nGroup tersedia: {len(get_available_groups())}",
            chat_id=chat_id,
        )
    elif command == "/groups":
        send_message(format_groups_list(), chat_id=chat_id)
    elif command == "/stock":
        _handle_stock_command(args, chat_id)
    elif command in {"/scan", "/send"}:
        _handle_scan_command(args, chat_id)
    elif command == "/export":
        _handle_export_command(args, chat_id)
    elif command == "/disclaimer":
        send_message(f"{DISCLAIMER}\n\nBatasan data: {DATA_LIMITATION}", chat_id=chat_id)
    else:
        send_message("Command tidak dikenal.\n\n" + HELP_MESSAGE, chat_id=chat_id)


def run_telegram_listener() -> None:
    if not is_configured():
        print("Telegram belum dikonfigurasi. Isi TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID di .env.")
        return

    ensure_directories()
    offset = _read_offset()
    print("Telegram command bot berjalan. Kirim /help dari Telegram. Tekan Ctrl+C untuk berhenti.")

    while True:
        try:
            updates = _get_updates(offset)
            for update in updates:
                update_id = int(update["update_id"])
                offset = update_id + 1
                _write_offset(offset)
                message = update.get("message")
                if message:
                    handle_telegram_message(message)
        except KeyboardInterrupt:
            print("Telegram command bot dihentikan.")
            break
        except Exception as exc:
            print(f"Telegram listener error: {exc}")
            time.sleep(5)
