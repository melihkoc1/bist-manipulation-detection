import pandas as pd

from bistmd.db import _explode_tickers, effective_dates

# Cuma 01.03.2019, sonraki işlem günü Pazartesi 04.03.2019
DAYS = pd.DatetimeIndex(["2019-02-28", "2019-03-01", "2019-03-04"])


def test_before_close_is_same_day():
    s = effective_dates(pd.Series(pd.to_datetime(["2019-03-01 17:59:59"])), DAYS)
    assert s.iloc[0] == pd.Timestamp("2019-03-01")


def test_after_close_is_next_trading_day():
    s = effective_dates(pd.Series(pd.to_datetime(["2019-03-01 18:00:00"])), DAYS)
    assert s.iloc[0] == pd.Timestamp("2019-03-04")  # hafta sonu atlanır


def test_weekend_is_next_trading_day():
    s = effective_dates(pd.Series(pd.to_datetime(["2019-03-02 10:00:00"])), DAYS)
    assert s.iloc[0] == pd.Timestamp("2019-03-04")


def test_beyond_calendar_is_nat():
    s = effective_dates(pd.Series(pd.to_datetime(["2019-03-04 19:00:00"])), DAYS)
    assert pd.isna(s.iloc[0])


def test_explode_tickers():
    k = pd.DataFrame({"disclosure_id": [1, 2, 3], "tickers": ["GARAN, TGB", None, "FORMT"]})
    out = _explode_tickers(k)
    assert sorted(out["ticker"]) == ["FORMT", "GARAN", "TGB"]
