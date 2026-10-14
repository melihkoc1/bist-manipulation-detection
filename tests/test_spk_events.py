import pandas as pd

from bistmd.labels.spk_events import _is_market_abuse, extract_period, extract_tickers


def test_ticker_before_pay():
    assert extract_tickers("CANTE pay piyasasında gerçekleştirilen piyasa bozucu eylemler.") == ["CANTE"]


def test_ticker_in_parentheses():
    text = "Başkent Doğalgaz Dağıtım GYO AŞ (BASGZ) pay piyasasında gerçekleştirilen işlemler"
    assert extract_tickers(text) == ["BASGZ"]


def test_stopwords_are_not_tickers():
    assert extract_tickers("6362 sayılı SPKn kapsamında BİST pay piyasası") == []


def test_period_extraction():
    start, end = extract_period("KRSTL payında 01.03.2023-15.05.2023 döneminde yapılan işlemler")
    assert start == pd.Timestamp("2023-03-01")
    assert end == pd.Timestamp("2023-05-15")


def test_no_period():
    assert extract_period("TCELL pay piyasasında gerçekleştirilen işlemler.") == (None, None)


def test_market_abuse_by_article():
    assert _is_market_abuse(" VI-104.1 sayılı Piyasa Bozucu Eylemler Tebliği Md.6/1 ", None)


def test_unrelated_violation():
    assert not _is_market_abuse("Pay satış bilgi formu ilan edilmeksizin satış", "Karar no 1.104 TL")


def test_ticker_before_capitalized_pay():
    assert extract_tickers("PEKGY Pay Piyasasında Gerçekleştirilen Eylemler") == ["PEKGY"]


def test_turkish_abbreviations_are_not_tickers():
    assert extract_tickers("BİAŞ pay piyasasında") == []
    assert extract_tickers("İPC Uygulanan Şahıs (İPC)") == []
