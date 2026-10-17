"""KAP bildirimlerinin üst verisini (yayın saati, konu, özet, hisse kodu) indirir.

API sorgu başına en fazla 2.000 kayıt döndürüyor (en yenileri); bu yüzden gün gün
sorgulanır. Bir gün sınıra ulaşırsa uyarı verilir. Sonuçlar ay bazında parquet
dosyalarına yazılır: data/raw/kap_disclosures/YYYY-MM.parquet

Kullanım:
    python -m bistmd.ingest.kap_disclosures --start 2010-01-01 --end 2026-10-16
"""

import argparse
import time

import pandas as pd
import requests

from bistmd.paths import RAW

URL = "https://www.kap.org.tr/tr/api/disclosure/members/byCriteria"
OUT_DIR = RAW / "kap_disclosures"
HEADERS = {"User-Agent": "Mozilla/5.0 (bistmd-research/0.1; university thesis project)", "Accept-Language": "tr"}
LIMIT = 2000

FIELDS = {
    "disclosureIndex": "disclosure_id",
    "publishDate": "published_at",
    "stockCodes": "tickers",
    "kapTitle": "company",
    "disclosureClass": "disclosure_class",   # ODA: özel durum, FR: finansal rapor, DG: diğer, DKB: düzenleyici kurum
    "disclosureType": "disclosure_type",
    "disclosureCategory": "disclosure_category",
    "subject": "subject",
    "summary": "summary",
    "isLate": "is_late",
    "relatedStocks": "related_stocks",
}


def _body(day: str) -> dict:
    return {"fromDate": day, "toDate": day, "memberType": "IGS", "mkkMemberOidList": [],
            "inactiveMkkMemberOidList": [], "disclosureClass": "", "subjectList": [], "isLate": "",
            "mainSector": "", "sector": "", "subSector": "", "marketOid": "", "index": "", "bdkReview": "",
            "bdkMemberOidList": [], "year": "", "term": "", "ruleType": "", "period": "",
            "fromSrc": False, "srcCategory": "", "discIndex": []}


def fetch_day(day: pd.Timestamp, session: requests.Session, retries: int = 3) -> list[dict]:
    for attempt in range(retries):
        try:
            resp = session.post(URL, json=_body(day.strftime("%Y-%m-%d")), timeout=120)
            resp.raise_for_status()
            rows = resp.json()
            if len(rows) >= LIMIT:
                print(f"UYARI: {day:%Y-%m-%d} günü {LIMIT} kayıt sınırına ulaştı, eksik olabilir")
            return rows
        except (requests.RequestException, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    return []


def to_frame(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=list(FIELDS.values()))
    df = df[[c for c in FIELDS if c in df.columns]].rename(columns=FIELDS)
    df["published_at"] = pd.to_datetime(df["published_at"], format="%d.%m.%Y %H:%M:%S")
    for col in ("related_stocks",):
        if col in df.columns:
            df[col] = df[col].astype("string")
    return df.drop_duplicates("disclosure_id")


def download(start: str, end: str, refresh: bool = False, pause: float = 0.3) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    current_month = pd.Timestamp.today().strftime("%Y-%m")
    for month in pd.period_range(start, end, freq="M"):
        path = OUT_DIR / f"{month}.parquet"
        # İçinde bulunulan ay her zaman yeniden çekilir
        if path.exists() and not refresh and str(month) != current_month:
            continue
        days = pd.date_range(max(month.start_time, pd.Timestamp(start)),
                             min(month.end_time.normalize(), pd.Timestamp(end)), freq="D")
        rows: list[dict] = []
        for day in days:
            rows.extend(fetch_day(day, session))
            time.sleep(pause)
        df = to_frame(rows)
        df.to_parquet(path, index=False)
        print(f"{month}: {len(df)} bildirim")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    download(args.start, args.end, args.refresh)


if __name__ == "__main__":
    main()
