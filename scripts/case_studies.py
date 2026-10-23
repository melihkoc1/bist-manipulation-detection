"""Vaka çalışmaları: seçilen SPK vakalarında fiyat, hacim ve sistemin haftalık sırası.

Model: birleşik kural + PU skoru (dürüst yıllık eğitim). Her vaka için bir grafik ve özet satırı.
Ayrıca tüm değerlendirme vakaları için "ilk alarm ile SPK'nın ilk kararı arasındaki süre" özeti.

Önkoşul: python scripts/score_v2.py --mode honest && python scripts/ensemble_v2.py
Kullanım: python scripts/case_studies.py HUBVC-0 KGYO-0 ...
Çıktı:    docs/figures/vaka_<case_id>.png, data/interim/results/case_studies.csv
"""

import argparse
import sys
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.ticker  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from evaluate_v2 import SCORES, load_cases, peak_dates  # noqa: E402

from bistmd.eval import weekly as W  # noqa: E402
from bistmd.models.core import RuleScore  # noqa: E402
from bistmd.paths import DB_PATH, INTERIM, ROOT  # noqa: E402

MODEL = "honest_none_4_kural_pu"
K = 20
FIG_DIR = ROOT / "docs" / "figures"
BEFORE, AFTER = pd.Timedelta(days=120), pd.Timedelta(days=120)


def load_scores() -> pd.DataFrame:
    wk = pd.read_parquet(SCORES / f"{MODEL}.parquet")
    wk["week"] = pd.PeriodIndex(wk["week"], freq="W-FRI")
    return wk


def spk_gap_summary(det: pd.DataFrame, exact: pd.DataFrame, decisions: pd.DataFrame) -> pd.DataFrame:
    """Yakalanan vakalarda ilk alarm → SPK'nın dönem başlangıcından sonraki ilk kararı (gün)."""
    d = det[det["detected"]].merge(exact, on="case_id")
    rows = []
    for _, c in d.iterrows():
        dec = decisions[(decisions["ticker"] == c["ticker"]) & (decisions["decision_date"] >= c["start"])]
        if dec.empty:
            continue
        first_any = dec["decision_date"].min()
        tier1 = dec.loc[dec["tier"] == 1, "decision_date"]
        rows.append({"case_id": c["case_id"], "first_alert": c["first_alert"],
                     "days_to_first_spk": (first_any - c["first_alert"]).days,
                     "days_to_sanction": (tier1.min() - c["first_alert"]).days if len(tier1) else None})
    return pd.DataFrame(rows)


