import pandas as pd

from bistmd.ingest.spk_bulletins import parse_name
from bistmd.labels.spk_bulletins import parse_bulletin_text, period_for_ticker

SAMPLE = """
SERMAYE PİYASASI KURULU BÜLTENİ 2019/67 12/12/2019
A. İZAHNAME / İHRAÇ BELGESİ ONAYLANAN SERMAYE PİYASASI ARAÇLARI
1. Borçlanma Araçları
B. SUÇ DUYURUSU, İDARİ PARA CEZASI İLE DİĞER YAPTIRIM VE TEDBİRLER
1. İdari Para Cezaları
a) Formet Çelik Kapı Sanayi ve Ticaret A.Ş. (FORMT) pay piyasasında 25.02.2019-01.03.2019 döneminde
gerçekleştirilen işlemler ile ilgili olarak yapılan inceleme sonucunda, aşağıdaki tabloda yer alan idari para
cezasının uygulanmasına karar verilmiştir.
IPC Uygulanan Şahıs
M******* Ç**** FORMT pay piyasasında gerçekleştirilen işlemler. VI-104.1 Sayılı Piyasa Bozucu Eylemler Tebliği
771.794,52
2. Suç Duyuruları
a) Asya Katılım Bankası A.Ş. (ASYAB) pay piyasasında 25.03.2014 tarihinde kamuya duyurulan özel durum
açıklaması öncesinde gerçekleştirilen işlemlerde 6362 sayılı SPKn'nun 106/1 maddesi
b) Halk Gayrimenkul Yatırım Ortaklığı A.Ş. (HLGYO) pay piyasasında 12.04.2019-03.05.2019 döneminde
gerçekleştirilen piyasa dolandırıcılığı niteliğindeki işlemler, SPKn 107/1 maddesi
3. Diğer Yaptırım, Tedbir ve İşlem Yasakları
a) Oylum Sınai Yatırımlar A.Ş. (OYLUM) pay piyasasında 02.03.2016-29.03.2016 döneminde gözlenen fiyat ve
miktar hareketlerinin incelenmesi sonucunda brüt takas uygulanmasına karar verilmiştir.
C. DİĞER BAŞVURU SONUÇLARI
1. Bir fon
"""


def _items():
    meta, items = parse_bulletin_text(SAMPLE)
    return meta, {(i["section"], i["item"]): i for i in items}


def test_meta():
    meta, _ = _items()
    assert meta == {"bulletin_year": 2019, "bulletin_no": 67, "bulletin_date": pd.Timestamp("2019-12-12")}


def test_fine_item():
    _, items = _items()
    it = items[("idari_para_cezasi", "a")]
    assert it["tickers"] == ["FORMT"]
    assert it["periods"]["FORMT"] == (pd.Timestamp("2019-02-25"), pd.Timestamp("2019-03-01"))
    assert it["category"] == "manipulation"
    assert it["total_amount_try"] == 771794.52
    assert "M*******" not in it["header"]  # kişi tablosu saklanmaz


def test_insider_is_separated():
    _, items = _items()
    assert items[("suc_duyurusu", "a")]["category"] == "insider"
    assert items[("suc_duyurusu", "b")]["category"] == "manipulation"


def test_market_measure():
    _, items = _items()
    assert items[("diger_tedbir", "a")]["category"] == "market_measure"


def test_section_stops_at_next_top_section():
    _, items = _items()
    assert len(items) == 4


def test_period_for_ticker_multi_stock():
    text = ("Componenta (COMDO) pay piyasasında 06.07.2015-10.08.2015 döneminde, Doğtaş (DGKLB) pay "
            "piyasasında 27.01.2015-09.02.2015 döneminde gerçekleştirilen işlemler")
    assert period_for_ticker(text, "DGKLB") == (pd.Timestamp("2015-01-27"), pd.Timestamp("2015-02-09"))
    assert period_for_ticker(text, "COMDO") == (pd.Timestamp("2015-07-06"), pd.Timestamp("2015-08-10"))


def test_standard_names():
    assert parse_name("2018-1") == (2018, 1)
    assert parse_name("2010_12") == (2010, 12)


def test_variant_names():
    assert parse_name("2024%2015") == (2024, 15)
    assert parse_name("20-2024") == (2024, 20)


def test_non_bulletin():
    assert parse_name("2022-2026 STRATEJİK PLAN") is None


