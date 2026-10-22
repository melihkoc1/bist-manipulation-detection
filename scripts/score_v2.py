"""Değerlendirme v2: modellerin 2017–2026 haftalık skorlarını üretip kaydeder.

Modlar:
  honest  Dürüst yıllık yeniden eğitim. Y yılı, ≤ Y−1 verisiyle ve Y−1 sonuna kadar SPK'nın
          AÇIKLADIĞI vakalarla eğitilen modelle skorlanır (gerçek kullanım senaryosu).
  loyo    Yıl dışarıda bırakma (hindsight). Y yılı, diğer tüm yılların tüm etiketleriyle
          eğitilen modelle skorlanır; Y yılına değen vakaların tüm satırları ve Y'nin ±90 günü
          eğitimden çıkarılır. Soru: "özellikler sinyal taşıyor mu?" (etiket azlığından bağımsız).

Her hafta, cumasının düştüğü yılın modeliyle skorlanır (yıl sınırında skorlar karışmaz).
Profil özellikleri (hisse kimliği) her zaman çıkarılır.

Kullanım:
    python scripts/score_v2.py --mode honest [--models 2_lightgbm,...] [--kap-set none|nonews|all]
                               [--no-vwap] [--out-dir scores_v2]
Çıktı: data/interim/{out-dir}/{mode}_{kap}_{model}.parquet (hafta × hisse)
--no-vwap: kapanış/VWAP özellikleri çıkarılır (katkılarını ayrı ölçmek için)
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from run_experiment import NONEWS, PROFILE, load, training_target  # noqa: E402

from bistmd.eval.weekly import to_weekly  # noqa: E402
from bistmd.labels.windows import case_windows  # noqa: E402
from bistmd.models.core import ALL_MODELS  # noqa: E402
from bistmd.paths import INTERIM  # noqa: E402

WINDOW = 6
YEARS = range(2012, 2027)  # özellikler 2010-04'ten; ilk dürüst model 2010–2011 verisiyle
PURGE = pd.Timedelta(days=90)
UNTRAINED = {"0a_kural", "0c_kural_vwap", "0b_basit"}
VWAP = ("close_vs_vwap", "close_above_vwap")


def prepare(df: pd.DataFrame, kap_set: str, no_vwap: bool = False) -> pd.DataFrame:
    df = df.drop(columns=PROFILE)
    if no_vwap:
        df = df.drop(columns=[c for c in df.columns if c.startswith(VWAP)])
    if kap_set != "all":
        kap_cols = [c for c in df.columns if c.startswith(("n_", "no_news", "days_since_")) or c == "ret_20_z_per_news"]
        keep = {"none": set(), "nonews": NONEWS}[kap_set]
        df = df.drop(columns=[c for c in kap_cols if c not in keep])
    return df


def rounds(df: pd.DataFrame, cases: pd.DataFrame, mode: str):
    week_year = df["date"].dt.to_period("W-FRI").dt.end_time.dt.year
    not_ignored = df[f"ignore_{WINDOW}m"].fillna(0) == 0
    windows = case_windows(cases, WINDOW)
    for yr in YEARS:
        score_mask = week_year == yr
        if mode == "honest":
            cutoff = pd.Timestamp(f"{yr - 1}-12-31")
            y = training_target(df, cases, WINDOW, False, cutoff)
            train = (df["date"] <= cutoff) & not_ignored
        else:
            y = df[f"pos_{WINDOW}m"].fillna(0).astype(int)
            lo, hi = pd.Timestamp(f"{yr}-01-01") - PURGE, pd.Timestamp(f"{yr}-12-31") + PURGE
            touching = set(windows.loc[(windows["start"] <= hi) & (windows["end"] >= lo), "case_id"])
            train = not_ignored & ~df["date"].between(lo, hi) & ~df[f"case_{WINDOW}m"].isin(touching)
        yield yr, train, y, score_mask


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("honest", "loyo"), default="honest")
    ap.add_argument("--models", default="")
    ap.add_argument("--kap-set", choices=("none", "nonews", "all"), default="none")
    ap.add_argument("--no-vwap", action="store_true")
    ap.add_argument("--out-dir", default="scores_v2")
    args = ap.parse_args()
    out = INTERIM / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    df, cases = load(WINDOW)
    df = prepare(df, args.kap_set, args.no_vwap)
    in_eval = df["date"].dt.to_period("W-FRI").dt.end_time.dt.year.between(min(YEARS), max(YEARS))
    wanted = [m for m in args.models.split(",") if m] or [c.name for c in ALL_MODELS] + ["random"]

    for name in wanted:
        path = out / f"{args.mode}_{args.kap_set}_{name}.parquet"
        t0 = time.time()
        base = df.loc[in_eval, ["ticker", "date"]].copy()
        if name == "random":
            base["score"] = np.random.default_rng(0).random(len(base))
            daily = base
        elif name in UNTRAINED:
            cls = next(c for c in ALL_MODELS if c.name == name)
            base["score"] = cls().score(df.loc[in_eval])
            daily = base
        else:
            cls = next(c for c in ALL_MODELS if c.name == name)
            parts = []
            for yr, train, y, score_mask in rounds(df, cases, args.mode):
                model = cls().fit(df.loc[train], y[train])
                s = df.loc[score_mask, ["ticker", "date"]].copy()
                s["score"] = model.score(df.loc[score_mask])
                parts.append(s)
                print(f"  {name} {yr}: eğitim {int(train.sum()):,} satır, pozitif {int(y[train].sum()):,} "
                      f"({time.time() - t0:.0f}s)", flush=True)
            daily = pd.concat(parts)
        wk = to_weekly(daily)
        wk["week"] = wk["week"].astype(str)
        wk.to_parquet(path, index=False)
        print(f"{name}: {len(wk):,} hisse-hafta → {path.name} ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
