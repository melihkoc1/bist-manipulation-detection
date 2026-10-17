"""Fiyat, hacim, likidite ve profil özellikleri (hisse × gün).

Altın kural: `t` günündeki her özellik yalnızca `t` günü kapanışına kadar (dahil) olan
veriyi kullanır. "Normal" seviyeyi ölçen hareketli pencereler `t` gününü dışarıda
bırakır (shift(1)), böylece bugünkü sıçrama kendi referansını şişirmez.
Bu kural tests/test_features.py içinde, verinin `t`'de kesilmiş haliyle karşılaştırılarak
test edilir.

Getiriler düzeltilmiş kapanıştan (`close`) hesaplanır; ham fiyatlar sermaye
işlemlerinde (bedelsiz, bölünme) sahte sıçramalar içerir.
"""

import numpy as np
import pandas as pd

LIMIT_UP_RET = 0.095  # BIST'te taban fiyat değişim sınırı genelde %10; yuvarlama payı


def _streak(flag: pd.Series) -> pd.Series:
    """Ardışık True sayısı (bugün dahil)."""
    groups = (~flag).cumsum()
    return flag.astype(int).groupby(groups).cumsum()


def ticker_features(p: pd.DataFrame) -> pd.DataFrame:
    """Tek hissenin tarih sıralı verisinden özellik tablosu üretir."""
    p = p.sort_values("date").reset_index(drop=True)
    # Kaynakta eksik değerler (None) bazı sütunları object tipine çeviriyor
    num = p.columns.difference(["ticker", "date"])
    p[num] = p[num].apply(pd.to_numeric, errors="coerce")
    f = pd.DataFrame({"ticker": p["ticker"], "date": p["date"]})

    logp = np.log(p["close"])
    r1 = logp.diff()
    f["ret_1"] = r1
    f["ret_5"] = logp.diff(5)
    f["ret_20"] = logp.diff(20)
    f["ret_60"] = logp.diff(60)

    vol60 = r1.shift(1).rolling(60, min_periods=40).std()
    f["vol_20"] = r1.rolling(20, min_periods=15).std()
    f["ret_5_z"] = f["ret_5"] / (vol60 * np.sqrt(5))
    f["ret_20_z"] = f["ret_20"] / (vol60 * np.sqrt(20))
    f["vol_ratio_20_60"] = f["vol_20"] / vol60

    # Endeksten ayrışma
    xu = np.log(p["xu100"])
    f["xu_ret_20"] = xu.diff(20)
    f["excess_ret_5"] = f["ret_5"] - xu.diff(5)
    f["excess_ret_20"] = f["ret_20"] - f["xu_ret_20"]
    f["up_while_market_down_20"] = ((f["ret_20"] > 0.2) & (f["xu_ret_20"] < 0)).astype(int)

    # Hacim (TL) anomalileri — referans dünü de içeren geçmiş pencere
    val = p["value_try"].where(p["value_try"] > 0)
    for w in (20, 60):
        f[f"value_ratio_{w}"] = val / val.shift(1).rolling(w, min_periods=w // 2).median()
    f["log_value"] = np.log1p(p["value_try"])
    f["value_up_streak"] = _streak(val.diff() > 0)
    f["value_ratio_5d_60"] = (val.rolling(5, min_periods=3).mean()
                              / val.shift(5).rolling(60, min_periods=30).median())

    # Halka açık kısma göre devir hızı (TL hacim / halka açık piyasa değeri)
    turnover = p["value_try"] / p["float_mcap_try"]
    f["float_turnover"] = turnover
    f["float_turnover_5"] = turnover.rolling(5, min_periods=3).sum()
    f["float_turnover_ratio_60"] = turnover / turnover.shift(1).rolling(60, min_periods=30).median()

    # Tavan serileri ve kapanış davranışı
    rng = (p["high_raw"] - p["low_raw"])
    close_loc = ((p["close_raw"] - p["low_raw"]) / rng).where(rng > 0, 0.5)
    limit_up = (r1 >= np.log1p(LIMIT_UP_RET)) & (p["close_raw"] >= p["high_raw"])
    f["close_loc"] = close_loc
    f["close_loc_5"] = close_loc.rolling(5, min_periods=3).mean()
    f["limit_up"] = limit_up.astype(int)
    f["limit_up_streak"] = _streak(limit_up)
    f["limit_up_10"] = limit_up.rolling(10, min_periods=1).sum()
    f["up_days_10"] = (r1 > 0).rolling(10, min_periods=5).sum()
    f["drawdown_from_60_high"] = p["close"] / p["close"].rolling(60, min_periods=20).max() - 1
    f["dist_from_60_low"] = p["close"] / p["close"].rolling(60, min_periods=20).min() - 1

    # Likidite ve profil
    f["amihud_60"] = np.log1p((r1.abs() / val * 1e6).rolling(60, min_periods=30).mean())
    f["log_mcap"] = np.log(p["mcap_try"])
    f["log_float_mcap"] = np.log(p["float_mcap_try"])
    f["free_float"] = p["free_float"]
    f["log_price"] = np.log(p["close_raw"])
    f["days_listed"] = np.arange(len(p))  # veri başlangıcından beri (2010 öncesi kesik)
    gap = p["date"].diff().dt.days
    f["trading_gap_60"] = (gap > 5).rolling(60, min_periods=1).sum()  # uzun işlem arası sayısı

    # Değeri USD'ye çevrilmiş piyasa değeri: TL enflasyonundan arındırılmış büyüklük
    f["log_mcap_usd"] = np.log(p["mcap_try"] / p["usdtry"])
    return f.replace([np.inf, -np.inf], np.nan)


def build(prices: pd.DataFrame) -> pd.DataFrame:
    parts = [ticker_features(g) for _, g in prices.groupby("ticker", sort=False)]
    return pd.concat(parts, ignore_index=True)
