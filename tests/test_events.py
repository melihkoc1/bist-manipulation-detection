import pandas as pd

from bistmd.labels.events import build_cases
from bistmd.labels.spk_bulletins import classify, extract_periods


def _item(header, articles=(), section="idari_para_cezasi"):
    return {"header": header, "articles": list(articles), "section": section, "mentions_trading_ban": False}


def test_warrant_is_excluded():
    h = "Türkiye Garanti Bankası AŞ (GARAN) payına dayalı GABAB alım varantı piyasasında işlemler"
    assert classify(_item(h, ["104"])) == "warrant"


def test_disclosure_related_104_is_insider():
    h = "Anel Elektrik (ANELE) pay piyasasında özel durum açıklamasının öncesinde ve sonrasında işlemler"
    assert classify(_item(h, ["104"])) == "insider"


def test_single_day_period():
    s, e = extract_periods("(TCELL) ve (KCHOL) pay piyasasında 22.02.2017 tarihinde gerçekleştirilen işlemler")
    assert s == e == pd.Timestamp("2017-02-22")


def _dec(date, start=None, end=None):
    return {"ticker": "GEREL", "decision_date": pd.Timestamp(date), "tier": 1, "decision_type": "idari_para_cezasi",
            "period_start": pd.Timestamp(start) if start else pd.NaT,
            "period_end": pd.Timestamp(end) if end else pd.NaT, "multi_stock": False}


def test_disjoint_periods_split_cases():
    d = pd.DataFrame([_dec("2020-11-26", "2020-06-01", "2020-06-30"), _dec("2021-09-01", "2021-07-01", "2021-07-10")])
    assert len(build_cases(d)) == 2


def test_close_decisions_without_periods_merge():
    d = pd.DataFrame([_dec("2020-01-10"), _dec("2020-09-01")])
    assert len(build_cases(d)) == 1


def test_short_period_forms():
    ts = pd.Timestamp
    assert extract_periods("Kaplamin hisse senedinde 07-10.01.2008 döneminde") == (ts("2008-01-07"), ts("2008-01-10"))
    assert extract_periods("hisse senedinde 12.01-21.02.2011 dönemlerinde") == (ts("2011-01-12"), ts("2011-02-21"))
    # Tam yazım bozulmamalı
    assert extract_periods("18.10.2005-31.10.2005 döneminde") == (ts("2005-10-18"), ts("2005-10-31"))
