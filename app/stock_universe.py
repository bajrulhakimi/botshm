from __future__ import annotations

import csv
import re
from pathlib import Path

from app.config import settings


GROUP_NOT_FOUND_MESSAGE = (
    "Group tidak ditemukan. Gunakan python main.py groups untuk melihat daftar group."
)

DEFAULT_GROUP = "all"
GROUPS_DIR = settings.data_dir / "groups"
GROUP_ORDER = [
    "all",
    "lq45",
    "idx30",
    "idx80",
    "kompas100",
    "jii",
    "high-dividend",
    "esg",
    "msci",
    "banking",
    "energy",
    "mining",
    "consumer",
    "telecom",
    "property",
    "technology",
]

INDEX_GROUPS = [
    "all",
    "lq45",
    "idx30",
    "idx80",
    "kompas100",
    "jii",
    "high-dividend",
    "esg",
    "msci",
]

SECTOR_GROUPS = [
    "banking",
    "energy",
    "mining",
    "consumer",
    "telecom",
    "property",
    "technology",
]


def normalize_symbol(symbol: str) -> str:
    clean_symbol = symbol.strip().upper().replace(".JK", "")
    return re.sub(r"[^A-Z0-9]", "", clean_symbol)


def normalize_group_name(group_name: str | None) -> str:
    return (group_name or DEFAULT_GROUP).strip().lower()


def format_group_label(group_name: str | None) -> str:
    normalized = normalize_group_name(group_name)
    labels = {
        "all": "All",
        "lq45": "LQ45",
        "idx30": "IDX30",
        "idx80": "IDX80",
        "kompas100": "Kompas100",
        "jii": "JII",
        "high-dividend": "IDX High Dividend 20",
        "esg": "IDX ESG Leaders",
        "msci": "MSCI Indonesia",
        "banking": "Banking",
        "energy": "Energy",
        "mining": "Mining",
        "consumer": "Consumer",
        "telecom": "Telecom",
        "property": "Property",
        "technology": "Technology",
    }
    return labels.get(normalized, normalized.upper())


def get_available_groups() -> list[str]:
    discovered = []
    if GROUPS_DIR.exists():
        discovered = sorted(path.stem.lower() for path in GROUPS_DIR.glob("*.csv"))

    ordered = [group for group in GROUP_ORDER if group == "all" or group in discovered]
    extra = [group for group in discovered if group not in ordered]
    return ordered + extra


def format_groups_list() -> str:
    available = set(get_available_groups())
    lines = ["AVAILABLE GROUPS", "", "[INDEKS / UNIVERSE]"]
    lines.extend(f"- {group}" for group in INDEX_GROUPS if group in available)
    lines.extend(["", "[SEKTOR]"])
    lines.extend(f"- {group}" for group in SECTOR_GROUPS if group in available)
    return "\n".join(lines)


def validate_group(group_name: str | None) -> str:
    normalized = normalize_group_name(group_name)
    if normalized == DEFAULT_GROUP:
        return normalized
    if normalized not in get_available_groups():
        raise ValueError(GROUP_NOT_FOUND_MESSAGE)
    return normalized


def _dedupe_symbols(symbols: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        normalized = normalize_symbol(symbol)
        if normalized and normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped


def load_all_symbols() -> list[str]:
    if not settings.stocks_csv.exists():
        raise FileNotFoundError(f"File daftar saham tidak ditemukan: {settings.stocks_csv}")

    symbols: list[str] = []
    with settings.stocks_csv.open("r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            if not row:
                continue
            symbol = normalize_symbol(row[0])
            if symbol and symbol != "SYMBOL" and symbol != "CODE":
                symbols.append(symbol)
    return _dedupe_symbols(symbols)


def _load_symbols_from_group_file(path: Path) -> list[str]:
    symbols: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as file:
        sample = file.read(2048)
        file.seek(0)
        try:
            has_header = csv.Sniffer().has_header(sample) if sample else False
        except csv.Error:
            has_header = sample.lower().startswith("symbol,")
        if has_header:
            reader = csv.DictReader(file)
            for row in reader:
                symbols.append(row.get("symbol", "") or row.get("code", ""))
        else:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    symbols.append(row[0])
    return _dedupe_symbols(symbols)


def load_group_symbols(group_name: str | None = DEFAULT_GROUP) -> list[str]:
    normalized = validate_group(group_name)
    if normalized == DEFAULT_GROUP:
        return load_all_symbols()

    path = GROUPS_DIR / f"{normalized}.csv"
    if not path.exists():
        raise ValueError(GROUP_NOT_FOUND_MESSAGE)

    symbols = _load_symbols_from_group_file(path)
    if not symbols:
        raise ValueError(f"Group {normalized} belum memiliki saham.")
    return symbols
