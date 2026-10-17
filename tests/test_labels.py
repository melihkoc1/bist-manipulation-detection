import pandas as pd

from bistmd.labels.windows import build


def _cases():
    return pd.DataFrame([
        # dönemi bilinen ana set vakası
        {"ticker": "AAA", "case_id": "AAA-0", "first_decision": pd.Timestamp("2020-12-01"),
         "period_start": pd.Timestamp("2020-03-02"), "period_end": pd.Timestamp("2020-03-06"),
         "multi_stock_only": False, "best_tier": 1},
        # dönemi bilinmeyen vaka → karar öncesi pencere
        {"ticker": "BBB", "case_id": "BBB-0", "first_decision": pd.Timestamp("2020-06-30"),
         "period_start": pd.NaT, "period_end": pd.NaT, "multi_stock_only": False, "best_tier": 1},
        # sadece çok hisseli karar → pozitif değil, yok sayılır
        {"ticker": "CCC", "case_id": "CCC-0", "first_decision": pd.Timestamp("2020-06-30"),
         "period_start": pd.NaT, "period_end": pd.NaT, "multi_stock_only": True, "best_tier": 1},
    ])


def _dates():
    d = pd.bdate_range("2019-06-01", "2020-12-31")
    return pd.DataFrame([(t, x) for t in ("AAA", "BBB", "CCC") for x in d], columns=["ticker", "date"])


def test_known_period_ignores_window_length():
    lab = build(_dates(), _cases()).set_index(["ticker", "date"])
    a = lab.loc["AAA"]
    for m in (3, 6, 12):
        assert a[f"pos_{m}m"].sum() == 5
    assert a["pos_exact"].sum() == 5
    assert a.loc[pd.Timestamp("2020-03-09"), "pos_3m"] == 0


def test_unknown_period_uses_decision_window():
    lab = build(_dates(), _cases()).set_index(["ticker", "date"])
    b = lab.loc["BBB"]
    assert b["pos_3m"].sum() < b["pos_6m"].sum() < b["pos_12m"].sum()
    assert b.loc[pd.Timestamp("2020-07-01"), "pos_12m"] == 0  # karardan sonra pozitif değil
    assert b["pos_exact"].sum() == 0


def test_multi_stock_case_is_ignored_not_positive():
    lab = build(_dates(), _cases()).set_index(["ticker", "date"])
    c = lab.loc["CCC"]
    assert c["pos_6m"].sum() == 0
    assert c["ignore_6m"].sum() > 0
