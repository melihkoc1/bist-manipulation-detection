"""Deney karşılaştırması: bir deney klasöründeki skorları ana skorlarla (scores_v2) karşılaştırır.

Rapor: 2017–2026 ve 2012–2026 için AUC, recall@20 (rastgele taban), ilk 10 isabeti; ayrıca aynı
vakalarda eşli bootstrap farkları. Hiçbir belgeyi değiştirmez (yalnızca ekrana yazar).

Kullanım: python scripts/exp_compare.py scores_exp_spk [--ensemble]
  --ensemble: deney klasöründeki 3b_pu_bagging ile 0a_kural'dan 4_kural_pu birleşimini üretir.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from compare_v2 import N_BOOT, per_case  # noqa: E402
from ensemble_v2 import combine  # noqa: E402
from evaluate_v2 import SCORES, evaluate_file, load_cases, peak_dates  # noqa: E402

from bistmd.paths import INTERIM  # noqa: E402

MODELS = ["2_lightgbm", "3b_pu_bagging", "4_kural_pu"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("exp_dir")
    ap.add_argument("--ensemble", action="store_true")
    args = ap.parse_args()
    exp = INTERIM / args.exp_dir
    if args.ensemble:
        parts = [pd.read_parquet(SCORES / "honest_none_0a_kural.parquet"), pd.read_parquet(exp / "honest_none_3b_pu_bagging.parquet")]
        combine(parts).to_parquet(exp / "honest_none_4_kural_pu.parquet", index=False)

    exact, core6, any12 = load_cases()
    peaks = peak_dates(exact)
    rows = []
    for m in MODELS:
        for tag, d in (("ana", SCORES), ("deney", exp)):
            p = d / f"honest_none_{m}.parquet"
            if p.exists():
                for r in evaluate_file(p, exact, core6, any12, peaks):
                    if r["period"] in ("2017–2026", "2012–2026"):
                        rows.append({"model": m, "skor": tag, **r})
    t = pd.DataFrame(rows)
    cols = ["model", "period", "skor", "auc", "rec@20", "rnd@20", "pre_peak@20", "prec@10", "base@10", "n_cases"]
    print(t[cols].sort_values(["period", "model", "skor"]).to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    main_cases = exact[exact["start"].dt.year >= 2017]
    rng = np.random.default_rng(0)
    print("\nEşli bootstrap (deney − ana), 2017–2026:")
    for m in MODELS:
        a, b = f"{args.exp_dir}/honest_none_{m}", f"honest_none_{m}"
        if not (INTERIM / f"{a}.parquet").exists():
            continue
        (auc_a, det_a), (auc_b, det_b) = per_case(a, main_cases, any12), per_case(b, main_cases, any12)
        cases = auc_a.index.intersection(auc_b.index).intersection(det_a.index).intersection(det_b.index)
        sa, na = auc_a.loc[cases, "sum"].to_numpy(), auc_a.loc[cases, "size"].to_numpy()
        sb, nb = auc_b.loc[cases, "sum"].to_numpy(), auc_b.loc[cases, "size"].to_numpy()
        da, db = det_a.loc[cases, "detected"].to_numpy(float), det_b.loc[cases, "detected"].to_numpy(float)
        idx = rng.integers(0, len(cases), size=(N_BOOT, len(cases)))
        d_auc = sa[idx].sum(1) / na[idx].sum(1) - sb[idx].sum(1) / nb[idx].sum(1)
        d_rec = da[idx].mean(1) - db[idx].mean(1)
        sig = lambda x: "anlamlı" if np.quantile(x, .025) > 0 or np.quantile(x, .975) < 0 else "anlamsız"  # noqa: E731
        print(f"  {m}: AUC {sa.sum() / na.sum() - sb.sum() / nb.sum():+.3f} "
              f"[{np.quantile(d_auc, .025):+.3f}, {np.quantile(d_auc, .975):+.3f}] {sig(d_auc)}; "
              f"recall@20 {da.mean() - db.mean():+.3f} [{np.quantile(d_rec, .025):+.3f}, {np.quantile(d_rec, .975):+.3f}] {sig(d_rec)} "
              f"({len(cases)} vaka)")


if __name__ == "__main__":
    main()
