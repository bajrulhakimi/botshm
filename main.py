from __future__ import annotations

import argparse
import sys


def command_scan() -> int:
    from app.analyzer import scan_all_stocks
    from app.config import ensure_directories
    from app.database import save_scan_results
    from app.report_generator import generate_text_report, save_text_report

    ensure_directories()
    results = scan_all_stocks()
    saved_rows = save_scan_results(results)
    report_path = save_text_report(results)
    print(generate_text_report(results))
    print(f"Laporan tersimpan: {report_path}")
    print(f"Data SQLite tersimpan: {saved_rows} baris")
    return 0


def command_send() -> int:
    from app.analyzer import scan_all_stocks
    from app.config import ensure_directories, settings
    from app.database import save_scan_results
    from app.report_generator import generate_text_report, save_text_report
    from app.telegram_bot import send_top_results

    ensure_directories()
    results = scan_all_stocks()
    saved_rows = save_scan_results(results)
    report_path = save_text_report(results)
    print(generate_text_report(results, top_n=settings.top_n))
    print(f"Laporan tersimpan: {report_path}")
    print(f"Data SQLite tersimpan: {saved_rows} baris")
    if send_top_results(results, top_n=settings.top_n):
        print("Laporan top saham berhasil dikirim ke Telegram.")
    else:
        print("Laporan top saham belum terkirim ke Telegram.")
    return 0


def command_stock(code: str) -> int:
    from app.analyzer import analyze_stock
    from app.config import ensure_directories
    from app.database import save_scan_results
    from app.report_generator import generate_text_report

    ensure_directories()
    try:
        result = analyze_stock(code)
    except Exception as exc:
        print(f"Gagal menganalisa {code}: {exc}")
        return 1

    if not result:
        print(f"{code.upper()}: tidak ada hasil analisa.")
        return 1

    save_scan_results([result])
    print(generate_text_report([result]))
    return 0


def command_export() -> int:
    from app.analyzer import scan_all_stocks
    from app.config import ensure_directories, settings
    from app.database import save_scan_results
    from app.report_generator import export_csv, generate_text_report, save_text_report

    ensure_directories()
    results = scan_all_stocks()
    saved_rows = save_scan_results(results)
    report_path = save_text_report(results)
    csv_path = export_csv(results)
    print(generate_text_report(results, top_n=settings.top_n))
    print(f"Laporan tersimpan: {report_path}")
    print(f"CSV tersimpan: {csv_path}")
    print(f"Data SQLite tersimpan: {saved_rows} baris")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="BOT ANALISA SAHAM IDX GRATIS berbasis data Yahoo Finance/yfinance.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("scan", help="Scan semua saham dan tampilkan hasil di terminal.")
    subparsers.add_parser("send", help="Scan semua saham lalu kirim top saham ke Telegram.")

    stock_parser = subparsers.add_parser("stock", help="Analisa satu saham tertentu.")
    stock_parser.add_argument("code", help="Kode saham IDX, contoh: BBCA")

    subparsers.add_parser("export", help="Scan semua saham lalu export hasil ke CSV.")
    subparsers.add_parser("schedule", help="Jalankan scheduler internal Python.")
    subparsers.add_parser("telegram", help="Jalankan bot command Telegram.")
    subparsers.add_parser("test-telegram", help="Tes pengiriman pesan Telegram.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "scan":
            return command_scan()
        if args.command == "send":
            return command_send()
        if args.command == "stock":
            return command_stock(args.code)
        if args.command == "export":
            return command_export()
        if args.command == "schedule":
            from app.scheduler import run_scheduler

            run_scheduler()
            return 0
        if args.command == "telegram":
            from app.telegram_bot import run_telegram_listener

            run_telegram_listener()
            return 0
        if args.command == "test-telegram":
            from app.telegram_bot import test_telegram

            if test_telegram():
                print("Test Telegram berhasil dikirim.")
            else:
                print("Test Telegram belum terkirim.")
            return 0
    except ModuleNotFoundError as exc:
        print(f"Dependensi belum terinstall: {exc.name}")
        print("Jalankan: python -m pip install -r requirements.txt")
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
