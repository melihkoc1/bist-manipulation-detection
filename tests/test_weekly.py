import numpy as np
import pandas as pd
import pytest

from bistmd.eval.weekly import auc_with_ci, case_detection, recall_lift_ci, to_weekly, week_labels


def _scores(n_tickers=10, n_days=20, hot=None):
    """hot: (ticker, ilk gün indeksi) → o günden itibaren en yüksek skor."""
    dates = pd.bdate_range("2021-01-04", periods=n_days)  # 4 hafta
    rows = [(f"T{i}", d, float(i)) for i in range(n_tickers) for d in dates]
    s = pd.DataFrame(rows, columns=["ticker", "date", "score"])
    if hot:
        t, i0 = hot
        s.loc[(s.ticker == t) & (s.date >= dates[i0]), "score"] = 100.0
    return s, dates


def test_weekly_ranks_and_pct():
    s, _ = _scores()
    wk = to_weekly(s)
    assert wk.groupby("week").size().eq(10).all()
    top = wk[wk["rank"] == 1]
    assert (top.ticker == "T9").all() and np.allclose(top.pct, 1.0)


def test_random_probability_formula():
    s, dates = _scores()
    wk = to_weekly(s)
    cases = pd.DataFrame({"case_id": ["c"], "ticker": ["T0"], "start": [dates[0]], "end": [dates[19]]})
    det = case_detection(wk, cases, k=2).iloc[0]
    # 4 hafta, her hafta 10 hisseden 2'si listede: 1 - 0.8^4
    assert det.n_weeks == 4
    assert det.p_random == pytest.approx(1 - 0.8 ** 4)
    assert not det.detected  # T0 her zaman en düşük skor


def test_short_window_overlap_and_lead():
    s, dates = _scores(hot=("T0", 7))  # 2. haftanın Çarşambası
    wk = to_weekly(s)
    # Dönem Çarşamba-Perşembe: tek hafta ile örtüşür (cuma listesi dışarıda kalmamalı)
    cases = pd.DataFrame({"case_id": ["c"], "ticker": ["T0"], "start": [dates[7]], "end": [dates[8]]})
    det = case_detection(wk, cases, k=1).iloc[0]
    assert det.n_weeks == 1 and det.detected
    assert det.p_random == pytest.approx(0.1)
    assert det.lead_days == (dates[9] - dates[7]).days  # ilk alarm o haftanın cuması


def test_auc_perfect_and_uninformative():
    s, dates = _scores(hot=("T0", 10))
    wk = to_weekly(s)
    exact = pd.DataFrame({"case_id": ["c"], "ticker": ["T0"], "start": [dates[10]], "end": [dates[19]]})
    lab = week_labels(wk, exact, exact)
    auc, lo, hi = auc_with_ci(lab, n_boot=50)
    # 2 pozitif (T0, 3-4. hafta, yüzdelik 1,0); 38 negatif. Negatiflerden ikisi (T9, 1-2. hafta)
    # da kendi haftasının zirvesinde (yüzdelik 1,0) → eşitlik yarım sayılır: (36 + 2·0,5) / 38
    assert auc == pytest.approx(37 / 38)
    rnd = to_weekly(s.assign(score=np.random.default_rng(0).random(len(s))))
    assert abs(auc_with_ci(week_labels(rnd, exact, exact), n_boot=10)[0] - 0.5) < 0.35
    # T0'nun skoru dönem dışında en düşük: yalnız dönem haftaları pozitif, diğer hafta(lar)ı belirsiz değil
    assert lab.loc[(lab.ticker == "T0") & (lab.week_end < dates[10]), "y"].eq(0).all()


def test_recall_lift():
    det = pd.DataFrame({"detected": [1, 1, 0, 0], "p_random": [0.1, 0.1, 0.1, 0.1]})
    r = recall_lift_ci(det, n_boot=200)
    assert r["recall"] == 0.5 and r["random"] == pytest.approx(0.1) and r["lift"] == pytest.approx(5.0)
