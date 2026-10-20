"""Değerlendirme v2: kaydedilmiş haftalık skorları rastgele tabana karşı ölçer.

Önkoşul: python scripts/score_v2.py ...
Kullanım: python scripts/evaluate_v2.py
Çıktı:    docs/sonuclar_v2.md, data/interim/results/v2_*.csv

Olay metrikleri yalnızca manipülasyon dönemi SPK kararında yazan ana set vakalarında
hesaplanır (kısa pencere). Rastgele taban her vaka için analitik olarak hesaplanır.
"""

import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from bistmd.eval import weekly as W  # noqa: E402
from bistmd.labels.windows import case_windows  # noqa: E402
from bistmd.paths import DB_PATH, INTERIM, ROOT  # noqa: E402

SCORES = INTERIM / "scores_v2"
KS = (10, 20, 50)
PERIODS = {"2017–2026": (2017, 2026), "2017–2021": (2017, 2021), "2022–2026": (2022, 2026)}
MODEL_ORDER = ["random", "0a_kural", "0b_basit", "1_iforest", "2_lightgbm", "3a_pu_agirlikli", "3b_pu_bagging"]


def load_cases():
    cases = duckdb.connect(str(DB_PATH), read_only=True).execute("SELECT * FROM spk_cases").df()
    w6 = case_windows(cases, 6)
    exact = w6[w6["core"] & w6["known_period"]][["case_id", "ticker", "start", "end"]]
    core6 = w6[w6["core"]][["case_id", "ticker", "start", "end"]]
    any12 = case_windows(cases, 12)[["case_id", "ticker", "start", "end"]]  # ana set dışı dahil
    return exact.reset_index(drop=True), core6, any12


def peak_dates(exact: pd.DataFrame) -> pd.Series:
    """Her vakanın dönemi içindeki kümülatif getiri zirvesinin tarihi."""
    f = pd.read_parquet(INTERIM / "features.parquet", columns=["ticker", "date", "ret_1"])
    f = f[f["ticker"].isin(exact["ticker"])]
    out = {}
    for _, c in exact.iterrows():
        p = f[(f["ticker"] == c["ticker"]) & (f["date"] >= c["start"]) & (f["date"] <= c["end"])]
        if len(p):
            out[c["case_id"]] = p.loc[p["ret_1"].fillna(0).cumsum().idxmax(), "date"]
    return pd.Series(out)


def evaluate_file(path: Path, exact, core6, any12, peaks) -> list[dict]:
    mode, kap, model = path.stem.split("_", 2)
    wk = pd.read_parquet(path)
    wk["week"] = pd.PeriodIndex(wk["week"], freq="W-FRI")
    lab = W.week_labels(wk, exact, any12)
    prec_lab = W.week_labels(wk, core6, any12).rename(columns={"y": "any_pos"})
    rows = []
    for pname, (y0, y1) in PERIODS.items():
        in_p = lambda d: d["week_end"].dt.year.between(y0, y1)  # noqa: E731
        cases_p = exact[exact["start"].dt.year.between(y0, y1)]
        auc, auc_lo, auc_hi = W.auc_with_ci(lab[in_p(lab)])
        r = {"mode": mode, "kap": kap, "model": model, "period": pname, "auc": auc, "auc_lo": auc_lo, "auc_hi": auc_hi}
        for k in KS:
            det = W.case_detection(wk[in_p(wk)], cases_p, k, peaks)
            rl = W.recall_lift_ci(det)
            r.update({f"n_cases": rl["n"], f"rec@{k}": rl["recall"], f"rnd@{k}": rl["random"],
                      f"lift@{k}": rl["lift"], f"lift_lo@{k}": rl["lift_lo"], f"lift_hi@{k}": rl["lift_hi"],
                      f"rec_lo@{k}": rl["recall_lo"], f"rec_hi@{k}": rl["recall_hi"]})
            if k == 20:
                bp = W.recall_lift_ci(det.dropna(subset=["p_random_before_peak"]),
                                      hit_col="detected_before_peak", p_col="p_random_before_peak")
                r.update({"pre_peak@20": bp["recall"], "pre_peak_rnd@20": bp["random"],
                          "lead_med@20": det["lead_days"].median()})
            pl = W.precision_lift(prec_lab[in_p(prec_lab)], k)
            r.update({f"prec@{k}": pl["precision"], f"base@{k}": pl["base_rate"], f"plift@{k}": pl["lift"]})
        rows.append(r)
    return rows


