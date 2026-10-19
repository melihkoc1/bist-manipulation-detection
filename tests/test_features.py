import numpy as np
import pandas as pd
import pytest

from bistmd.features.price import ticker_features


def _fake_prices(n=300, seed=0):
    rng = np.random.default_rng(seed)
    close = 10 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    high = close * (1 + rng.uniform(0, 0.03, n))
    low = close * (1 - rng.uniform(0, 0.03, n))
    mcap = close * 1e8
    return pd.DataFrame({
        "ticker": "TEST", "date": pd.bdate_range("2020-01-01", periods=n),
        "close": close, "close_raw": close, "high_raw": high, "low_raw": low,
        "value_try": rng.lognormal(15, 1, n), "mcap_try": mcap, "float_mcap_try": mcap * 0.3,
        "free_float": 0.3, "xu100": 1000 * np.exp(np.cumsum(rng.normal(0, 0.01, n))), "usdtry": 7.0,
    })


@pytest.mark.parametrize("cut", [100, 180, 250])
def test_no_lookahead(cut):
    """t gününe kadar kesilmiş veriyle hesaplanan özellikler, tüm veriyle hesaplananla aynı olmalı."""
    p = _fake_prices()
    full = ticker_features(p).iloc[cut]
    truncated = ticker_features(p.iloc[: cut + 1]).iloc[cut]
    pd.testing.assert_series_equal(full, truncated, check_names=False)


def test_limit_up_streak():
    p = _fake_prices(80)
    for i in (70, 71, 72):  # üç gün üst üste tavan, günün en yükseğinden kapanış
        p.loc[i:, ["close", "close_raw"]] *= 1.10
        p.loc[i, "high_raw"] = p.loc[i, "close_raw"]
        p.loc[i + 1:, ["high_raw", "low_raw"]] *= 1.10
    f = ticker_features(p)
    assert f.loc[72, "limit_up_streak"] == 3
    assert f.loc[72, "limit_up_10"] >= 3


def test_value_ratio_excludes_today():
    p = _fake_prices(100)
    p.loc[99, "value_try"] = p["value_try"].iloc[:99].median() * 50
    f = ticker_features(p)
    assert f.loc[99, "value_ratio_60"] > 30


def test_kap_features_respect_effective_date():
    from bistmd.features.kap import ticker_kap_features

    dates = pd.Series(pd.bdate_range("2020-01-01", periods=30))
    ev = pd.DataFrame({"effective_date": [dates[10], dates[10], dates[25]],
                       "category": ["strong_news", "unusual_move", "strong_news"]})
    f = ticker_kap_features(dates, ev).set_index("date")
    assert f.loc[dates[9], "n_strong_news_5"] == 0          # olaydan önceki gün görünmez
    assert f.loc[dates[10], "n_strong_news_5"] == 1
    assert f.loc[dates[14], "n_strong_news_5"] == 1
    assert f.loc[dates[15], "n_strong_news_5"] == 0          # 5 işlem günü sonra pencereden çıkar
    assert f.loc[dates[10], "n_unusual_move_20"] == 1
    assert f.loc[dates[13], "days_since_strong_news"] == 3
    assert f.loc[dates[5], "days_since_strong_news"] == 250  # henüz hiç haber yok


def test_categorize_separates_price_reactive_from_news():
    from bistmd.features.kap import categorize

    subj = pd.Series(["Özel Durum Açıklaması (Genel)"] * 4 + ["Şirket Genel Bilgi Formu", "Yeni İş İlişkisi"])
    summ = pd.Series(["BİAŞ'da oluşan ağırlıklı ortalama fiyatın, pay başına net aktif değerin 2 katını aşması",
                      "Yönetim Kurulu Görev Dağılımı", "Savunma sanayi sözleşme imzalandı", "Genel Müdür Ataması",
                      None, None])
    assert categorize(subj, summ).tolist() == [
        "price_reactive", "governance_routine", "strong_news", "weak_news", "routine", "strong_news"]
