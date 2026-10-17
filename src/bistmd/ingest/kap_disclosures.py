"""KAP bildirimlerinin üst verisini (yayın saati, konu, özet, hisse kodu) indirir.

API sorgu başına en fazla 2.000 kayıt döndürüyor (en yenileri) ve istek sınırı (429)
uyguluyor. Bu yüzden haftalık pencerelerle sorgulanır; sınıra ulaşan pencere ikiye
bölünür. 429 gelirse artan sürelerle beklenir. Sonuçlar ay bazında parquet
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


def _body(start: str, end: str) -> dict:
    return {"fromDate": start, "toDate": end, "memberType": "IGS", "mkkMemberOidList": [],
            "inactiveMkkMemberOidList": [], "disclosureClass": "", "subjectList": [], "isLate": "",
            "mainSector": "", "sector": "", "subSector": "", "marketOid": "", "index": "", "bdkReview": "",
            "bdkMemberOidList": [], "year": "", "term": "", "ruleType": "", "period": "",
            "fromSrc": False, "srcCategory": "", "discIndex": []}


def _post(start: pd.Timestamp, end: pd.Timestamp, session: requests.Session,
          pause: float, retries: int = 6) -> list[dict]:
    """Tek sorgu. 429 (istek sınırı) gelirse 60s, 120s, 240s... bekleyip tekrar dener."""
    for attempt in range(retries):
        time.sleep(pause)
        try:
            resp = session.post(URL, json=_body(f"{start:%Y-%m-%d}", f"{end:%Y-%m-%d}"), timeout=120)
            if resp.status_code == 429:
                raise requests.HTTPError("429", response=resp)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            if attempt == retries - 1:
                raise
            wait = 60 * 2 ** attempt if "429" in str(exc) else 10 * (attempt + 1)
            print(f"  {start:%Y-%m-%d}..{end:%Y-%m-%d}: {exc.__class__.__name__} {exc}, {wait}s bekleniyor")
            time.sleep(wait)
    return []


def fetch_range(start: pd.Timestamp, end: pd.Timestamp, session: requests.Session,
                pause: float = 2.0) -> list[dict]:
    """Aralığı tek sorguyla çeker; sonuç 2.000 sınırına ulaşırsa ikiye bölüp tekrar dener."""
    rows = _post(start, end, session, pause)
    if len(rows) < LIMIT:
        return rows
    if start == end:
        print(f"UYARI: {start:%Y-%m-%d} günü {LIMIT} kayıt sınırına ulaştı, eksik olabilir")
        return rows
    mid = start + (end - start) // 2
    mid = mid.normalize()
    return fetch_range(start, mid, session, pause) + fetch_range(mid + pd.Timedelta(days=1), end, session, pause)


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


def download(start: str, end: str, refresh: bool = False, pause: float = 2.0) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    current_month = pd.Timestamp.today().strftime("%Y-%m")
    for month in pd.period_range(start, end, freq="M"):
        path = OUT_DIR / f"{month}.parquet"
        # İçinde bulunulan ay her zaman yeniden çekilir
        if path.exists() and not refresh and str(month) != current_month:
            continue
        m_start = max(month.start_time, pd.Timestamp(start))
        m_end = min(month.end_time.normalize(), pd.Timestamp(end))
        rows: list[dict] = []
        # Haftalık pencereler; yoğun haftalar fetch_range içinde bölünür
        for w_start in pd.date_range(m_start, m_end, freq="7D"):
            w_end = min(w_start + pd.Timedelta(days=6), m_end)
            rows.extend(fetch_range(w_start, w_end, session, pause))
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
