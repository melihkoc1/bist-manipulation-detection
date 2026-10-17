"""SPK vakalarından hisse × gün etiketleri üretir.

Her vaka için pozitif günler:
- Manipülasyon dönemi kararda yazıyorsa: [period_start, period_end]
- Yazmıyorsa: [ilk karar − N ay, ilk karar], N ∈ {3, 6, 12}

Üç varyant (`pos_3m`, `pos_6m`, `pos_12m`) ayrı sütunlarda tutulur; dönemi bilinen
vakalarda üçü de aynı dönemi verir. Tezde sonuçların pencere seçimine duyarlılığı
bu sütunlarla raporlanır.

Ana set dışında kalan vakalar (yalnızca çok hisseli kararlardan gelenler, Tier 3
piyasa tedbirleri) pozitif sayılmaz ama `ignore_*` maskesiyle işaretlenir: bu günler
ne pozitif ne de "temiz" kabul edilmeli, değerlendirmeden çıkarılmalıdır.
"""

import pandas as pd

WINDOWS_MONTHS = (3, 6, 12)


def case_windows(cases: pd.DataFrame, months: int) -> pd.DataFrame:
    """Her vaka için (ticker, case_id, start, end, known_period, core, tier) döndürür."""
    c = cases.copy()
    known = c["period_start"].notna() & c["period_end"].notna()
    c["start"] = c["period_start"].where(known, c["first_decision"] - pd.DateOffset(months=months))
    c["end"] = c["period_end"].where(known, c["first_decision"])
    c["known_period"] = known
    c["core"] = ~c["multi_stock_only"] & (c["best_tier"] <= 2)
    return c[["ticker", "case_id", "start", "end", "known_period", "core", "best_tier"]]


def build(dates: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    """`dates`: ticker, date (özellik tablosundaki tüm hisse-günler)."""
    out = dates[["ticker", "date"]].copy()
    for m in WINDOWS_MONTHS:
        w = case_windows(cases, m)
        merged = out.merge(w, on="ticker", how="inner")
        inside = merged[(merged["date"] >= merged["start"]) & (merged["date"] <= merged["end"])]
        core = inside[inside["core"]]
        pos = core.drop_duplicates(["ticker", "date"])[["ticker", "date", "case_id", "best_tier"]]
        pos = pos.rename(columns={"case_id": f"case_{m}m", "best_tier": f"tier_{m}m"})
        pos[f"pos_{m}m"] = 1
        ign = inside[~inside["core"]].drop_duplicates(["ticker", "date"])[["ticker", "date"]]
        ign[f"ignore_{m}m"] = 1
        out = out.merge(pos, on=["ticker", "date"], how="left").merge(ign, on=["ticker", "date"], how="left")
        out[f"pos_{m}m"] = out[f"pos_{m}m"].fillna(0).astype(int)
        # Hem ana set hem ana set dışı vakaya düşen gün pozitiftir
        out[f"ignore_{m}m"] = (out[f"ignore_{m}m"].fillna(0).astype(int) * (1 - out[f"pos_{m}m"]))
    # Dönemi kararda yazan vakalar: en kesin etiket
    w = case_windows(cases, 3)
    w = w[w["known_period"] & w["core"]]
    merged = out[["ticker", "date"]].merge(w, on="ticker")
    exact = merged[(merged["date"] >= merged["start"]) & (merged["date"] <= merged["end"])]
    out["pos_exact"] = out.set_index(["ticker", "date"]).index.isin(
        exact.set_index(["ticker", "date"]).index).astype(int)
    return out
