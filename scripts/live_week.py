"""Canlı test (MEL-17): bir haftanın şüpheli listesini donmuş modelle üretip kayda geçirir.

Adımlar:
1. İş Yatırım'dan son ~15 ayın fiyatları indirilir (son 30 günde işlem görmüş hisseler + KAP'ın
   güncel listesindeki yeni hisseler). Araştırma verisine (data/raw) dokunulmaz; anlık görüntü
   data/live/prices/<hafta>.parquet olarak saklanır.
2. Fiyat göstergeleri araştırmadaki kodla (bistmd.features.price) hesaplanır.
3. Hafta, donmuş Kural + PU ile skorlanır (ana değerlendirmedeki haftalık yüzdelik birleşimi).
4. Tam liste data/live/weeks/<hafta>.parquet, ilk 20 data/live/weeks/<hafta>_ilk20.csv olarak yazılır.
   İlk 20 dosyasının sha256 parmak izi docs/canli_test/kayit.csv'ye eklenir (hisse adı yok).
   Kaydedilmiş bir hafta yeniden yazılmaz.

Kullanım:
    python scripts/live_week.py                 # son tamamlanan hafta
    python scripts/live_week.py --week 2026-11-13
    python scripts/live_week.py --verify        # kayıtlı ilk 20 dosyalarının parmak izlerini denetler
"""

import argparse
import csv
import hashlib
import json
import pickle
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from ensemble_v2 import combine  # noqa: E402

from bistmd.eval.weekly import to_weekly  # noqa: E402
from bistmd.features import price as price_features  # noqa: E402
from bistmd.ingest import prices_isyatirim, universe  # noqa: E402
from bistmd.models.core import RuleScore  # noqa: E402
from bistmd.paths import INTERIM, RAW  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LIVE = INTERIM.parent / "live"
MODEL_PATH = LIVE / "model" / "pu_bagging.pkl"
MANIFEST = ROOT / "docs" / "canli_test" / "model.json"
LOG = ROOT / "docs" / "canli_test" / "kayit.csv"
TOP = 20
HISTORY = pd.DateOffset(months=15)  # 60 günlük pencereler + 60 günlük referanslar için yeterli
LOG_COLS = ["hafta_sonu", "kayit_zamani_utc", "gecikmeli", "veri_son_gun", "n_hisse",
            "sha256_ilk20", "model_sha256"]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def last_complete_friday(today: pd.Timestamp) -> pd.Timestamp:
    """Bugünden önceki en yakın cuma (bugün cumaysa bir önceki; seans akşamı kapanmamış olabilir)."""
    back = (today.weekday() - 4) % 7 or 7
    return (today - pd.Timedelta(days=back)).normalize()


def fetch_prices(week_end: pd.Timestamp, pause: float) -> pd.DataFrame:
    start = week_end - HISTORY
    recent = []
    for p in sorted((RAW / "prices_isyatirim").glob("*.parquet")):
        d = pd.read_parquet(p, columns=["date"])["date"]
        if len(d) and d.max() >= pd.Timestamp("2026-09-01"):
            recent.append(p.stem)
    uni = universe.load(refresh=True)["ticker"].tolist()
    tickers = sorted(set(recent) | set(uni))
    session = __import__("requests").Session()
    parts, failed = [], []
    for i, t in enumerate(tickers):
        try:
            df = prices_isyatirim.fetch(t, start=f"{start:%d-%m-%Y}", end=f"{week_end:%d-%m-%Y}", session=session)
            if len(df):
                parts.append(df.assign(ticker=t))
        except Exception as exc:  # noqa: BLE001 — tek hisse hatası listeyi durdurmasın
            failed.append(t)
            print(f"  UYARI {t}: {exc}")
        if i % 100 == 0:
            print(f"  fiyat {i}/{len(tickers)}", flush=True)
        time.sleep(pause)
    print(f"fiyat: {len(parts)} hisse, {len(failed)} hata")
    return pd.concat(parts, ignore_index=True)


def score_week(prices: pd.DataFrame, week_end: pd.Timestamp) -> pd.DataFrame:
    feats = price_features.build(prices)
    week_start = week_end - pd.Timedelta(days=6)
    X = feats[feats["date"].between(week_start, week_end)].reset_index(drop=True)
    with open(MODEL_PATH, "rb") as fh:
        pu = pickle.load(fh)
    rule = X[["ticker", "date"]].assign(score=RuleScore().score(X).to_numpy())
    pux = X[["ticker", "date"]].assign(score=pu.score(X))
    out = combine([to_weekly(rule), to_weekly(pux)])
    out["week"] = out["week"].astype(str)
    return out.sort_values("rank").reset_index(drop=True)


