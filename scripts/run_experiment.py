"""Modelleri eğitir ve zaman bölmelerinde olay bazlı metriklerle karşılaştırır.

Önkoşul: python scripts/build_features.py
Kullanım:
    python scripts/run_experiment.py [--window 6] [--models 0a_kural,2_lightgbm] [--hindsight]

--window     Dönemi bilinmeyen vakalar için karar öncesi pencere (3/6/12 ay)
--hindsight  Eğitimde sonradan açıklanan kararları da kullan. Varsayılan (dürüst mod):
             yalnızca eğitim döneminin sonuna kadar SPK'nın açıkladığı vakalar pozitiftir.
Çıktı: data/interim/results/results_w{window}.parquet ve docs/sonuclar_w{window}.md
"""

import argparse
import time

import duckdb
import numpy as np
import pandas as pd

from bistmd.eval import metrics
from bistmd.labels.windows import case_windows
from bistmd.models.core import ALL_MODELS
from bistmd.paths import DB_PATH, INTERIM, ROOT

KS = (10, 20, 50)
# Hissenin kimliğini taşıyan, zaman içinde yavaş değişen özellikler (bkz. özellik önem analizi)
PROFILE = ["free_float", "log_mcap_usd", "amihud_60"]
EVAL_SPLITS = ("val", "test", "forward")


def load(window: int):
    feats = pd.read_parquet(INTERIM / "features.parquet")
    labels = pd.read_parquet(INTERIM / "labels.parquet")
    con = duckdb.connect(str(DB_PATH), read_only=True)
    cases = con.execute("SELECT * FROM spk_cases").df()
    con.close()
    df = feats.merge(labels[["ticker", "date", f"pos_{window}m", f"ignore_{window}m", f"case_{window}m"]],
                     on=["ticker", "date"], how="left")
    df["split"] = metrics.split_of(df["date"])
    return df, cases


def training_target(df: pd.DataFrame, cases: pd.DataFrame, window: int, hindsight: bool) -> pd.Series:
    y = df[f"pos_{window}m"].fillna(0).astype(int)
    if not hindsight:
        cutoff = pd.Timestamp(metrics.SPLITS["train"][1])
        known = set(cases.loc[cases["first_decision"] <= cutoff, "case_id"])
        y = y.where(df[f"case_{window}m"].isin(known), 0)
    return y


def eval_cases(cases: pd.DataFrame, window: int, split: str) -> pd.DataFrame:
    w = case_windows(cases, window)
    w = w[w["core"]]
    a, b = metrics.SPLITS[split]
    return w[(w["start"] >= a) & (w["start"] <= b)]


