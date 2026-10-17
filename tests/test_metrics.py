import numpy as np
import pandas as pd

from bistmd.eval.metrics import bootstrap_ci, event_metrics, precision_at_k, weekly_alerts


def _scores():
    dates = pd.bdate_range("2021-01-04", periods=20)  # 4 hafta
    rows = []
    for d in dates:
        rows += [("AAA", d, 0.1), ("BBB", d, 0.5), ("CCC", d, 0.2)]
    s = pd.DataFrame(rows, columns=["ticker", "date", "score"])
    s.loc[(s.ticker == "AAA") & (s.date >= dates[10]), "score"] = 0.9  # 3. haftadan itibaren şüpheli
    return s, dates


def test_weekly_top1():
    s, dates = _scores()
    a = weekly_alerts(s, k=1)
    assert a.groupby("week").size().max() == 1
    assert a.sort_values("week")["ticker"].tolist() == ["BBB", "BBB", "AAA", "AAA"]


def test_event_detection_and_lead():
    s, dates = _scores()
    a = weekly_alerts(s, k=1)
    cases = pd.DataFrame([{"case_id": "AAA-0", "ticker": "AAA", "start": dates[8], "end": dates[19],
                           "known_period": True}])
    m = event_metrics(a, cases).iloc[0]
    assert m["detected"]
    assert m["first_alert"] == dates[14]  # 3. haftanın cuması
    assert m["lead_days_from_start"] == (dates[14] - dates[8]).days


def test_precision_at_k():
    s, dates = _scores()
    a = weekly_alerts(s, k=1)
    lab = s[["ticker", "date"]].copy()
    lab["pos"] = ((lab.ticker == "AAA") & (lab.date >= dates[10])).astype(int)
    assert precision_at_k(a, lab, "pos", None) == 0.5


def test_bootstrap_ci_contains_mean():
    lo, hi = bootstrap_ci(np.array([1, 0, 1, 1, 0, 1, 0, 1]))
    assert lo <= 0.625 <= hi