def plot_case(case: pd.Series, wk: pd.DataFrame, prices: pd.DataFrame, decisions: pd.DataFrame,
              det: pd.Series) -> Path:
    lo, hi = case["start"] - BEFORE, case["end"] + AFTER
    p = prices[(prices["ticker"] == case["ticker"]) & prices["date"].between(lo, hi)]
    w = wk[(wk["ticker"] == case["ticker"]) & wk["week_end"].between(lo, hi)]
    dec = decisions[(decisions["ticker"] == case["ticker"]) & (decisions["decision_date"] >= case["start"])]

    fig, axes = plt.subplots(3, 1, figsize=(10, 7.5), sharex=True,
                             gridspec_kw={"height_ratios": [3, 1.3, 1.5]})
    ax_p, ax_v, ax_r = axes
    for ax in axes:
        ax.axvspan(case["start"], case["end"], color="#f4a261", alpha=0.25, lw=0)
        ax.grid(alpha=0.25)
    ax_p.plot(p["date"], p["close"], color="#264653", lw=1.4)
    ax_p.set_ylabel("Fiyat (düzeltilmiş, TL)")
    ax_v.bar(p["date"], p["value_try"] / 1e6, color="#2a9d8f", width=1.0)
    ax_v.set_ylabel("Hacim (mn TL)")
    ax_r.plot(w["week_end"], w["rank"], color="#6d597a", marker="o", ms=3, lw=1)
    ax_r.axhline(K, color="#e63946", ls="--", lw=1)
    ax_r.text(w["week_end"].min(), K, f" ilk {K} (alarm eşiği)", color="#e63946", va="bottom", fontsize=8)
    ax_r.set_yscale("log")
    ax_r.set_yticks([1, 5, 20, 100, 500])
    ax_r.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax_r.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax_r.set_ylim(600, 0.8)  # ters eksen: 1 üstte
    ax_r.set_ylabel("Haftalık sıra\n(1 = en şüpheli)")

    handles = [plt.Rectangle((0, 0), 1, 1, color="#f4a261", alpha=0.4, label="SPK'nın belirttiği manipülasyon dönemi")]
    if pd.notna(det.get("first_alert")):
        for ax in axes:
            ax.axvline(det["first_alert"], color="#e63946", lw=1.5)
        handles.append(plt.Line2D([], [], color="#e63946", lw=1.5, label="Sistemin ilk alarmı"))
    inside = dec[dec["decision_date"] <= hi]
    for d in inside["decision_date"].unique():
        for ax in axes:
            ax.axvline(d, color="black", ls=":", lw=1.3)
    if len(inside):
        handles.append(plt.Line2D([], [], color="black", ls=":", lw=1.3, label="SPK kararı"))
    later = dec[dec["decision_date"] > hi]
    title = f"{case['ticker']} — {case['start']:%d.%m.%Y}–{case['end']:%d.%m.%Y}"
    if len(later):
        title += f"  (sonraki SPK kararı: {later['decision_date'].min():%d.%m.%Y}, grafik dışında)"
    ax_p.set_title(title, fontsize=11)
    ax_p.legend(handles=handles, loc="upper left", fontsize=8, framealpha=0.9)
    ax_r.xaxis.set_major_formatter(mdates.DateFormatter("%m.%Y"))
    fig.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / f"vaka_{case['case_id']}.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def rules_at(feats: pd.DataFrame, ticker: str, date: pd.Timestamp) -> str:
    """İlk alarm haftasında sağlanan kurallar (haftanın en yüksek kural skorlu günü)."""
    f = feats[(feats["ticker"] == ticker) & feats["date"].between(date - pd.Timedelta(days=6), date)]
    if f.empty:
        return ""
    row = f.loc[RuleScore().score(f).idxmax()]
    return ", ".join(f"{c}={row[c]:.2f}" for c, t in RuleScore.RULES.items() if row[c] >= t)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*")
    args = ap.parse_args()

    exact, _, _ = load_cases()
    peaks = peak_dates(exact)
    wk = load_scores()
    det = W.case_detection(wk, exact, K, peaks)
    con = duckdb.connect(str(DB_PATH), read_only=True)
    decisions = con.execute("SELECT ticker, decision_type, decision_date, tier FROM spk_decisions").df()
    prices = con.execute("SELECT ticker, date, close, value_try FROM prices").df()
    con.close()

    gap = spk_gap_summary(det, exact, decisions)
    main_set = gap[gap["case_id"].isin(exact.loc[exact["start"].dt.year >= 2017, "case_id"])]
    print(f"Yakalanan vakalar (2017–2026, n={len(main_set)}): ilk alarm → SPK'nın ilk kararı medyan "
          f"{main_set['days_to_first_spk'].median():.0f} gün; → ilk ceza/suç duyurusu medyan "
          f"{main_set['days_to_sanction'].median():.0f} gün")
    print(f"  ilk karardan önce alarm: {(main_set['days_to_first_spk'] > 0).mean():.0%}; "
          f"ilk karardan ≥30 gün önce: {(main_set['days_to_first_spk'] >= 30).mean():.0%}; "
          f"cezadan ≥180 gün önce: {(main_set['days_to_sanction'] >= 180).mean():.0%}")

    if not args.cases:
        return
    feats = pd.read_parquet(INTERIM / "features.parquet",
                            columns=["ticker", "date", "ret_20_z", *RuleScore.RULES])
    rows = []
    for cid in args.cases:
        case = exact[exact["case_id"] == cid].iloc[0]
        d = det.set_index("case_id").loc[cid]
        path = plot_case(case, wk, prices, decisions, d)
        g = gap.set_index("case_id")
        rows.append({
            "case_id": cid, "start": case["start"].date(), "end": case["end"].date(),
            "detected": bool(d["detected"]), "first_alert": d["first_alert"],
            "lead_days": d["lead_days"], "before_peak": bool(d["detected_before_peak"]),
            "p_random": round(d["p_random"], 2), "best_rank": int(wk[(wk["ticker"] == case["ticker"])
                                                                     & wk["week_end"].between(case["start"], case["end"] + pd.Timedelta(days=6))]["rank"].min()),
            "days_to_first_spk": g["days_to_first_spk"].get(cid), "days_to_sanction": g["days_to_sanction"].get(cid),
            "rules": rules_at(feats, case["ticker"], d["first_alert"]) if d["detected"] else "",
            "figure": path.relative_to(ROOT).as_posix(),
        })
    res = pd.DataFrame(rows)
    (INTERIM / "results").mkdir(parents=True, exist_ok=True)
    res.to_csv(INTERIM / "results" / "case_studies.csv", index=False)
    print(res.to_string())


if __name__ == "__main__":
    main()
