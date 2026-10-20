"""Değerlendirme v2: haftalık listeler, analitik rastgele taban, lift ve küme bootstrap'i.

v1'deki hata: 6 aylık pencerelerde "pencere içinde en az bir alarm" metriği rastgele seçimle
de ~%50 çıkıyordu. v2'de:
- Olay bazlı metrikler yalnızca manipülasyon dönemi kararda yazan (kısa pencereli, medyan 22 gün)
  vakalarda hesaplanır.
- Her vaka için rastgele haftalık k'lık listenin vakayı yakalama olasılığı analitik olarak
  hesaplanır: 1 − Π_w (1 − k / N_w), w = vakanın penceresiyle örtüşen haftalar,
  N_w = o hafta skorlanan hisse sayısı. Lift = model recall / rastgele recall.
- Taban oranından bağımsız genel ölçü: haftalık kesitsel yüzdelik üzerinden AUC
  (pozitif: dönemi bilinen vaka haftaları; negatif: hiçbir vaka penceresine değmeyen haftalar).
- Güven aralıkları vaka düzeyinde küme bootstrap'iyle (aynı vakanın haftaları birlikte çekilir).
"""

import numpy as np
import pandas as pd


def to_weekly(scores: pd.DataFrame) -> pd.DataFrame:
    """ticker, date, score → hafta × hisse: en yüksek skor, haftalık sıra ve yüzdelik."""
    s = scores.dropna(subset=["score"]).copy()
    s["week"] = s["date"].dt.to_period("W-FRI")
    wk = s.groupby(["week", "ticker"], as_index=False, observed=True).agg(score=("score", "max"))
    wk["n_week"] = wk.groupby("week")["ticker"].transform("size")
    wk["rank"] = wk.groupby("week")["score"].rank(ascending=False, method="first")
    wk["pct"] = 1 - (wk["rank"] - 1) / wk["n_week"]  # 1 = haftanın en şüphelisi
    wk["week_start"] = wk["week"].dt.start_time
    wk["week_end"] = wk["week"].dt.end_time.dt.normalize()
    return wk


def _overlapping(wk: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    m = cases.merge(wk, on="ticker", how="inner")
    return m[(m["week_start"] <= m["end"]) & (m["week_end"] >= m["start"])]


def case_detection(wk: pd.DataFrame, cases: pd.DataFrame, k: int,
                   peaks: pd.Series | None = None) -> pd.DataFrame:
    """Vaka başına: hafta sayısı, yakalandı mı, rastgele yakalanma olasılığı, ilk alarm, öncü gün.

    cases: case_id, ticker, start, end.  peaks: case_id → zirve tarihi (opsiyonel).
    """
    m = _overlapping(wk, cases)
    m = m.assign(hit=m["rank"] <= k, q=1 - np.minimum(k / m["n_week"], 1.0))
    g = m.groupby("case_id")
    out = pd.DataFrame({
        "n_weeks": g.size(),
        "detected": g["hit"].any(),
        "p_random": 1 - g["q"].prod(),
    })
    first = m[m["hit"]].groupby("case_id")["week_end"].min()
    out["first_alert"] = first
    start = cases.set_index("case_id")["start"]
    out["lead_days"] = (out["first_alert"] - start.reindex(out.index)).dt.days
    if peaks is not None:
        pk = peaks.reindex(m["case_id"]).to_numpy()
        before = m[m["week_start"].to_numpy() <= pk]
        gb = before.groupby("case_id")
        out["detected_before_peak"] = gb["hit"].any().reindex(out.index, fill_value=False)
        out["p_random_before_peak"] = (1 - gb["q"].prod()).reindex(out.index, fill_value=0.0)
    return out.reset_index()


def week_labels(wk: pd.DataFrame, exact_cases: pd.DataFrame, any_windows: pd.DataFrame) -> pd.DataFrame:
    """Haftalara etiket: 1 = dönemi bilinen vaka haftası, 0 = hiçbir vaka penceresine değmeyen,
    NaN = belirsiz (yalnızca uzun pencereli / ana set dışı vakalara değen hafta)."""
    pos = _overlapping(wk, exact_cases)[["week", "ticker", "case_id"]].drop_duplicates(["week", "ticker"])
    touched = _overlapping(wk, any_windows)[["week", "ticker"]].drop_duplicates()
    out = wk.merge(pos, on=["week", "ticker"], how="left")
    out = out.merge(touched.assign(touched=1), on=["week", "ticker"], how="left")
    out["y"] = np.where(out["case_id"].notna(), 1.0, np.where(out["touched"].isna(), 0.0, np.nan))
    return out.drop(columns="touched")


def _auc_parts(pos_pct: np.ndarray, neg_sorted: np.ndarray) -> np.ndarray:
    """Her pozitif için, kendisinden düşük negatiflerin oranı (eşitlikler yarım)."""
    lo = np.searchsorted(neg_sorted, pos_pct, side="left")
    hi = np.searchsorted(neg_sorted, pos_pct, side="right")
    return (lo + hi) / 2 / len(neg_sorted)


def auc_with_ci(labeled: pd.DataFrame, n_boot: int = 1000, seed: int = 0) -> tuple[float, float, float]:
    """Haftalık yüzdelik üzerinden AUC ve vaka kümesi bootstrap %95 GA."""
    neg = np.sort(labeled.loc[labeled["y"] == 0, "pct"].to_numpy())
    pos = labeled[labeled["y"] == 1]
    parts = pd.Series(_auc_parts(pos["pct"].to_numpy(), neg), index=pos.index)
    by_case = parts.groupby(pos["case_id"]).agg(["sum", "size"])
    auc = by_case["sum"].sum() / by_case["size"].sum()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(by_case), size=(n_boot, len(by_case)))
    s, n = by_case["sum"].to_numpy()[idx].sum(1), by_case["size"].to_numpy()[idx].sum(1)
    boots = s / n
    return float(auc), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


def recall_lift_ci(det: pd.DataFrame, n_boot: int = 2000, seed: int = 0,
                   hit_col: str = "detected", p_col: str = "p_random") -> dict:
    """Recall, rastgele recall, lift ve vaka bootstrap'iyle lift için %95 GA."""
    d = det[hit_col].to_numpy(dtype=float)
    p = det[p_col].to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    rec_b, rnd_b = d[idx].mean(1), p[idx].mean(1)
    lift_b = rec_b / np.maximum(rnd_b, 1e-9)
    return {
        "n": len(d), "recall": d.mean(), "recall_lo": np.quantile(rec_b, 0.025),
        "recall_hi": np.quantile(rec_b, 0.975), "random": p.mean(),
        "lift": d.mean() / max(p.mean(), 1e-9),
        "lift_lo": np.quantile(lift_b, 0.025), "lift_hi": np.quantile(lift_b, 0.975),
    }


def precision_lift(wk_lab: pd.DataFrame, k: int, pos_col: str = "any_pos") -> dict:
    """Haftalık ilk k listesinde pozitif oranı / tüm hisse-haftalarda pozitif oranı."""
    valid = wk_lab[wk_lab[pos_col].notna()]
    top = valid[valid["rank"] <= k]
    base = valid[pos_col].mean()
    prec = top[pos_col].mean()
    return {"precision": prec, "base_rate": base, "lift": prec / base if base else np.nan}