def top_csv(wk: pd.DataFrame) -> bytes:
    t = wk.head(TOP)
    lines = ["sira,hisse,skor"] + [f"{int(r)},{tk},{s:.6f}" for r, tk, s in zip(t["rank"], t["ticker"], t["score"])]
    return ("\n".join(lines) + "\n").encode("utf-8")


def read_log() -> list[dict]:
    if not LOG.exists():
        return []
    with open(LOG, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def verify() -> None:
    rows = read_log()
    bad = 0
    for r in rows:
        p = LIVE / "weeks" / f"{r['hafta_sonu']}_ilk20.csv"
        ok = p.exists() and sha256_bytes(p.read_bytes()) == r["sha256_ilk20"]
        bad += not ok
        print(f"{r['hafta_sonu']}: {'tamam' if ok else 'UYUŞMUYOR / dosya yok'}")
    model_ok = sha256_bytes(MODEL_PATH.read_bytes()) == json.loads(MANIFEST.read_text(encoding="utf-8"))["model_sha256"]
    print(f"model: {'tamam' if model_ok else 'UYUŞMUYOR'}; {len(rows)} hafta, {bad} sorun")
    sys.exit(1 if bad or not model_ok else 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", help="haftanın cuma tarihi (YYYY-AA-GG)")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--pause", type=float, default=0.3)
    args = ap.parse_args()
    if args.verify:
        return verify()

    now = pd.Timestamp.now(tz="Europe/Istanbul").tz_localize(None)
    week_end = pd.Timestamp(args.week) if args.week else last_complete_friday(now.normalize())
    if week_end.weekday() != 4:
        sys.exit("--week bir cuma olmalı")
    if now < week_end + pd.Timedelta(hours=19):
        sys.exit("Hafta henüz kapanmadı.")
    if any(r["hafta_sonu"] == f"{week_end:%Y-%m-%d}" for r in read_log()):
        sys.exit(f"{week_end:%Y-%m-%d} zaten kayıtlı; kayıtlar değiştirilmez.")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256_bytes(MODEL_PATH.read_bytes()) != manifest["model_sha256"]:
        sys.exit("Donmuş model dosyası manifestle uyuşmuyor.")

    t0 = time.time()
    prices = fetch_prices(week_end, args.pause)
    prices = prices[prices["close"].notna()]
    snap = LIVE / "prices" / f"{week_end:%Y-%m-%d}.parquet"
    snap.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(snap, index=False)
    data_end = prices["date"].max()
    if data_end < week_end - pd.Timedelta(days=4):
        sys.exit(f"Fiyat verisi haftayı kapsamıyor (son gün {data_end:%Y-%m-%d}).")

    wk = score_week(prices, week_end)
    out = LIVE / "weeks"
    out.mkdir(parents=True, exist_ok=True)
    wk.to_parquet(out / f"{week_end:%Y-%m-%d}.parquet", index=False)
    top = top_csv(wk)
    (out / f"{week_end:%Y-%m-%d}_ilk20.csv").write_bytes(top)

    late = now > week_end + pd.Timedelta(days=3)  # pazartesi sonrası kayıt
    row = {"hafta_sonu": f"{week_end:%Y-%m-%d}",
           "kayit_zamani_utc": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
           "gecikmeli": int(late), "veri_son_gun": f"{data_end:%Y-%m-%d}", "n_hisse": int(wk["n_week"].iloc[0]),
           "sha256_ilk20": sha256_bytes(top), "model_sha256": manifest["model_sha256"][:16]}
    new = not LOG.exists()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LOG_COLS, lineterminator="\n")
        if new:
            w.writeheader()
        w.writerow(row)
    print(f"{row['hafta_sonu']}: {row['n_hisse']} hisse skorlandı, ilk 20 parmak izi {row['sha256_ilk20'][:12]}… "
          f"({time.time() - t0:.0f}s). Depoya kaydetmek için docs/canli_test/kayit.csv'yi commit edin.")


if __name__ == "__main__":
    main()
