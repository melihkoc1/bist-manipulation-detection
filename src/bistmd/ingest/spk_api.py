"""SPK İdari Yaptırımlar API'sinden (idariyaptirimlar.spk.gov.tr) ham kayıtları indirir.

Not: İşlem yasağı uç noktası yalnızca güncel/yakın tarihli yasakları döndürüyor
(2024 öncesi boş). Eski işlem yasakları için SPK bültenleri ayrıca taranmalı.

Kullanım:
    python -m bistmd.ingest.spk_api --start 2013 --end 2026
"""

import argparse
import json
import time

import requests

from bistmd.paths import RAW

BASE_URL = "https://idariyaptirimlar.spk.gov.tr/api/"
ENDPOINTS = {
    "islem_yasagi": "IslemYasagi/Filtre",
    "idari_para_cezasi": "IdariParaCezasi/Filtre",
}
OUT_DIR = RAW / "spk_api"
HEADERS = {"User-Agent": "bistmd-research/0.1 (university thesis project)"}


def fetch_year(endpoint: str, year: int, session: requests.Session) -> list[dict]:
    resp = session.get(BASE_URL + endpoint, params={"kurulKararYili": year}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def download(start: int, end: int, refresh: bool = False, pause: float = 1.0) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    for name, endpoint in ENDPOINTS.items():
        for year in range(start, end + 1):
            path = OUT_DIR / f"{name}_{year}.json"
            # Güncel yıl her zaman yeniden çekilir; geçmiş yıllar önbellekten okunur.
            if path.exists() and not refresh and year < end:
                continue
            records = fetch_year(endpoint, year, session)
            path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
            print(f"{name} {year}: {len(records)} kayıt")
            time.sleep(pause)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=2013)
    parser.add_argument("--end", type=int, default=2026)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    download(args.start, args.end, args.refresh)


if __name__ == "__main__":
    main()
