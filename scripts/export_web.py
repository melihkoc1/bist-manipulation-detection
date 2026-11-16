"""Web arayüzü (web/) için veri dışa aktarımı. Yalnızca okur; modelleri yeniden çalıştırmaz.

Kaynaklar: data/db/bist.duckdb, data/interim/scores_v2 (dürüst haftalık skorlar),
data/interim/features.parquet (kural göstergeleri), data/interim/results/*.csv.
Çıktı: web/public/data/ (git'e girmez; gerçek haftalık listeler yalnızca yerelde kalır)
  index.json          sonuç tabloları, zamanlama, vaka çalışmaları, hafta ve hisse listeleri
  weeks/<yıl>.json    her hafta, her model için ilk 50 hisse + kurallar + SPK bağlantısı
  stocks/<KOD>.json   fiyat, hacim, haftalık sıra, kural göstergeleri, SPK kararları, KAP

Önkoşul: score_v2.py --mode honest, ensemble_v2.py, evaluate_v2.py, case_studies.py
Kullanım: python scripts/export_web.py
"""

import json
import shutil
import sys
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from case_studies import spk_gap_summary  # noqa: E402
from evaluate_v2 import load_cases, peak_dates  # noqa: E402

from bistmd.eval import weekly as W  # noqa: E402
from bistmd.features import kap_content  # noqa: E402
from bistmd.labels.windows import case_windows  # noqa: E402
from bistmd.models.core import RuleScore  # noqa: E402
from bistmd.paths import DB_PATH, INTERIM, ROOT  # noqa: E402

OUT = ROOT / "web" / "public" / "data"
SCORES = INTERIM / "scores_v2"
RESULTS = INTERIM / "results"
LIST_MODELS = ["4_kural_pu", "0a_kural", "3b_pu_bagging"]  # zaman makinesinde seçilebilenler
RESULT_MODELS = ["random", "0a_kural", "1_iforest", "2_lightgbm", "3a_pu_agirlikli", "3b_pu_bagging", "4_kural_pu"]
CASE_STUDIES = ["IZFAS-0", "SANEL-0", "KGYO-0", "KONYA-0", "KUYAS-0"]
TOP = 50
K = 20
LATER = pd.Timedelta(days=730)
RULES = list(RuleScore.RULES)
KAP_GROUP = {"strong_news": "news", "weak_news": "news", "price_reactive": "price",
             "unusual_move": "price", "rumor": "rumor"}


def dump(path: Path, obj) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    path.write_text(s, encoding="utf-8")
    return len(s)


def iso(d) -> str | None:
    return None if pd.isna(d) else pd.Timestamp(d).strftime("%Y-%m-%d")


def r(x, nd=3):
    return None if x is None or pd.isna(x) else round(float(x), nd)


