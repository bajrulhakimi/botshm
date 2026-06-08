from __future__ import annotations

import os
import time

import schedule

from app.analyzer import scan_all_stocks
from app.config import ensure_directories, settings
from app.database import save_scan_results
from app.report_generator import generate_text_report, save_text_report
from app.stock_universe import DEFAULT_GROUP
from app.telegram_bot import send_top_results


def _configure_timezone() -> None:
    os.environ["TZ"] = settings.timezone
    if hasattr(time, "tzset"):
        time.tzset()


def run_scan_and_send() -> None:
    ensure_directories()
    results = scan_all_stocks(DEFAULT_GROUP)
    save_scan_results(results)
    report_path = save_text_report(results, group_name=DEFAULT_GROUP)
    print(generate_text_report(results, group_name=DEFAULT_GROUP))
    print(f"Laporan tersimpan: {report_path}")
    send_top_results(results, top_n=settings.top_n, group_name=DEFAULT_GROUP)


def run_scheduler() -> None:
    _configure_timezone()
    ensure_directories()
    for day in (
        schedule.every().monday,
        schedule.every().tuesday,
        schedule.every().wednesday,
        schedule.every().thursday,
        schedule.every().friday,
    ):
        day.at(settings.scan_time).do(run_scan_and_send)

    print(
        f"Scheduler berjalan. Scan otomatis Senin-Jumat jam {settings.scan_time} "
        f"{settings.timezone}. Tekan Ctrl+C untuk berhenti."
    )
    while True:
        schedule.run_pending()
        time.sleep(30)
