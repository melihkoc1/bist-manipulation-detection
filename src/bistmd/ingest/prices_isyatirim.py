"""İş Yatırım'dan günlük hisse verisi indirir.

Avantajı: işlemden kalkmış hisseleri de içerir (hayatta kalma yanlılığını azaltır) ve
aynı yanıtta piyasa değeri, halka açık piyasa değeri, sermaye, XU100 ve USD kuru gelir.
Eksikleri: açılış fiyatı ve lot bazında hacim yok (hacim TL cinsinden).
Kod değiştiren hisseler güncel koduyla tutulur (ör. KOZAL → TRALT).

Kullanım:
    python -m bistmd.ingest.prices_isyatirim FORMT ANELT THYAO
"""

import argparse
import time

import pandas as pd
import requests

from bistmd.paths import RAW

URL = "https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/HisseTekil"
OUT_DIR = RAW / "prices_isyatirim"
HEADERS = {"User-Agent": "Mozilla/5.0 (bistmd-research/0.1; university thesis project)"}

COLUMNS = {
    "HGDG_HS_KODU": "ticker",
    "HGDG_TARIH": "date",
    "HGDG_KAPANIS": "close",       # düzeltilmiş kapanış
    "HGDG_AOF": "vwap",            # ağırlıklı ortalama fiyat
    "HGDG_MIN": "low",
    "HGDG_MAX": "high",
    "HGDG_HACIM": "value_try",     # işlem hacmi (TL)
    "HG_KAPANIS": "close_raw",     # düzeltilmemiş kapanış (tavan/taban tespiti için)
    "HG_MIN": "low_raw",
    "HG_MAX": "high_raw",
    "SERMAYE": "capital",
    "PD": "mcap_try",
    "HAO_PD": "float_mcap_try",
    "END_DEGER": "xu100",
    "DD_DEGER": "usdtry",
}


def fetch(ticker: str, start: str = "01-01-2010", end: str | None = None,
          session: requests.Session | None = None) -> pd.DataFrame:
    end = end or pd.Timestamp.today().strftime("%d-%m-%Y")
    s = session or requests.Session()
    resp = s.get(URL, params={"hisse": ticker, "startdate": start, "enddate": end},
                 headers=HEADERS, timeout=120)
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("ok"):
        raise RuntimeError(f"{ticker}: {payload.get('errorDescription')}")
    df = pd.DataFrame(payload["value"])
    if df.empty:
        return pd.DataFrame(columns=list(COLUMNS.values()))
    df = df[[c for c in COLUMNS if c in df.columns]].rename(columns=COLUMNS)
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    df["free_float"] = df["float_mcap_try"] / df["mcap_try"]
    return df.sort_values("date").reset_index(drop=True)


def download(tickers: list[str], refresh: bool = False, pause: float = 1.0) -> dict[str, int]:
    """Her hisse için data/raw/prices_isyatirim/<KOD>.parquet yazar; {kod: satır sayısı} döndürür."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    counts: dict[str, int] = {}
    for t in tickers:
        path = OUT_DIR / f"{t}.parquet"
        if path.exists() and not refresh:
            counts[t] = len(pd.read_parquet(path))
            continue
        try:
            df = fetch(t, session=session)
        except Exception as exc:
            print(f"UYARI: {t} indirilemedi: {exc}")
            continue
        df.to_parquet(path, index=False)
        counts[t] = len(df)
        print(f"{t}: {len(df)} gün" + (f" ({df.date.min():%Y-%m-%d} → {df.date.max():%Y-%m-%d})" if len(df) else ""))
        time.sleep(pause)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    download([t.upper() for t in args.tickers], args.refresh)


if __name__ == "__main__":
    main()