def test_ticker_resolution():
    from bistmd.labels.tickers import prepare_universe, resolve

    u = prepare_universe(pd.DataFrame({
        "ticker": ["TRALT", "MEPET", "FORMT"],
        "title": ["TÜRK ALTIN İŞLETMELERİ A.Ş.", "MEPET METRO PETROL VE TESİSLERİ SANAYİ TİCARET A.Ş.",
                  "FORMET METAL VE CAM SANAYİ A.Ş."],
    }))
    assert resolve("FORMT", "", u) == ("FORMT", "listed")
    hdr = "Mepet Metro Petrol ve Tesisleri Sanayi Ticaret A.Ş. paylarında gerçekleştirilen işlemler"
    assert resolve(None, hdr, u) == ("MEPET", "by_name")
    assert resolve("XXXXX", "Bilinmeyen Şirket A.Ş. (XXXXX) pay piyasasında", u) == ("XXXXX", "unlisted")


OLD_SAMPLE = """
SERMAYE PİYASASI KURULU
2009/2
HAFTALIK BÜLTEN
       05/01/2009 – 09/01/2009

14. Yataş Yatağan Sanayi A.Ş. yönetim kurulu üyeleri hakkında SPKn'nun 47/A-6 maddesi kapsamında
Cumhuriyet Savcılığı'na suç duyurusunda bulunulmasına karar verilmiştir.
15. Boyasan Tekstil Sanayi ve Ticaret A.Ş. (Boyasan) hisse senedinin piyasasında 18.10.2005-31.10.2005 döneminde
gerçekleştirilen işlemlerin incelenmesi sonucunda;
A) 18.10.2005-31.10.2005 döneminde Boyasan hisse senedinde gerçekleştirilen SPKn’nun 47/I-A-2 maddesinde
tanımlanan suçun unsurlarını içeren fiilleri nedeniyle, M***** Ç**** hakkında Cumhuriyet Savcılığına suç
duyurusunda bulunulmasına, B) hakkında işlem yapma yasağı getirilmesine, karar verilmiştir.
16. MTEKS hisse senedinde 15.01.2009-26.02.2009 döneminde Sermaye Piyasası Kanunu (SPKn)’nun 47/I-A-1
maddesinde tanımlanan suçun unsurlarını içeren fiilleri nedeniyle Matlı Tekstil A.Ş. hisse senedi ile ilgili
suç duyurusunda bulunulmasına karar verilmiştir.
17. Kaplamin Ambalaj Sanayi ve Ticaret A.Ş. hisse senedinde 07-10.01.2008 tarihleri arasında
gerçekleştirilen SPKn. 47/1-(A)-2 maddesinde tanımlanan fiiller nedeniyle suç duyurusunda bulunulmasına karar verilmiştir.
"""


def test_old_format_items():
    from bistmd.labels.spk_bulletins import parse_old_bulletin_text
    meta, items = parse_old_bulletin_text(OLD_SAMPLE)
    assert meta["bulletin_year"] == 2009 and meta["bulletin_no"] == 2
    assert meta["bulletin_date"] == pd.Timestamp("2009-01-09")
    cats = {it["item"]: it["category"] for it in items}
    assert "14" not in cats  # hisse piyasası işlemi değil
    assert cats["15"] == "manipulation" and cats["16"] == "insider" and cats["17"] == "manipulation"
    boy = next(it for it in items if it["item"] == "15")
    assert boy["companies"] == ["Boyasan Tekstil Sanayi ve Ticaret A.Ş."]
    assert boy["period"] == (pd.Timestamp("2005-10-18"), pd.Timestamp("2005-10-31"))
    assert boy["section"] == "suc_duyurusu"
    kap = next(it for it in items if it["item"] == "17")
    assert kap["period"] == (pd.Timestamp("2008-01-07"), pd.Timestamp("2008-01-10"))


def test_strict_company_match():
    from bistmd.labels.tickers import match_company, prepare_universe
    u = prepare_universe(pd.DataFrame({
        "ticker": ["ATA", "SNPAM", "SONME", "TBORG"],
        "title": ["Ata Menkul Kıymetler Yatırım Ortaklığı A.Ş.", "Sönmez Pamuklu Sanayii A.Ş.",
                  "Sönmez Filament Sentetik İplik ve Elyaf Sanayi A.Ş.", "Türk Tuborg Bira ve Malt Sanayii A.Ş."]}))
    assert match_company("Metro Menkul Kıymetler Yatırım Ortaklığı A.Ş.", u) is None
    assert match_company("Sönmez Pamuklu Sanayi A.Ş.", u) == "SNPAM"
    assert match_company("Sönmez Filament Sentetik İplik ve Elyaf San. A.Ş.", u) == "SONME"
    assert match_company("Türk Tuborg Bira ve Malt Sanayi A.Ş.", u) == "TBORG"