def query(sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


def load_week_scores(model: str) -> pd.DataFrame:
    w = pd.read_parquet(SCORES / f"honest_none_{model}.parquet",
                        columns=["week", "ticker", "rank", "pct", "n_week", "week_start", "week_end"])
    w["week_start"] = pd.to_datetime(w["week_start"])
    w["week_end"] = pd.to_datetime(w["week_end"])
    return w


def weekly_rule_values() -> pd.DataFrame:
    """Hisse × hafta: haftanın en çok kural sağlanan günündeki 6 kural göstergesi."""
    f = pd.read_parquet(INTERIM / "features.parquet", columns=["ticker", "date", "ret_20_z", *RULES])
    f["week_end"] = f["date"].dt.to_period("W-FRI").dt.end_time.dt.normalize()
    f["score"] = RuleScore().score(f)
    f = f.sort_values(["ticker", "week_end", "score", "date"], ascending=[True, True, False, False])
    f = f.drop_duplicates(["ticker", "week_end"])
    return f.set_index(["ticker", "week_end"])[RULES]


def case_table() -> pd.DataFrame:
    c = query("SELECT * FROM spk_cases")
    w = case_windows(c, 6)[["case_id", "start", "end", "known_period", "core"]]
    return c.merge(w, on="case_id")


def spk_link(ticker: str, ws: pd.Timestamp, we: pd.Timestamp, by_ticker: dict) -> tuple[str, int | None]:
    """Streamlit arayüzüyle aynı kural: 'in' (SPK'nın yazdığı dönem), 'later' (2 yıl içinde karar), ''."""
    c = by_ticker.get(ticker)
    if c is None:
        return "", None
    known = c[c["known_period"] & (c["start"] <= we) & (c["end"] >= ws)]
    if len(known):
        return "in", int((known["first_decision"].min() - we).days)
    later = c[~c["known_period"] & (c["first_decision"] > we) & (c["first_decision"] <= we + LATER)]
    if len(later):
        return "later", int((later["first_decision"].min() - we).days)
    return "", None


def export_weeks(names: dict, rules: pd.DataFrame, cases: pd.DataFrame) -> list[dict]:
    core = cases[cases["core"]]
    by_ticker = {t: g for t, g in core.groupby("ticker")}
    exact = core[core["known_period"]]
    scores = {m: load_week_scores(m) for m in LIST_MODELS}
    base = scores[LIST_MODELS[0]]
    weeks = (base.groupby("week_end").agg(start=("week_start", "first"), n=("n_week", "first"))
             .reset_index().sort_values("week_end"))

    # o hafta puanlanan ve SPK'nın yazdığı dönemde olan hisse sayısı (rastgele beklenti için)
    m = base[["ticker", "week_start", "week_end"]].merge(exact[["ticker", "start", "end"]], on="ticker")
    m = m[(m["start"] <= m["week_end"]) & (m["end"] >= m["week_start"])]
    in_period = m.drop_duplicates(["ticker", "week_end"]).groupby("week_end").size()

    tops = {mdl: s[s["rank"] <= TOP].sort_values(["week_end", "rank"]) for mdl, s in scores.items()}
    tops = {mdl: dict(tuple(t.groupby("week_end"))) for mdl, t in tops.items()}
    out_years: dict[int, list] = {}
    index = []
    for _, wk in weeks.iterrows():
        we, ws = wk["week_end"], wk["start"]
        entry = {"end": iso(we), "start": iso(ws), "n": int(wk["n"]), "inPeriod": int(in_period.get(we, 0)),
                 "lists": {}}
        for mdl in LIST_MODELS:
            t = tops[mdl].get(we)
            rows = []
            for row in ([] if t is None else t.itertuples()):
                rv = rules.loc[(row.ticker, we)].tolist() if (row.ticker, we) in rules.index else [None] * 6
                link, days = spk_link(row.ticker, ws, we, by_ticker)
                rows.append([row.ticker, int(row.rank), r(row.pct, 4), [r(v) for v in rv], link, days])
            entry["lists"][mdl] = rows
        out_years.setdefault(we.year, []).append(entry)
        index.append({"end": entry["end"], "start": entry["start"], "n": entry["n"]})
    for y, items in out_years.items():
        dump(OUT / "weeks" / f"{y}.json", {"weeks": items})
    return index


def classify_kap(kap: pd.DataFrame) -> pd.Series:
    cat = kap_content.classify(kap["subject"], kap["summary"]).map(kap_content.group_of)
    return cat.map(KAP_GROUP).fillna("other")


def export_stocks(names: dict, rules: pd.DataFrame, cases: pd.DataFrame, decisions: pd.DataFrame) -> list[dict]:
    wk = load_week_scores("4_kural_pu")
    tickers = sorted(set(wk["ticker"]) | set(cases.loc[cases["core"], "ticker"]))
    prices = query("SELECT ticker, date, close, value_try FROM prices ORDER BY ticker, date")
    prices = prices[prices["ticker"].isin(tickers)]
    kap = query("SELECT ticker, published_at, subject, summary, disclosure_id FROM kap_disclosures "
                "WHERE ticker IS NOT NULL ORDER BY published_at DESC")
    kap = kap[kap["ticker"].isin(tickers)]
    kap["grp"] = classify_kap(kap)
    p_by = dict(tuple(prices.groupby("ticker")))
    w_by = dict(tuple(wk.groupby("ticker")))
    k_by = dict(tuple(kap.groupby("ticker")))
    d_by = dict(tuple(decisions.groupby("ticker")))
    c_by = dict(tuple(cases.groupby("ticker")))
    rules_by = {t: g.droplevel(0) for t, g in rules.groupby(level=0)}
    out = []
    for t in tickers:
        p = p_by.get(t, pd.DataFrame(columns=["date", "close", "value_try"]))
        w = w_by.get(t, pd.DataFrame(columns=["week_end", "rank", "n_week"])).sort_values("week_end")
        rv = rules_by.get(t)
        ranks = []
        for row in w.itertuples():
            vals = rv.loc[row.week_end].tolist() if rv is not None and row.week_end in rv.index else [None] * 6
            ranks.append([iso(row.week_end), int(row.rank), int(row.n_week), *[r(v) for v in vals]])
        d = d_by.get(t, pd.DataFrame())
        dec = [{"date": iso(x.decision_date), "type": x.decision_type, "ref": x.ref, "tier": int(x.tier),
                "pStart": iso(x.period_start), "pEnd": iso(x.period_end)} for x in d.itertuples()]
        c = c_by.get(t, pd.DataFrame())
        cs = [{"id": x.case_id, "start": iso(x.start), "end": iso(x.end), "known": bool(x.known_period),
               "core": bool(x.core), "first": iso(x.first_decision)} for x in c.itertuples()]
        k = k_by.get(t, pd.DataFrame())
        kp = [[iso(x.published_at), x.subject or "", x.grp, int(x.disclosure_id)] for x in k.itertuples()]
        obj = {"ticker": t, "name": names.get(t, ""),
               "prices": {"d": [iso(x) for x in p["date"]], "c": [r(x, 4) for x in p["close"]],
                          "v": [None if pd.isna(x) else int(x) for x in p["value_try"]]},
               "ranks": ranks, "decisions": dec, "cases": cs, "kap": kp}
        dump(OUT / "stocks" / f"{t}.json", obj)
        out.append({"t": t, "name": names.get(t, ""), "nDec": len(dec),
                    "nCore": int(c["core"].sum()) if len(c) else 0, "scored": bool(len(w))})
    return out


def results_table() -> list[dict]:
    res = pd.read_csv(RESULTS / "v2_all.csv")
    res = res[(res["mode"] == "honest") & (res["kap"] == "none") & res["model"].isin(RESULT_MODELS)]
    cols = {"auc": "auc", "auc_lo": "aucLo", "auc_hi": "aucHi", "n_cases": "nCases", "rec@20": "rec",
            "rnd@20": "rnd", "lift@20": "lift", "pre_peak@20": "prePeak", "pre_peak_rnd@20": "prePeakRnd",
            "lead_med@20": "lead", "prec@10": "prec10", "base@10": "base10", "plift@10": "plift10",
            "rec@10": "rec10", "rnd@10": "rnd10", "rec@50": "rec50", "rnd@50": "rnd50"}
    return [{"model": x["model"], "period": x["period"], **{v: r(x[k], 4) for k, v in cols.items()}}
            for _, x in res.iterrows()]


def timing(decisions: pd.DataFrame) -> dict:
    """Kural + PU'nun yakaladığı 2017–2026 vakaları: ilk alarm → SPK'nın ilk kararı / ilk cezası (gün)."""
    exact, _, _ = load_cases()
    wk = load_week_scores("4_kural_pu")
    wk["week"] = wk["week_end"].dt.to_period("W-FRI")
    main = exact[exact["start"].dt.year >= 2017]
    det = W.case_detection(wk, main, K)
    g = spk_gap_summary(det, main, decisions)
    first = g["days_to_first_spk"].dropna()
    sanc = g["days_to_sanction"].dropna()
    return {"nCaught": int(det["detected"].sum()), "nCases": len(det), "first": [int(x) for x in first],
            "sanction": [int(x) for x in sanc], "medFirst": float(first.median()),
            "medSanction": float(sanc.median()), "pctBefore": round(float((first > 0).mean()), 3),
            "leadMed": float(det.loc[det["detected"], "lead_days"].median())}


def case_studies(cases: pd.DataFrame, decisions: pd.DataFrame) -> list[dict]:
    cs = pd.read_csv(RESULTS / "case_studies.csv", parse_dates=["start", "end", "first_alert"])
    exact, _, _ = load_cases()
    peaks = peak_dates(exact[exact["case_id"].isin(CASE_STUDIES)])
    prices = query("SELECT ticker, date, close FROM prices")
    out = []
    for cid in CASE_STUDIES:
        x = cs[cs["case_id"] == cid].iloc[0]
        t = cid.split("-")[0]
        p = prices[(prices["ticker"] == t)].set_index("date")["close"].sort_index()
        pk = peaks.get(cid)
        after = p[p.index > x["end"]].iloc[:120] if pk is not None else pd.Series(dtype=float)
        peak_px = float(p.loc[x["start"]:x["end"]].max())
        start_px = float(p.loc[:x["start"]].iloc[-1]) if len(p.loc[:x["start"]]) else None
        dec = decisions[(decisions["ticker"] == t) & (decisions["decision_date"] >= x["start"])]
        out.append({
            "id": cid, "ticker": t, "start": iso(x["start"]), "end": iso(x["end"]),
            "caught": bool(x["detected"]), "firstAlert": iso(x["first_alert"]),
            "leadDays": None if pd.isna(x["lead_days"]) else int(x["lead_days"]),
            "pRandom": r(x["p_random"], 2), "bestRank": int(x["best_rank"]),
            "daysToFirstSpk": None if pd.isna(x["days_to_first_spk"]) else int(x["days_to_first_spk"]),
            "daysToSanction": None if pd.isna(x["days_to_sanction"]) else int(x["days_to_sanction"]),
            "peak": iso(pk), "startPx": r(start_px, 4), "peakPx": r(peak_px, 4),
            "minAfter": r(after.min(), 4) if len(after) else None,
            "firstSpk": iso(dec["decision_date"].min()) if len(dec) else None,
            "firstSanction": iso(dec.loc[dec["tier"] == 1, "decision_date"].min()) if (dec["tier"] == 1).any() else None,
        })
    return out


def main() -> None:
    t0 = time.time()
    if OUT.exists():
        shutil.rmtree(OUT)
    u = query("SELECT ticker, title FROM universe")
    k = query("SELECT ticker, any_value(company) AS title FROM kap_disclosures WHERE ticker IS NOT NULL GROUP BY ticker")
    names = pd.concat([u, k]).dropna().drop_duplicates("ticker").set_index("ticker")["title"].to_dict()
    cases = case_table()
    decisions = query("SELECT ticker, decision_type, decision_date, period_start, period_end, ref, tier "
                      "FROM spk_decisions ORDER BY decision_date")
    print("kural göstergeleri…", flush=True)
    rules = weekly_rule_values()
    print(f"haftalar… ({time.time() - t0:.0f} sn)", flush=True)
    weeks = export_weeks(names, rules, cases)
    print(f"hisseler… ({time.time() - t0:.0f} sn)", flush=True)
    stocks = export_stocks(names, rules, cases, decisions)
    print(f"özet… ({time.time() - t0:.0f} sn)", flush=True)
    n_kap = int(query("SELECT count(*) AS n FROM kap_disclosures")["n"][0])
    index = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "models": LIST_MODELS, "rules": RuleScore.RULES, "top": TOP,
        "weeks": weeks, "stocks": stocks,
        "results": results_table(), "timing": timing(decisions),
        "cases": case_studies(cases, decisions),
        "counts": {"cases": len(cases), "core": int(cases["core"].sum()),
                   "known": int((cases["core"] & cases["known_period"]).sum()),
                   "decisions": len(decisions), "kap": n_kap,
                   "bulletinYears": [2009, int(decisions["decision_date"].dt.year.max())],
                   "minWeek": int(min(w["n"] for w in weeks)), "maxWeek": int(max(w["n"] for w in weeks)),
                   "meanWeek": round(float(np.mean([w["n"] for w in weeks])))},
    }
    dump(OUT / "index.json", index)
    size = sum(f.stat().st_size for f in OUT.rglob("*.json")) / 1e6
    print(f"bitti: {len(weeks)} hafta, {len(stocks)} hisse, {size:.0f} MB → {OUT.relative_to(ROOT)} "
          f"({time.time() - t0:.0f} sn)")


if __name__ == "__main__":
    main()
