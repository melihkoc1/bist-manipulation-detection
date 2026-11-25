"""Denenen diğer modellerin (MEL-81…88, MEL-32) 2017–2026 sonuçlarını tek tabloda toplar.

Her model için: AUC, yakalama@20, rastgele yakalama, ilk 10 isabeti ve karşılığına göre eşli
bootstrap farkı (aynı vakalar). Skorlar deney klasörlerinden okunur (data/interim/scores_exp_*,
depoda değil); her biri deneyin kendi betiğiyle üretilir (bkz. docs/yorum_v2.md).

Kullanım: python scripts/alt_models.py   → data/interim/results/alt_models.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from compare_v2 import N_BOOT, per_case  # noqa: E402
from evaluate_v2 import evaluate_file, load_cases, peak_dates  # noqa: E402

from bistmd.paths import INTERIM  # noqa: E402

PU, ENS, LGBM, IF = "scores_v2/honest_none_3b_pu_bagging", "scores_v2/honest_none_4_kural_pu", \
    "scores_v2/honest_none_2_lightgbm", "scores_v2/honest_none_1_iforest"
# (anahtar, Türkçe ad, İngilizce ad, grup, skor dosyası, karşılığı, Linear)
MODELS = [
    ("2b", "Lojistik regresyon", "Logistic regression", "tek", "scores_exp_mel81/honest_none_2b_lojistik", LGBM, "MEL-81"),
    ("3c", "PU-lojistik", "PU-logistic", "tek", "scores_exp_mel81/honest_none_3c_pu_lojistik", PU, "MEL-81"),
    ("3d", "nnPU (doğrusal)", "nnPU (linear)", "tek", "scores_exp_mel82/honest_none_3d_nnpu_lineer", PU, "MEL-82"),
    ("3f", "PU-Random Forest", "PU-Random Forest", "tek", "scores_exp_mel83/honest_none_3f_pu_rf", PU, "MEL-83"),
    ("3g", "PU-Extra Trees", "PU-Extra Trees", "tek", "scores_exp_mel83/honest_none_3g_pu_et", PU, "MEL-83"),
    ("5b", "Grafik şekli benzerliği (DTW)", "Chart-shape similarity (DTW)", "tek", "scores_exp_mel84/honest_none_5b_dtw_knn", PU, "MEL-84"),
    ("6", "Derin öğrenme (1B CNN)", "Deep learning (1D CNN)", "tek", "scores_exp_mel85/honest_none_6_cnn", PU, "MEL-85"),
    ("1b", "Otomatik kodlayıcı", "Autoencoder", "tek", "scores_exp_mel86/honest_none_1b_autoencoder", IF, "MEL-86"),
    ("7", "Çöküş modeli (SPK etiketi yok)", "Crash model (no SPK labels)", "tek", "scores_exp_mel87/honest_none_7_cokus", PU, "MEL-87"),
    ("32c", "PU + kendi örüntü etiketleri (C)", "PU + own pattern labels (C)", "tek", "scores_exp_mel32c/honest_none_3b_pu_bagging", PU, "MEL-32"),
    ("88", "PU + birlikte sıçrama ağı", "PU + co-surge network", "tek", "scores_exp_mel88/honest_none_3b_pu_bagging", PU, "MEL-88"),
    ("32b", "PU + kendi örüntü etiketleri (B)", "PU + own pattern labels (B)", "tek", "scores_exp_mel32b/honest_none_3b_pu_bagging", PU, "MEL-32"),
    ("e3a", "Kural + Elkan–Noto PU", "Rules + Elkan–Noto PU", "birlesim", "scores_exp_mel82_en/honest_none_4_kural_pu", ENS, "MEL-82"),
    ("e3c", "Kural + PU-lojistik", "Rules + PU-logistic", "birlesim", "scores_exp_mel81_pu/honest_none_4_kural_pu", ENS, "MEL-81"),
    ("e3d", "Kural + nnPU", "Rules + nnPU", "birlesim", "scores_exp_mel82_nn/honest_none_4_kural_pu", ENS, "MEL-82"),
    ("e3f", "Kural + PU-Random Forest", "Rules + PU-Random Forest", "birlesim", "scores_exp_mel83_3f_pu_rf/honest_none_4_kural_pu", ENS, "MEL-83"),
    ("e3g", "Kural + PU-Extra Trees", "Rules + PU-Extra Trees", "birlesim", "scores_exp_mel83_3g_pu_et/honest_none_4_kural_pu", ENS, "MEL-83"),
    ("u3f", "Kural + PU + PU-Random Forest", "Rules + PU + PU-Random Forest", "birlesim", "scores_exp_mel83_uclu/honest_none_4_kural_pu", ENS, "MEL-83"),
    ("u5b", "Kural + PU + şekil benzerliği", "Rules + PU + shape similarity", "birlesim", "scores_exp_mel84b_uclu/honest_none_4_kural_pu", ENS, "MEL-84"),
    ("u6", "Kural + PU + CNN", "Rules + PU + CNN", "birlesim", "scores_exp_mel85_uclu/honest_none_4_kural_pu", ENS, "MEL-85"),
    ("u1b", "Kural + PU + otomatik kodlayıcı", "Rules + PU + autoencoder", "birlesim", "scores_exp_mel86_uclu/honest_none_4_kural_pu", ENS, "MEL-86"),
    ("u7", "Kural + PU + çöküş modeli", "Rules + PU + crash model", "birlesim", "scores_exp_mel87_uclu/honest_none_4_kural_pu", ENS, "MEL-87"),
    ("e32c", "Kural + PU (kendi etiketler C)", "Rules + PU (own labels C)", "birlesim", "scores_exp_mel32c/honest_none_4_kural_pu", ENS, "MEL-32"),
    ("e88", "Kural + PU (birlikte sıçrama ağı)", "Rules + PU (co-surge network)", "birlesim", "scores_exp_mel88/honest_none_4_kural_pu", ENS, "MEL-88"),
    ("e32b", "Kural + PU (kendi etiketler B)", "Rules + PU (own labels B)", "birlesim", "scores_exp_mel32b/honest_none_4_kural_pu", ENS, "MEL-32"),
]


def paired(a: str, b: str, cases, any12, rng) -> dict:
    (aa, da), (ab, db) = per_case(a, cases, any12), per_case(b, cases, any12)
    c = aa.index.intersection(ab.index).intersection(da.index).intersection(db.index)
    sa, na, sb, nb = aa.loc[c, "sum"].values, aa.loc[c, "size"].values, ab.loc[c, "sum"].values, ab.loc[c, "size"].values
    xa, xb = da.loc[c, "detected"].values.astype(float), db.loc[c, "detected"].values.astype(float)
    idx = rng.integers(0, len(c), size=(N_BOOT, len(c)))
    dauc = sa[idx].sum(1) / na[idx].sum(1) - sb[idx].sum(1) / nb[idx].sum(1)
    drec = xa[idx].mean(1) - xb[idx].mean(1)
    sig = lambda x: bool(np.quantile(x, .025) > 0 or np.quantile(x, .975) < 0)  # noqa: E731
    return {"d_auc": sa.sum() / na.sum() - sb.sum() / nb.sum(), "d_auc_lo": np.quantile(dauc, .025),
            "d_auc_hi": np.quantile(dauc, .975), "d_auc_sig": sig(dauc), "d_rec": xa.mean() - xb.mean(),
            "d_rec_lo": np.quantile(drec, .025), "d_rec_hi": np.quantile(drec, .975), "d_rec_sig": sig(drec)}


def main() -> None:
    exact, core6, any12 = load_cases()
    peaks = peak_dates(exact)
    main_cases = exact[exact["start"].dt.year >= 2017]
    rng = np.random.default_rng(0)
    rows = []
    for key, tr, en, grp, path, ref, issue in MODELS:
        f = INTERIM / f"{path}.parquet"
        if not f.exists():
            print(f"  yok, atlandı: {path}")
            continue
        m = next(r for r in evaluate_file(f, exact, core6, any12, peaks) if r["period"] == "2017–2026")
        rows.append({"key": key, "tr": tr, "en": en, "group": grp, "issue": issue, "ref": ref.split("_", 3)[-1],
                     "auc": m["auc"], "rec": m["rec@20"], "rnd": m["rnd@20"], "prec10": m["prec@10"],
                     "n_cases": m["n_cases"], **paired(path, ref, main_cases, any12, rng)})
        print(f"  {key}: AUC {m['auc']:.3f}, yakalama {m['rec@20']:.3f}", flush=True)
    out = INTERIM / "results" / "alt_models.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"yazıldı: {out}")


if __name__ == "__main__":
    main()
