"""Modeller arası eşleştirilmiş karşılaştırma (aynı vakalar üzerinde bootstrap).

İki modelin güven aralıklarının örtüşmesi, farkın anlamsız olduğunu göstermez; aynı vakalar
yeniden örneklenerek farkın kendi güven aralığı hesaplanır. Fark GA'sı 0'ı içermiyorsa
fark anlamlıdır (%95).

Kullanım: python scripts/compare_v2.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from evaluate_v2 import SCORES, load_cases  # noqa: E402

from bistmd.eval import weekly as W  # noqa: E402
from bistmd.paths import ROOT  # noqa: E402

N_BOOT = 4000
COMPARISONS = [
    # (soru, A, B) — fark = A − B
    ("Soru 2: PU bagging vs gözetimli", "honest_none_3b_pu_bagging", "honest_none_2_lightgbm"),
    ("Soru 2: PU ağırlıklı vs gözetimli", "honest_none_3a_pu_agirlikli", "honest_none_2_lightgbm"),
    ("ML vs kural: PU bagging vs kural", "honest_none_3b_pu_bagging", "honest_none_0a_kural"),
    ("ML vs kural: LightGBM vs kural", "honest_none_2_lightgbm", "honest_none_0a_kural"),
    ("Gözetimsiz: Isolation Forest vs kural", "honest_none_1_iforest", "honest_none_0a_kural"),
    ("Etiket bolluğu: LightGBM hindsight vs dürüst", "loyo_none_2_lightgbm", "honest_none_2_lightgbm"),
    ("Soru 3: LightGBM habersiz hareket vs KAP yok", "honest_nonews_2_lightgbm", "honest_none_2_lightgbm"),
    ("Soru 3: LightGBM tüm KAP vs KAP yok", "honest_all_2_lightgbm", "honest_none_2_lightgbm"),
    ("Soru 3: PU bagging habersiz hareket vs KAP yok", "honest_nonews_3b_pu_bagging", "honest_none_3b_pu_bagging"),
]


def per_case(name: str, exact, any12):
    wk = pd.read_parquet(SCORES / f"{name}.parquet")
    wk["week"] = pd.PeriodIndex(wk["week"], freq="W-FRI")
    lab = W.week_labels(wk, exact, any12)
    neg = np.sort(lab.loc[lab["y"] == 0, "pct"].to_numpy())
    pos = lab[lab["y"] == 1]
    parts = pd.Series(W._auc_parts(pos["pct"].to_numpy(), neg), index=pos.index)
    auc = parts.groupby(pos["case_id"]).agg(["sum", "size"])
    det = W.case_detection(wk, exact, 20).set_index("case_id")
    return auc, det


def main() -> None:
    exact, _, any12 = load_cases()
    exact = exact[exact["start"].dt.year >= 2017]  # ana tabloyla aynı vaka kümesi
    cache = {}
    rows = []
    rng = np.random.default_rng(0)
    for q, a, b in COMPARISONS:
        if not ((SCORES / f"{a}.parquet").exists() and (SCORES / f"{b}.parquet").exists()):
            continue
        for n in (a, b):
            cache.setdefault(n, per_case(n, exact, any12))
        (auc_a, det_a), (auc_b, det_b) = cache[a], cache[b]
        cases = auc_a.index.intersection(auc_b.index).intersection(det_a.index).intersection(det_b.index)
        sa, na = auc_a.loc[cases, "sum"].to_numpy(), auc_a.loc[cases, "size"].to_numpy()
        sb, nb = auc_b.loc[cases, "sum"].to_numpy(), auc_b.loc[cases, "size"].to_numpy()
        da = det_a.loc[cases, "detected"].to_numpy(float)
        db = det_b.loc[cases, "detected"].to_numpy(float)
        idx = rng.integers(0, len(cases), size=(N_BOOT, len(cases)))
        d_auc = sa[idx].sum(1) / na[idx].sum(1) - sb[idx].sum(1) / nb[idx].sum(1)
        d_rec = da[idx].mean(1) - db[idx].mean(1)
        rows.append({
            "karşılaştırma": q, "vaka": len(cases),
            "AUC farkı": sa.sum() / na.sum() - sb.sum() / nb.sum(),
            "AUC GA": f"[{np.quantile(d_auc, .025):+.3f}, {np.quantile(d_auc, .975):+.3f}]",
            "AUC anlamlı": "evet" if np.quantile(d_auc, .025) > 0 or np.quantile(d_auc, .975) < 0 else "hayır",
            "recall@20 farkı": da.mean() - db.mean(),
            "recall GA": f"[{np.quantile(d_rec, .025):+.3f}, {np.quantile(d_rec, .975):+.3f}]",
            "recall anlamlı": "evet" if np.quantile(d_rec, .025) > 0 or np.quantile(d_rec, .975) < 0 else "hayır",
        })
    res = pd.DataFrame(rows)
    md = res.to_markdown(index=False, floatfmt="+.3f")
    print(md)
    doc = ROOT / "docs" / "sonuclar_v2.md"
    text = doc.read_text(encoding="utf-8").split("\n## Eşleştirilmiş karşılaştırmalar")[0]
    doc.write_text(text.rstrip() + "\n\n## Eşleştirilmiş karşılaştırmalar (aynı vakalar, bootstrap %95 GA, 2017–2026)\n\n"
                   + md + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
