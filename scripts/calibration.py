"""Kural + PU haftalık yüzdeliğinin olasılık kalibrasyonu ve konformal eşik (MEL-90 deneyi).

Model değişmez. Dürüst: Y yılının kalibratörü / eşiği yalnız Y−1 sonuna kadarki haftalar ve Y−1 sonuna
kadar SPK'nın açıkladığı vakalarla kurulur. Tasarım Linear MEL-90'da sonuçtan önce kayıtlı.

Kullanım: python scripts/calibration.py [--score scores_v2/honest_none_4_kural_pu]
"""

import argparse
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).parent))
from evaluate_v2 import load_cases  # noqa: E402

from bistmd.eval import weekly as W  # noqa: E402
from bistmd.paths import DB_PATH, INTERIM  # noqa: E402

YEARS = range(2017, 2027)
ALPHA = 0.2
EPS = 1e-6


def logit(p):
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def metrics(p, y):
    p = np.clip(p, EPS, 1 - EPS)
    brier = np.mean((p - y) ** 2)
    ll = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    bins = pd.qcut(pd.Series(p).rank(method="first"), 10, labels=False)
    g = pd.DataFrame({"p": p, "y": y, "b": bins}).groupby("b").agg(p=("p", "mean"), y=("y", "mean"), n=("p", "size"))
    ece = float((g["n"] * (g["p"] - g["y"]).abs()).sum() / g["n"].sum())
    return {"brier": brier, "logloss": ll, "ece": ece}, g


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", default="scores_v2/honest_none_4_kural_pu")
    args = ap.parse_args()

    exact, core6, any12 = load_cases()
    dec = duckdb.connect(str(DB_PATH), read_only=True).execute(
        "SELECT case_id, first_decision FROM spk_cases").df().set_index("case_id")["first_decision"]
    wk = pd.read_parquet(INTERIM / f"{args.score}.parquet")
    wk["week"] = pd.PeriodIndex(wk["week"], freq="W-FRI")
    lab = W.week_labels(wk, core6, any12)
    lab = lab[lab["y"].notna()].copy()
    lab["year"] = lab["week_end"].dt.year
    lab["decided"] = pd.to_datetime(lab["case_id"].map(dec))

    # vaka düzeyi: dönemi bilinen ana set vakalarında pencere içi en yüksek haftalık yüzdelik
    ex = W.week_labels(wk, exact, any12)
    cmax = ex[ex["y"] == 1].groupby("case_id")["pct"].max()
    cs = exact.set_index("case_id").assign(maxpct=cmax, decided=pd.to_datetime(dec)).dropna(subset=["maxpct"])

    preds, conf = [], []
    for yr in YEARS:
        cut = pd.Timestamp(f"{yr - 1}-12-31")
        tr = lab[lab["week_end"] <= cut]
        ytr = ((tr["y"] == 1) & (tr["decided"] <= cut)).astype(int).to_numpy()
        te = lab[lab["year"] == yr]
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(tr["pct"], ytr)
        pl = LogisticRegression(C=1e6, max_iter=1000).fit(logit(tr["pct"].to_numpy())[:, None], ytr)
        preds.append(pd.DataFrame({"year": yr, "y": te["y"].to_numpy(), "pct": te["pct"].to_numpy(),
                                   "iso": iso.predict(te["pct"]),
                                   "platt": pl.predict_proba(logit(te["pct"].to_numpy())[:, None])[:, 1],
                                   "base": ytr.mean()}))
        # konformal: geçmişte açıklanmış vakaların en yüksek yüzdeliğinin ALPHA dilimi
        past = cs[cs["decided"] <= cut]["maxpct"].to_numpy()
        n = len(past)
        q = np.sort(past)[max(int(np.floor(ALPHA * (n + 1))) - 1, 0)] if n else np.nan
        pw = tr.loc[(tr["y"] == 1) & (tr["decided"] <= cut), "pct"].to_numpy()
        qw = np.quantile(pw, ALPHA) if len(pw) else np.nan
        new = cs[cs["start"].dt.year == yr]["maxpct"]
        tw = te.loc[te["y"] == 1, "pct"]
        conf.append({"year": yr, "n_cal": n, "thr_case": q, "cov_case": (new >= q).mean(), "n_new": len(new),
                     "alarm_case": (te["pct"] >= q).mean(), "thr_week": qw, "cov_week": (tw >= qw).mean(),
                     "alarm_week": (te["pct"] >= qw).mean()})

    P = pd.concat(preds, ignore_index=True)
    print("== Kalibrasyon (hafta düzeyi, son etiketlere göre) ==")
    for name, (y0, y1) in {"2017–2026": (2017, 2026), "2017–2021": (2017, 2021), "2022–2026": (2022, 2026)}.items():
        s = P[P["year"].between(y0, y1)]
        print(f"-- {name}: {len(s):,} hafta, gerçek oran {s['y'].mean():.4f}")
        for m in ("base", "iso", "platt"):
            r, _ = metrics(s[m].to_numpy(), s["y"].to_numpy())
            print(f"   {m:6s} ort. tahmin {s[m].mean():.4f}  Brier {r['brier']:.5f}  logloss {r['logloss']:.4f}  ECE {r['ece']:.4f}")
    s = P
    _, g = metrics(s["iso"].to_numpy(), s["y"].to_numpy())
    print("güvenilirlik (izotonik, 2017–2026, tahmin dilimleri):")
    print(g.round(4).to_string())
    for k in (0.01, 0.05):
        t = s[s["pct"] >= 1 - k]
        print(f"  üst %{k:.0%} yüzdelik: ort. izotonik {t['iso'].mean():.4f}, gerçek oran {t['y'].mean():.4f}, n {len(t):,}")
    C = pd.DataFrame(conf)
    print("\n== Konformal eşik (hedef kapsama %80) ==")
    print(C.round(3).to_string(index=False))
    for name, (y0, y1) in {"2017–2026": (2017, 2026), "2017–2021": (2017, 2021), "2022–2026": (2022, 2026)}.items():
        c = C[C["year"].between(y0, y1)]
        cov = (c["cov_case"] * c["n_new"]).sum() / c["n_new"].sum()
        print(f"  {name}: vaka kapsaması {cov:.3f} ({int(c['n_new'].sum())} vaka), ort. alarm oranı {c['alarm_case'].mean():.3f}; "
              f"hafta kapsaması {c['cov_week'].mean():.3f}, alarm {c['alarm_week'].mean():.3f}")
    out = INTERIM / "results"
    P.to_parquet(out / "calibration_preds.parquet", index=False)
    C.to_csv(out / "calibration_conformal.csv", index=False)


if __name__ == "__main__":
    main()