def fmt(x, lo=None, hi=None, d=2):
    if pd.isna(x):
        return "—"
    return f"{x:.{d}f}" + (f" [{lo:.{d}f}–{hi:.{d}f}]" if lo is not None and not pd.isna(lo) else "")


def table(res: pd.DataFrame, period: str = "2017–2026") -> str:
    r = res[res["period"] == period].set_index("model").reindex([m for m in MODEL_ORDER if m in set(res["model"])])
    lines = ["| Model | AUC [%95 GA] | recall@20 (rastgele) | lift@20 [%95 GA] | recall@50 (rastgele) | "
             "zirveden önce@20 (rastgele) | öncü gün@20 | isabet@10 lift |",
             "|---|---|---|---|---|---|---:|---:|"]
    for m, x in r.iterrows():
        lines.append(
            f"| {m} | {fmt(x['auc'], x['auc_lo'], x['auc_hi'])} | {x['rec@20']:.2f} ({x['rnd@20']:.2f}) | "
            f"{fmt(x['lift@20'], x['lift_lo@20'], x['lift_hi@20'], 1)} | {x['rec@50']:.2f} ({x['rnd@50']:.2f}) | "
            f"{x['pre_peak@20']:.2f} ({x['pre_peak_rnd@20']:.2f}) | {fmt(x['lead_med@20'], d=0)} | "
            f"{x['plift@10']:.1f}× |")
    return "\n".join(lines)


def main() -> None:
    exact, core6, any12 = load_cases()
    peaks = peak_dates(exact)
    rows = []
    for path in sorted(SCORES.glob("*.parquet")):
        rows += evaluate_file(path, exact, core6, any12, peaks)
        print(f"ölçüldü: {path.stem}", flush=True)
    res = pd.DataFrame(rows)
    (INTERIM / "results").mkdir(parents=True, exist_ok=True)
    res.to_csv(INTERIM / "results" / "v2_all.csv", index=False)

    n = int(res["n_cases"].max())
    lines = ["# Değerlendirme v2 — rastgele tabana karşı", "",
             "Vakalar: manipülasyon dönemi SPK kararında yazan ana set vakaları (kısa pencere, medyan 22 gün), "
             f"2017–2026 başlayan, fiyat verisi olan: **{n} vaka**. Haftalık liste: ~556 hisseden ilk k.",
             "Rastgele = her vaka için analitik yakalanma olasılığı. Lift = recall / rastgele. "
             "AUC: haftalık kesitsel yüzdelik; pozitif = vaka dönemi haftaları, negatif = hiçbir vaka penceresine "
             "(12 ay, ana set dışı dahil) değmeyen haftalar. GA: vaka kümesi bootstrap'i. "
             "İsabet@10 lift: haftalık ilk 10'un 6 aylık vaka pencerelerine denk gelme oranı / taban oran.", ""]
    for mode, kap, title in [("honest", "none", "Dürüst yıllık eğitim (ana sonuç) — KAP özellikleri yok"),
                             ("loyo", "none", "Yıl dışarıda bırakma (hindsight etiketler) — özellikler sinyal taşıyor mu?")]:
        sub = res[(res["mode"] == mode) & (res["kap"] == kap)]
        if mode == "loyo":
            base = res[(res["mode"] == "honest") & (res["kap"] == "none") & res["model"].isin(["random", "0a_kural"])]
            sub = pd.concat([base, sub])
        if sub.empty:
            continue
        lines += [f"## {title}", "", table(sub), ""]
        for p in ("2017–2021", "2022–2026"):
            lines += [f"**{p}:**", "", table(sub, p), ""]
    q3 = res[(res["mode"] == "honest") & res["model"].isin(["2_lightgbm", "3b_pu_bagging"])]
    if q3["kap"].nunique() > 1:
        t = q3[q3["period"] == "2017–2026"].pivot_table(index="model", columns="kap",
                                                       values=["auc", "lift@20", "plift@10"]).round(3)
        lines += ["## Tez sorusu 3 — KAP özellik kümeleri (dürüst, 2017–2026)", "", t.to_markdown(), ""]
    (ROOT / "docs" / "sonuclar_v2.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
