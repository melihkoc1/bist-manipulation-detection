"""KAP'tan güncel BIST şirket listesini (kod + unvan) indirir.

Not: Liste yalnızca bugün işlem gören şirketleri içerir. İşlemden kalkmış hisseler
SPK kararlarından ve İş Yatırım fiyat verisinden ayrıca tespit edilir.
"""

import json
import re

import pandas as pd
import requests

from bistmd.paths import RAW

URL = "https://www.kap.org.tr/tr/bist-sirketler"
OUT = RAW / "universe" / "kap_bist.parquet"
HEADERS = {"User-Agent": "Mozilla/5.0 (bistmd-research/0.1; university thesis project)"}

_RECORD = re.compile(r'\{"mkkMemberOid":"[^"]*","kapMemberTitle":"[^"]*",[^{}]*?"stockCode":"[^"]*"[^{}]*\}')


def fetch() -> pd.DataFrame:
    html = requests.get(URL, headers=HEADERS, timeout=120).text.replace('\\"', '"')
    rows = []
    for raw in _RECORD.findall(html):
        rec = json.loads(raw)
        # Bazı şirketlerin birden fazla kodu var: "GARAN, TGB"
        for code in (c.strip() for c in rec["stockCode"].split(",")):
            if code:
                rows.append({"ticker": code, "title": rec["kapMemberTitle"], "mkk_oid": rec["mkkMemberOid"]})
    return pd.DataFrame(rows).drop_duplicates("ticker").sort_values("ticker").reset_index(drop=True)


def load(refresh: bool = False) -> pd.DataFrame:
    if OUT.exists() and not refresh:
        return pd.read_parquet(OUT)
    df = fetch()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    return df


if __name__ == "__main__":
    df = load(refresh=True)
    print(f"{len(df)} kod, {df.mkk_oid.nunique()} şirket")