def evaluate(name, scores, df, cases, window, prices) -> list[dict]:
    rows = []
    for split in EVAL_SPLITS:
        part = scores[scores["split"] == split]
        ev_cases = eval_cases(cases, window, split)
        lab = df.loc[df["split"] == split, ["ticker", "date", f"pos_{window}m", f"ignore_{window}m"]]
        for k in KS:
            alerts = metrics.weekly_alerts(part, k)
            em = metrics.event_metrics(alerts, ev_cases, prices)
            det = em["detected"].to_numpy(dtype=float) if len(em) else np.array([])
            lo, hi = metrics.bootstrap_ci(det)
            rows.append({
                "model": name, "split": split, "k": k, "n_cases": len(em),
                "event_recall": det.mean() if len(det) else np.nan, "ci_lo": lo, "ci_hi": hi,
                "precision_at_k": metrics.precision_at_k(alerts, lab, f"pos_{window}m", f"ignore_{window}m"),
                "median_lead_days": em["lead_days_from_start"].median(),
                "alert_before_peak": em["alert_before_peak"].mean(),
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, default=6, choices=(3, 6, 12))
    parser.add_argument("--models", default="")
    parser.add_argument("--hindsight", action="store_true")
    parser.add_argument("--drop-kap", action="store_true",
                        help="Ablation (tez sorusu 3): KAP / habersiz hareket özellikleri olmadan")
    parser.add_argument("--profile", choices=("raw", "rank", "drop"), default="raw",
                        help="Yavaş değişen profil özellikleri: ham / günlük kesitsel sıra / çıkar")
    args = parser.parse_args()
    t0 = time.time()

    df, cases = load(args.window)
    if args.profile == "rank":
        # Günlük kesitsel yüzdelik: "bugün borsadaki en küçük %10'da mı?" — zaman kaymasına dayanıklı
        for c in PROFILE:
            df[c] = df.groupby("date")[c].rank(pct=True)
    elif args.profile == "drop":
        df = df.drop(columns=PROFILE)
    if args.drop_kap:
        kap_cols = [c for c in df.columns if c.startswith(("n_", "no_news", "days_since_")) or c == "ret_20_z_per_news"]
        df = df.drop(columns=kap_cols)
        print(f"ablation: {len(kap_cols)} KAP sütunu çıkarıldı")
    y = training_target(df, cases, args.window, args.hindsight)
    train = (df["split"] == "train") & (df[f"ignore_{args.window}m"].fillna(0) == 0)
    Xtr, ytr = df.loc[train], y[train]
    scored = df["split"].isin(EVAL_SPLITS)
    prices = df.loc[scored, ["ticker", "date"]].copy()
    # Zirve tespiti için düzeltilmiş fiyat seviyesi: log getirilerin kümülatifi
    prices["close"] = df.loc[scored].groupby("ticker")["ret_1"].cumsum().fillna(0)
    print(f"eğitim: {len(Xtr):,} satır, pozitif {int(ytr.sum()):,} | değerlendirme: {int(scored.sum()):,} satır")

    wanted = [m for m in args.models.split(",") if m]
    rows = []
    for cls in ALL_MODELS:
        model = cls()
        if wanted and model.name not in wanted:
            continue
        t = time.time()
        model.fit(Xtr, ytr)
        s = df.loc[scored, ["ticker", "date", "split"]].copy()
        s["score"] = model.score(df.loc[scored])
        rows += evaluate(model.name, s, df, cases, args.window, prices)
        print(f"{model.name}: {time.time() - t:.0f}s")

    res = pd.DataFrame(rows)
    out = INTERIM / "results"
    out.mkdir(parents=True, exist_ok=True)
    tag = (f"w{args.window}" + ("_hindsight" if args.hindsight else "") + ("_nokap" if args.drop_kap else "")
           + (f"_profile{args.profile}" if args.profile != "raw" else ""))
    res.to_parquet(out / f"results_{tag}.parquet", index=False)

    mode = (("hindsight" if args.hindsight else "dürüst mod") + (", KAP özellikleri yok" if args.drop_kap else "")
            + (f", profil özellikleri: {args.profile}" if args.profile != "raw" else ""))
    lines = [f"# Sonuçlar — pencere {args.window} ay, {mode}", ""]
    for split in EVAL_SPLITS:
        r = res[res["split"] == split]
        if r.empty:
            continue
        lines += [f"## {split} ({metrics.SPLITS[split][0]} → {metrics.SPLITS[split][1]}), "
                  f"vaka sayısı: {int(r['n_cases'].iloc[0])}", ""]
        t = r.pivot_table(index="model", columns="k", values=["event_recall", "precision_at_k"])
        t.columns = [f"{'recall' if a == 'event_recall' else 'prec'}@{k}" for a, k in t.columns]
        k20 = r[r["k"] == 20].set_index("model")
        t["recall@20 %95 GA"] = k20.apply(lambda x: f"[{x.ci_lo:.2f}, {x.ci_hi:.2f}]", axis=1)
        t["öncü gün (medyan)@20"] = k20["median_lead_days"]
        t["zirveden önce@20"] = k20["alert_before_peak"]
        lines += [t.round(3).to_markdown(), ""]
    (ROOT / "docs" / f"sonuclar_{tag}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"toplam {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
