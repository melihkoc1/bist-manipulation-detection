"""Rastgele skor tabanı: olay bazlı recall'un rastgele seçimle ne kadar olduğunu ölçer.

Uzun pencereli (karar öncesi 6 ay) vakalarda haftalık k hisselik rastgele liste bile pencere
içinde bir kez alarm verme şansına sahiptir; bu yüzden recall tek başına "model işe yarıyor"
kanıtı değildir. Bu script rastgele skor, kural tabanlı model ve LightGBM'i, vakaları
"dönemi kararda yazan (kısa pencere)" ve "dönemi bilinmeyen (6 aylık pencere)" diye ayırarak
karşılaştırır.

Kullanım: python scripts/baseline_random.py [--seeds 5]
"""

import argparse
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from run_experiment import EVAL_SPLITS, KS, PROFILE, eval_cases, load, training_target  # noqa: E402

from bistmd.eval import metrics  # noqa: E402
from bistmd.models.core import RuleScore, Supervised  # noqa: E402

WINDOW = 6


def score_rounds(df, cases, cls, scored):
    """Yıllık yeniden eğitim (profil özellikleri çıkarılmış)."""
    parts = []
    for yr in sorted(df.loc[scored, "date"].dt.year.unique()):
        cutoff = pd.Timestamp(f"{yr - 1}-12-31")
        y = training_target(df, cases, WINDOW, False, cutoff)
        tr = (df["date"] <= cutoff) & (df[f"ignore_{WINDOW}m"].fillna(0) == 0)
        model = cls().fit(df.loc[tr], y[tr])
        rows = scored & (df["date"].dt.year == yr)
        s = df.loc[rows, ["ticker", "date", "split"]].copy()
        s["score"] = model.score(df.loc[rows])
        parts.append(s)
    return pd.concat(parts)


def detect(scores, cases, prices):
    """(split, k, grup) → vaka sayısı, recall, zirveden önce alarm oranı."""
    out = []
    for split in EVAL_SPLITS:
        part = scores[scores["split"] == split]
        ev = eval_cases(cases, WINDOW, split)
        for k in KS:
            alerts = metrics.weekly_alerts(part, k)
            em = metrics.event_metrics(alerts, ev, prices).merge(ev[["case_id", "known_period"]], on="case_id")
            for name, sub in [("tümü", em), ("dönem biliniyor (kısa pencere)", em[em.known_period]),
                              ("dönem bilinmiyor (6 ay)", em[~em.known_period])]:
                out.append({"split": split, "k": k, "grup": name, "n": len(sub),
                            "recall": sub["detected"].mean(), "once": sub["alert_before_peak"].mean()})
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()

    df, cases = load(WINDOW)
    df = df.drop(columns=PROFILE)
    scored = df["split"].isin(EVAL_SPLITS)
    prices = df.loc[scored, ["ticker", "date"]].copy()
    prices["close"] = df.loc[scored].groupby("ticker")["ret_1"].cumsum().fillna(0)
    base = df.loc[scored, ["ticker", "date", "split"]].copy()
    n_stocks = df.loc[scored].groupby(df["date"].dt.to_period("W-FRI"))["ticker"].nunique().median()
    print(f"haftada skorlanan hisse sayısı (medyan): {n_stocks:.0f}")

    res = {}
    rnd = []
    for seed in range(args.seeds):
        s = base.copy()
        s["score"] = np.random.default_rng(seed).random(len(s))
        rnd.append(detect(s, cases, prices))
    res["rastgele"] = pd.concat(rnd).groupby(["split", "k", "grup"], as_index=False).mean(numeric_only=True)

    s = base.copy()
    s["score"] = RuleScore().score(df.loc[scored])
    res["kural (0a)"] = detect(s, cases, prices)
    res["LightGBM (yıllık)"] = detect(score_rounds(df, cases, Supervised, scored), cases, prices)

    all_ = pd.concat({k: v for k, v in res.items()}, names=["model"]).reset_index(level=0)
    for k in (20, 50):
        t = all_[(all_.k == k) & all_.split.isin(["test", "forward"])]
        print(f"\n=== recall@{k} (test+ileriye dönük ortalaması; vaka sayısı toplamı) ===")
        tab = t.pivot_table(index="grup", columns="model", values="recall").round(3)
        tab["vaka (test+ileri)"] = t[t.model == "rastgele"].groupby("grup")["n"].sum()
        print(tab.to_string())
    t = all_[(all_.k == 20) & all_.split.isin(["test", "forward"])]
    print("\n=== zirveden ÖNCE alarm oranı @20 (tümü) ===")
    print(t[t.grup == "tümü"].pivot_table(index="split", columns="model", values="once").round(3).to_string())
    all_.to_csv("data/interim/results/baseline_random.csv", index=False)


if __name__ == "__main__":
    main()
