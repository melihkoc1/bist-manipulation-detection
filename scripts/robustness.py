"""Sağlamlık testleri (MEL-15): ana sonuç farklı kesitlerde de geçerli mi?

Kesitler (2012–2026, dönemi bilinen 184 vaka; ana dönem 2017–2026 ayrıca):
  1. Liste uzunluğu k: 5, 10, 20, 30, 50, 100
  2. Yıl: her yılın vakaları ayrı
  3. Şirket büyüklüğü: dönem başındaki piyasa değerine göre üç eşit grup
  4. Vaka süresi: kısa / orta / uzun (rastgele seçim uzun vakaları daha kolay yakalar)
Her satırda yakalama, rastgele taban ve lift [%95 GA] verilir.

Önkoşul: score_v2.py --mode honest, ensemble_v2.py
Kullanım: python scripts/robustness.py
Çıktı:    docs/saglamlik.md (her çalıştırmada yeniden yazılır)
"""

import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from evaluate_v2 import SCORES, load_cases  # noqa: E402

from bistmd.eval import weekly as W  # noqa: E402
from bistmd.paths import DB_PATH, ROOT  # noqa: E402

MODELS = {"4_kural_pu": "Kural + PU", "0a_kural": "Kurallar", "3b_pu_bagging": "PU bagging"}
KS = [5, 10, 20, 30, 50, 100]


def load(model: str) -> pd.DataFrame:
    wk = pd.read_parquet(SCORES / f"honest_none_{model}.parquet")
    wk["week"] = pd.PeriodIndex(wk["week"], freq="W-FRI")
    return wk


def row(det: pd.DataFrame, **label) -> dict:
    r = W.recall_lift_ci(det)
    return {**label, "vaka": r["n"], "yakalama": r["recall"], "rastgele": r["random"],
            "lift": r["lift"], "GA": f"[{r['lift_lo']:.1f}–{r['lift_hi']:.1f}]"}


def md(df: pd.DataFrame) -> str:
    d = df.copy()
    for c in ("yakalama", "rastgele"):
        d[c] = d[c].map(lambda x: f"{x:.2f}")
    d["lift"] = d["lift"].map(lambda x: f"{x:.1f}×")
    return d.to_markdown(index=False)


def main() -> None:
    exact, _, _ = load_cases()
    exact = exact[exact["start"].dt.year >= 2012].copy()  # evaluate_v2 ile aynı: skorlar 2012'de başlıyor
    con = duckdb.connect(str(DB_PATH), read_only=True)
    mcap = con.execute("SELECT ticker, date, mcap_try FROM prices WHERE mcap_try IS NOT NULL").df()
    con.close()
    # dönem başındaki (veya hemen öncesindeki) piyasa değeri, enflasyon etkisini azaltmak için yıl içi sıralamayla
    mcap["date"] = mcap["date"].astype("datetime64[ns]")
    exact["start"] = exact["start"].astype("datetime64[ns]")
    mcap = mcap.sort_values("date")
    start_mcap = pd.merge_asof(exact.sort_values("start"), mcap.rename(columns={"date": "start"}),
                               on="start", by="ticker", direction="backward")
    mcap["year"] = mcap["date"].dt.year
    yr_med = mcap.groupby("year")["mcap_try"].median()
    start_mcap["rel_mcap"] = start_mcap["mcap_try"] / start_mcap["start"].dt.year.map(yr_med)
    exact = exact.merge(start_mcap[["case_id", "rel_mcap"]], on="case_id", how="left")
    exact["days"] = (exact["end"] - exact["start"]).dt.days
    exact["size"] = pd.qcut(exact["rel_mcap"], 3, labels=["küçük", "orta", "büyük"])
    exact["dur"] = pd.cut(exact["days"], [-1, 45, 120, 1e9], labels=["kısa (≤45 gün)", "orta (46–120)", "uzun (>120)"])

    wks = {m: load(m) for m in MODELS}
    sections = []

    rows = []
    for m, name in MODELS.items():
        for per, y0 in (("2017–2026", 2017), ("2012–2026", 2012)):
            c = exact[exact["start"].dt.year >= y0]
            w = wks[m][wks[m]["week_end"].dt.year >= y0]
            for k in KS:
                rows.append(row(W.case_detection(w, c, k), model=name, dönem=per, k=k))
    sections.append(("1. Liste uzunluğu (k)", md(pd.DataFrame(rows))))

    rows = []
    det = W.case_detection(wks["4_kural_pu"], exact, 20).merge(exact, on="case_id")
    for yr, g in det.groupby(det["start"].dt.year):
        rows.append(row(g, yıl=yr))
    sections.append(("2. Yıllara göre (Kural + PU, k = 20; vakanın başladığı yıl)", md(pd.DataFrame(rows))))

    rows = []
    for col, title in (("size", "büyüklük"), ("dur", "süre")):
        for m, name in MODELS.items():
            d = W.case_detection(wks[m], exact, 20).merge(exact, on="case_id")
            for grp, g in d.groupby(col, observed=True):
                rows.append(row(g, kesit=title, grup=grp, model=name))
    t = pd.DataFrame(rows)
    sections.append(("3. Şirket büyüklüğü (dönem başı piyasa değeri / o yılın medyanı, üç eşit grup; k = 20)",
                     md(t[t["kesit"] == "büyüklük"].drop(columns="kesit"))))
    sections.append(("4. Vaka süresi (k = 20)", md(t[t["kesit"] == "süre"].drop(columns="kesit"))))

    text = ["# Sağlamlık testleri", "",
            "`scripts/robustness.py` üretir; her çalıştırmada yeniden yazılır. Yorum: `docs/yorum_v2.md`.", "",
            "Dürüst yıllık eğitim skorları; dönemi kararda yazan ana set vakaları (2012–2026: 184). "
            "Rastgele: aynı uzunlukta rastgele listenin vakayı en az bir hafta yakalama olasılığı. "
            "GA: lift için vaka bootstrap %95 güven aralığı.", ""]
    for h, body in sections:
        text += [f"## {h}", "", body, ""]
    out = ROOT / "docs" / "saglamlik.md"
    out.write_text("\n".join(text), encoding="utf-8")
    print("\n".join(text))


if __name__ == "__main__":
    main()
