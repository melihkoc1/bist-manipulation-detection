"""Model girdisi: hisse × gün özellik ve etiket tablosu.

Önkoşul: python -m bistmd.db  (prices, kap_disclosures, spk_cases tabloları)
Kullanım: python scripts/build_features.py [--start 2012-01-01]
Çıktı:    data/interim/features.parquet, data/interim/labels.parquet
"""

import argparse
import time

import duckdb
import pandas as pd

from bistmd.features import kap as kap_features
from bistmd.features import price as price_features
from bistmd.labels import windows
from bistmd.paths import DB_PATH, INTERIM


def main() -> None:
    parser = argparse.ArgumentParser()
    # Özellik pencereleri 60 güne kadar geri baktığı için fiyatlar daha erken yüklenir
    parser.add_argument("--start", default="2012-01-01")
    args = parser.parse_args()
    start = pd.Timestamp(args.start)
    t0 = time.time()

    con = duckdb.connect(str(DB_PATH), read_only=True)
    prices = con.execute("SELECT * FROM prices WHERE date >= ?", [start - pd.DateOffset(months=6)]).df()
    kap = con.execute("SELECT ticker, effective_date, subject FROM kap_disclosures").df()
    cases = con.execute("SELECT * FROM spk_cases").df()
    con.close()
    print(f"yüklendi: {prices.ticker.nunique()} hisse, {len(prices):,} satır, {len(kap):,} KAP satırı "
          f"({time.time() - t0:.0f}s)")

    feats = price_features.build(prices)
    feats = kap_features.build(feats, kap)
    feats = feats[feats["date"] >= start].reset_index(drop=True)
    print(f"özellikler: {feats.shape[1] - 2} sütun, {len(feats):,} satır ({time.time() - t0:.0f}s)")

    labels = windows.build(feats[["ticker", "date"]], cases)
    INTERIM.mkdir(parents=True, exist_ok=True)
    feats.to_parquet(INTERIM / "features.parquet", index=False)
    labels.to_parquet(INTERIM / "labels.parquet", index=False)

    summary = labels.groupby(labels["date"].dt.year)[["pos_exact", "pos_3m", "pos_6m", "pos_12m"]].sum()
    print("Yıllara göre pozitif hisse-gün sayısı:")
    print(summary.to_string())
    print(f"bitti ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
