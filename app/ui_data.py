"""Arayüz için önbellekli veri okuyucuları. Yalnızca okur; hiçbir veriyi değiştirmez.

Kaynaklar: data/db/bist.duckdb (fiyat, SPK, KAP), data/interim/scores_v2 (dürüst haftalık skorlar),
data/interim/features.parquet (kural özellikleri), data/interim/results/v2_all.csv (sonuç tabloları).
"""

import duckdb
import numpy as np
import pandas as pd
import streamlit as st

from bistmd.eval import weekly as W
from bistmd.labels.windows import case_windows
from bistmd.models.core import RuleScore
from bistmd.paths import DB_PATH, INTERIM, ROOT

SCORES = INTERIM / "scores_v2"
RESULTS = INTERIM / "results" / "v2_all.csv"
FIGURES = ROOT / "docs" / "figures"
LIST_MODELS = ["4_kural_pu", "0a_kural", "3b_pu_bagging"]  # zaman makinesinde seçilebilenler
LATER_DECISION = pd.Timedelta(days=730)


def missing_inputs() -> list[str]:
    need = [DB_PATH, INTERIM / "features.parquet", RESULTS] + [SCORES / f"honest_none_{m}.parquet" for m in LIST_MODELS]
    return [str(p.relative_to(ROOT)) for p in need if not p.exists()]


def _query(sql: str, params: list | None = None) -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute(sql, params or []).df()
    finally:
        con.close()


@st.cache_data(show_spinner=False)
def weekly_scores(model: str) -> pd.DataFrame:
    w = pd.read_parquet(SCORES / f"honest_none_{model}.parquet",
                        columns=["week", "ticker", "rank", "pct", "n_week", "week_start", "week_end"])
    w["week_start"] = pd.to_datetime(w["week_start"])
    w["week_end"] = pd.to_datetime(w["week_end"])
    return w


@st.cache_data(show_spinner=False)
def company_names() -> dict[str, str]:
    """Güncel KAP listesindeki unvan; işlemden kalkanlar için KAP bildirimlerindeki şirket adı."""
    u = _query("SELECT ticker, title FROM universe")
    k = _query("SELECT ticker, any_value(company) AS title FROM kap_disclosures "
               "WHERE ticker IS NOT NULL GROUP BY ticker")
    return pd.concat([u, k]).dropna().drop_duplicates("ticker").set_index("ticker")["title"].to_dict()


@st.cache_data(show_spinner=False)
def cases() -> pd.DataFrame:
    """SPK vakaları + etiket penceresi; yalnızca ana set (çok hisseli kararlar ve piyasa tedbirleri hariç)."""
    c = _query("SELECT * FROM spk_cases")
    w = case_windows(c, 6)[["case_id", "start", "end", "known_period", "core"]]
    c = c.merge(w, on="case_id")
    return c[c["core"]].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def decisions() -> pd.DataFrame:
    return _query("SELECT ticker, decision_type, decision_date, period_start, period_end, ref, tier "
                  "FROM spk_decisions ORDER BY decision_date")


@st.cache_data(show_spinner=False)
def prices(ticker: str) -> pd.DataFrame:
    return _query("SELECT date, close, value_try FROM prices WHERE ticker = ? ORDER BY date", [ticker])


@st.cache_data(show_spinner=False)
def kap(ticker: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return _query("SELECT published_at, subject, summary FROM kap_disclosures "
                  "WHERE ticker = ? AND published_at BETWEEN ? AND ? ORDER BY published_at DESC",
                  [ticker, start, end + pd.Timedelta(days=1)])


@st.cache_resource(show_spinner=False)
def rule_features() -> pd.DataFrame:
    return pd.read_parquet(INTERIM / "features.parquet", columns=["ticker", "date", *RuleScore.RULES])


def rules_fired(tickers: list[str], week_start: pd.Timestamp, week_end: pd.Timestamp) -> dict[str, list[str]]:
    """Haftanın en çok kural sağlanan gününde sağlanan kurallar (hisse başına)."""
    f = rule_features()
    f = f[f["date"].between(week_start, week_end) & f["ticker"].isin(tickers)]
    thr = pd.Series(RuleScore.RULES)
    hits = f[list(thr.index)].ge(thr)
    f = f.assign(n_hits=hits.sum(axis=1))
    best = f.loc[f.groupby("ticker")["n_hits"].idxmax()] if len(f) else f
    return {r.ticker: [c for c in thr.index if hits.loc[i, c]] for i, r in best.iterrows()}


def spk_links(tickers: list[str], week_start: pd.Timestamp, week_end: pd.Timestamp) -> dict[str, tuple[str, int]]:
    """Hisse → (durum, gün). durum: 'in_period' / 'in_period_before' / 'later'."""
    c = cases()
    c = c[c["ticker"].isin(tickers)]
    out: dict[str, tuple[str, int]] = {}
    known = c[c["known_period"] & (c["start"] <= week_end) & (c["end"] >= week_start)]
    for _, r in known.sort_values("first_decision").iterrows():
        days = (r["first_decision"] - week_end).days
        out.setdefault(r["ticker"], ("in_period" if days >= 0 else "in_period_before", days))
    later = c[~c["known_period"] & (c["first_decision"] > week_end)
              & (c["first_decision"] <= week_end + LATER_DECISION)]
    for _, r in later.sort_values("first_decision").iterrows():
        out.setdefault(r["ticker"], ("later", (r["first_decision"] - week_end).days))
    return out


def tickers_in_known_periods(week_start: pd.Timestamp, week_end: pd.Timestamp) -> set[str]:
    c = cases()
    k = c[c["known_period"] & (c["start"] <= week_end) & (c["end"] >= week_start)]
    return set(k["ticker"])


@st.cache_data(show_spinner=False)
def results() -> pd.DataFrame:
    r = pd.read_csv(RESULTS)
    return r[(r["mode"] == "honest") & (r["kap"] == "none")]


@st.cache_data(show_spinner=False)
def spk_timing() -> dict:
    """Kural + PU'nun yakaladığı 2017–2026 vakalarında ilk alarm → SPK'nın ilk kararı / ilk cezası (gün).
    Vaka kümesi scripts/evaluate_v2.py ile aynı: ana set, dönemi kararda yazan, 2017+ başlayan."""
    c = cases()
    exact = c[c["known_period"] & (c["start"].dt.year >= 2017)][["case_id", "ticker", "start", "end"]]
    wk = weekly_scores("4_kural_pu").copy()
    wk["week"] = wk["week_end"].dt.to_period("W-FRI")
    det = W.case_detection(wk, exact, 20)
    d = det[det["detected"]].merge(exact, on="case_id")
    dec = decisions()
    first, sanction = [], []
    for _, r in d.iterrows():
        x = dec[(dec["ticker"] == r["ticker"]) & (dec["decision_date"] >= r["start"])]
        if x.empty:
            continue
        first.append((x["decision_date"].min() - r["first_alert"]).days)
        t1 = x.loc[x["tier"] == 1, "decision_date"]
        if len(t1):
            sanction.append((t1.min() - r["first_alert"]).days)
    first = np.array(first)
    return {"n": len(first), "pct_first": round(100 * (first > 0).mean()),
            "d_first": int(np.median(first)), "d_sanction": int(np.median(sanction))}
