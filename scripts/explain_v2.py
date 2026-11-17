"""PU bagging için "neden şüpheli?" açıklamaları (MEL-14).

score_v2.py --mode honest ile aynı yıllık modeller aynı tohumla yeniden eğitilir ve LightGBM'in
yerleşik SHAP katkıları (`pred_contrib=True`, TreeSHAP) hesaplanır. Katkılar log-odds
ölçeğindedir; torbaların ortalaması alınır. (Skor torba olasılıklarının ortalaması olduğu için
log-odds toplamı skorla birebir aynı değil, sıralaması çok yakın; yeniden üretim kontrolü aşağıda.)

Açıklanan satırlar: her haftanın Kural + PU ve PU bagging ilk 50'sindeki hisse-haftalar; haftanın
skoru en yüksek günü (haftalık skor = günlük skorların en büyüğü). Ayrıca genel önem için her
yıldan rastgele 20.000 satır.

Kullanım: python scripts/explain_v2.py
Çıktı:
  data/interim/explain/pu_contrib.parquet   hisse-hafta × gösterge katkısı (site dışa aktarımı okur)
  docs/aciklamalar.md                       genel önem tabloları ve yeniden üretim kontrolü
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from run_experiment import load  # noqa: E402
from score_v2 import prepare, rounds  # noqa: E402

from bistmd.models.core import PUBagging  # noqa: E402
from bistmd.paths import INTERIM, ROOT  # noqa: E402

SCORES = INTERIM / "scores_v2"
OUT = INTERIM / "explain"
TOP = 50
SAMPLE = 20_000
LABELS = {
    'ret_1': 'Günlük getiri',
    'ret_5': '1 haftalık getiri',
    'ret_20': '1 aylık getiri',
    'ret_60': '3 aylık getiri',
    'vol_20': 'Günlük oynaklık (1 ay)',
    'ret_5_z': 'Haftalık getirinin olağan dışılığı',
    'ret_20_z': 'Aylık getirinin olağan dışılığı',
    'vol_ratio_20_60': 'Oynaklık artışı',
    'xu_ret_20': 'Piyasanın aylık getirisi',
    'excess_ret_5': 'Endeks üstü getiri (1 hafta)',
    'excess_ret_20': 'Endeks üstü getiri (1 ay)',
    'up_while_market_down_20': 'Piyasa düşerken sert yükseliş',
    'value_ratio_20': 'Günlük hacim / 1 ay normali',
    'value_ratio_60': 'Günlük hacim / 3 ay normali',
    'value_up_streak': 'Hacmin art arda arttığı gün',
    'value_ratio_5d_60': 'Haftalık hacim / 3 ay normali',
    'float_turnover': 'Halka açık devir (gün)',
    'float_turnover_5': 'Halka açık devir (hafta)',
    'float_turnover_ratio_60': 'Halka açık devir artışı',
    'close_loc': 'Gün içi tepede kapanış',
    'close_loc_5': 'Hafta boyu tepede kapanış',
    'limit_up': 'Tavan',
    'limit_up_streak': 'Art arda tavan',
    'limit_up_10': '10 günde tavan sayısı',
    'up_days_10': '10 günde yükselen gün',
    'close_vs_vwap': 'Kapanış / ortalama fiyat',
    'close_vs_vwap_5': 'Kapanış / ortalama fiyat (hafta)',
    'close_vs_vwap_5_z': 'Kapanış oyununun olağan dışılığı',
    'close_above_vwap_10': '10 günde ortalamanın üstünde kapanış',
    'drawdown_from_60_high': '3 aylık zirveden uzaklık',
    'dist_from_60_low': '3 aylık dipten yükseliş',
    'trading_gap_60': 'Uzun işlem arası (3 ay)',
}


def contrib(model: PUBagging, X: pd.DataFrame) -> np.ndarray:
    """Torba ortalaması SHAP katkıları: (n, gösterge + 1); son sütun taban değer."""
    return np.mean([m.booster_.predict(X[model.cols], pred_contrib=True) for m in model.models], axis=0)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df, cases = load(6)
    df = prepare(df, "none")
    df["week"] = df["date"].dt.to_period("W-FRI").astype(str)

    want = []
    for m in ("4_kural_pu", "3b_pu_bagging"):
        w = pd.read_parquet(SCORES / f"honest_none_{m}.parquet")
        want.append(w.loc[w["rank"] <= TOP, ["week", "ticker"]])
    want = pd.concat(want).drop_duplicates()
    stored = pd.read_parquet(SCORES / "honest_none_3b_pu_bagging.parquet")[["week", "ticker", "score"]]

    rows, glob = [], []
    t0 = time.time()
    rng = np.random.default_rng(0)
    for yr, train, y, score_mask in rounds(df, cases, "honest"):
        model = PUBagging().fit(df.loc[train], y[train])
        cols = model.cols
        year = df.loc[score_mask]
        cand = year.merge(want, on=["week", "ticker"])
        cand["score"] = model.score(cand)
        best = cand.loc[cand.groupby(["week", "ticker"])["score"].idxmax()].reset_index(drop=True)
        c = contrib(model, best)
        out = best[["week", "ticker", "date", "score"]].copy()
        out[cols] = c[:, :-1]
        out["_base"] = c[:, -1]
        out["year"] = yr
        rows.append(out)

        samp = year.iloc[rng.choice(len(year), size=min(SAMPLE, len(year)), replace=False)]
        g = np.abs(contrib(model, samp)[:, :-1]).mean(axis=0)
        glob.append(pd.Series(g, index=cols, name=yr))
        print(f"{yr}: {len(out):,} hisse-hafta açıklandı ({time.time() - t0:.0f}s)", flush=True)

    res = pd.concat(rows, ignore_index=True)
    res.to_parquet(OUT / "pu_contrib.parquet", index=False)

    # Yeniden üretim kontrolü: haftalık en yüksek günlük skor, kayıtlı PU skoruyla aynı mı?
    chk = res[["week", "ticker", "score"]].merge(stored, on=["week", "ticker"], suffixes=("", "_kayit"))
    diff = (chk["score"] - chk["score_kayit"]).abs()

    feats = [c for c in res.columns if c not in ("week", "ticker", "date", "score", "_base", "year")]
    gl = pd.concat(glob, axis=1).T
    share = gl.div(gl.sum(axis=1), axis=0)
    per = {"2012–2016": share.loc[2012:2016].mean(), "2017–2021": share.loc[2017:2021].mean(),
           "2022–2026": share.loc[2022:2026].mean(), "Tümü": share.mean()}
    tab = pd.DataFrame(per).sort_values("Tümü", ascending=False)
    top_abs = res[feats].abs()
    top_share = (top_abs.div(top_abs.sum(axis=1), axis=0)).mean().reindex(tab.index)
    tab["İlk 50 satırlarında"] = top_share
    # İlk 50'de göstergenin skoru artırdığı satır oranı (katkı > 0)
    tab["İlk 50'de yukarı itme %"] = (res[feats] > 0).mean().reindex(tab.index) * 100

    fmt = tab.copy()
    fmt.index = [f"{LABELS.get(i, i)} (`{i}`)" for i in fmt.index]
    for c in fmt.columns[:-1]:
        fmt[c] = (fmt[c] * 100).map(lambda v: f"%{v:.1f}")
    fmt[fmt.columns[-1]] = tab[tab.columns[-1]].map(lambda v: f"%{v:.0f}")
    text = [
        "# PU modelinin açıklamaları (SHAP)", "",
        "`scripts/explain_v2.py` üretir; yorum `docs/yorum_v2.md`.", "",
        "Dürüst yıllık PU bagging modelleri (15 torba LightGBM) aynı tohumla yeniden eğitildi; katkılar "
        "LightGBM'in yerleşik TreeSHAP'i ile log-odds ölçeğinde, torba ortalaması.", "",
        f"**Yeniden üretim kontrolü:** {len(chk):,} hisse-haftada yeniden eğitilen skor ile kayıtlı skor "
        f"arasındaki en büyük fark {diff.max():.2e} (ortalama {diff.mean():.2e}).", "",
        "## Genel önem: göstergenin ortalama |katkı| payı", "",
        "İlk dört sütun: her yıldan rastgele 20.000 hisse-gün. \"İlk 50 satırlarında\": haftalık ilk 50'ye "
        "giren hisse-haftaların en şüpheli günü. Son sütun: ilk 50'de göstergenin skoru yukarı ittiği satır oranı.", "",
        fmt.to_markdown(), "",
    ]
    (ROOT / "docs" / "aciklamalar.md").write_text("\n".join(text), encoding="utf-8")
    print("\n".join(text))


if __name__ == "__main__":
    main()
