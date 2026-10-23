"""Kural + ML birleşik skoru: haftalık sıra yüzdeliklerinin ortalaması.

Kurallar daha çok vaka yakalıyor, ML'in haftalık ilk 10'u daha isabetli; iki skoru birleştirmek
ikisinin güçlü yanını almayı dener. Ağırlıklar sonuçlara bakılmadan eşit (1/n) seçildi; test
verisinde ayarlanmadı. Skor ölçekleri farklı olduğu için ham skorlar değil, hafta içi yüzdelikler
(1 = haftanın en şüphelisi) ortalanır.

Önkoşul: python scripts/score_v2.py --mode honest
Kullanım: python scripts/ensemble_v2.py
Çıktı:    data/interim/scores_v2/honest_none_4_*.parquet
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from evaluate_v2 import SCORES  # noqa: E402

# Ana birleşim (önceden belirlendi): kural + PU bagging. Diğerleri ikincil.
ENSEMBLES = {
    "4_kural_pu": ["0a_kural", "3b_pu_bagging"],
    "4_kural_lgbm": ["0a_kural", "2_lightgbm"],
    "4_kural_iforest_pu": ["0a_kural", "1_iforest", "3b_pu_bagging"],
}


def combine(parts: list[pd.DataFrame]) -> pd.DataFrame:
    """Aynı hafta × hisse satırlarında yüzdeliklerin ortalaması; sıra ve yüzdelik yeniden hesaplanır."""
    key = ["week", "ticker"]
    m = parts[0][key + ["pct", "week_start", "week_end"]].rename(columns={"pct": "p0"})
    for i, p in enumerate(parts[1:], 1):
        m = m.merge(p[key + ["pct"]].rename(columns={"pct": f"p{i}"}), on=key, how="inner")
    m["score"] = m[[f"p{i}" for i in range(len(parts))]].mean(axis=1)
    m["n_week"] = m.groupby("week")["ticker"].transform("size")
    m["rank"] = m.groupby("week")["score"].rank(ascending=False, method="first")
    m["pct"] = 1 - (m["rank"] - 1) / m["n_week"]
    return m[["week", "ticker", "score", "n_week", "rank", "pct", "week_start", "week_end"]]


def main(mode: str = "honest", kap: str = "none") -> None:
    for name, members in ENSEMBLES.items():
        parts = [pd.read_parquet(SCORES / f"{mode}_{kap}_{m}.parquet") for m in members]
        out = combine(parts)
        out.to_parquet(SCORES / f"{mode}_{kap}_{name}.parquet", index=False)
        print(f"{name}: {len(out):,} hisse-hafta ({' + '.join(members)})")


if __name__ == "__main__":
    main()
