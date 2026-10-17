"""Gerçekçi değerlendirme: zaman bölmeleri, haftalık top-k listeler, olay bazlı metrikler.

Senaryo: Bir gözetim analisti her hafta modelin en şüpheli gördüğü k hisseye bakar.
- weekly_alerts:  her hafta, hissenin o haftaki en yüksek skoruna göre ilk k hisse
- event_recall@k: vakaların kaçında, vaka penceresi içinde en az bir alarm verildi
- lead time:      ilk alarm ile manipülasyon döneminin başlangıcı / fiyat zirvesi arası
- precision@k:    haftalık listelerdeki hisse-haftaların ne kadarı pozitif pencerede
                  (etiketsiz ≠ temiz olduğundan bu bir ALT SINIRDIR)
"""

import numpy as np
import pandas as pd

# Varsayılan zaman bölmesi (PLAN.md B8)
SPLITS = {
    "train": ("2012-01-01", "2021-12-31"),
    "val": ("2022-01-01", "2022-12-31"),
    "test": ("2023-01-01", "2024-12-31"),
    "forward": ("2025-01-01", "2026-12-31"),
}


def split_of(dates: pd.Series) -> pd.Series:
    out = pd.Series("none", index=dates.index)
    for name, (a, b) in SPLITS.items():
        out[(dates >= a) & (dates <= b)] = name
    return out


def weekly_alerts(scores: pd.DataFrame, k: int) -> pd.DataFrame:
    """scores: ticker, date, score → hafta, ticker, week_score, rank, alert_date

    Hafta sonunda (o haftanın son işlem günü) liste oluşturulur; alarm tarihi o gündür.
    """
    s = scores.dropna(subset=["score"]).copy()
    s["week"] = s["date"].dt.to_period("W-FRI")
    wk = s.groupby(["week", "ticker"]).agg(week_score=("score", "max"), alert_date=("date", "max")).reset_index()
    wk["rank"] = wk.groupby("week")["week_score"].rank(ascending=False, method="first")
    return wk[wk["rank"] <= k].reset_index(drop=True)


def event_metrics(alerts: pd.DataFrame, cases: pd.DataFrame, prices: pd.DataFrame | None = None) -> pd.DataFrame:
    """Vaka başına: yakalandı mı, ilk alarm, öncü süre.

    cases: case_id, ticker, start, end (değerlendirme penceresi), known_period
    prices: ticker, date, close (zirve tarihini bulmak için, opsiyonel)
    """
    rows = []
    for _, c in cases.iterrows():
        a = alerts[(alerts["ticker"] == c["ticker"]) & (alerts["alert_date"] >= c["start"])
                   & (alerts["alert_date"] <= c["end"])]
        first = a["alert_date"].min() if len(a) else pd.NaT
        row = {"case_id": c["case_id"], "ticker": c["ticker"], "detected": len(a) > 0,
               "first_alert": first, "n_alert_weeks": len(a),
               "lead_days_from_start": np.nan, "peak_date": pd.NaT, "alert_before_peak": np.nan}
        if c.get("known_period", False) and pd.notna(first):
            row["lead_days_from_start"] = (first - c["start"]).days
        if prices is not None and pd.notna(first):
            p = prices[(prices["ticker"] == c["ticker"]) & (prices["date"] >= c["start"])
                       & (prices["date"] <= c["end"])]
            if len(p):
                peak = p.loc[p["close"].idxmax(), "date"]
                row["peak_date"] = peak
                row["alert_before_peak"] = bool(first <= peak)
        rows.append(row)
    cols = ["case_id", "ticker", "detected", "first_alert", "n_alert_weeks",
            "lead_days_from_start", "peak_date", "alert_before_peak"]
    out = pd.DataFrame(rows, columns=cols)
    out["alert_before_peak"] = out["alert_before_peak"].astype(float)
    return out


def precision_at_k(alerts: pd.DataFrame, labels: pd.DataFrame, pos_col: str, ignore_col: str | None) -> float:
    """Haftalık listelerdeki (hisse, hafta) çiftlerinin pozitif günlere denk gelme oranı."""
    lab = labels.copy()
    lab["week"] = lab["date"].dt.to_period("W-FRI")
    cols = [pos_col] + ([ignore_col] if ignore_col else [])
    wk = lab.groupby(["week", "ticker"])[cols].max().reset_index()
    m = alerts.merge(wk, on=["week", "ticker"], how="left").fillna({pos_col: 0})
    if ignore_col:
        m = m[m[ignore_col].fillna(0) == 0]
    return float(m[pos_col].mean()) if len(m) else np.nan


def bootstrap_ci(values: np.ndarray, n: int = 2000, alpha: float = 0.05, seed: int = 0) -> tuple[float, float]:
    """Vaka bazlı oranlar için yüzdelik bootstrap güven aralığı."""
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    means = rng.choice(values, size=(n, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))
