"""Canlı test haftaları için güncel KAP bildirimlerini indirir (MEL-94 haber bağlamı; yalnız yerel).

Model ve kayıtlı listeler değişmez. İlk canlı haftanın 35 gün öncesinden bugüne kadarki bildirimler
data/live/kap/kap.parquet dosyasına yazılır; `export_web.py --live` bunlardan listedeki hisselerin
son 30 gününü yerel siteye (dosyanın altındaki nota) aktarır.

Kullanım: python scripts/live_kap.py
"""

import csv
import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent))
from bistmd.ingest.kap_disclosures import HEADERS, fetch_range, to_frame  # noqa: E402
from bistmd.paths import ROOT  # noqa: E402

LIVE = ROOT / "data" / "live"
OUT = LIVE / "kap" / "kap.parquet"


def main() -> None:
    log = ROOT / "docs" / "canli_test" / "kayit.csv"
    weeks = sorted(r["hafta_sonu"] for r in csv.DictReader(open(log, encoding="utf-8")))
    if not weeks:
        sys.exit("Kayıtlı canlı hafta yok.")
    start = pd.Timestamp(weeks[0]) - pd.Timedelta(days=35)
    end = pd.Timestamp.today().normalize()
    s = requests.Session()
    s.headers.update(HEADERS)
    rows = []
    for w in pd.date_range(start, end, freq="7D"):
        rows.extend(fetch_range(w, min(w + pd.Timedelta(days=6), end), s, pause=2.0))
    df = to_frame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"{len(df):,} bildirim, {start:%Y-%m-%d} – {end:%Y-%m-%d} → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
