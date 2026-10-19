import pandas as pd
import pytest

from bistmd.features.kap_content import classify_summaries, group_of


@pytest.mark.parametrize("text,expected", [
    ("BİAŞ'da oluşan ağırlıklı ortalama fiyatın, pay başına net aktif değerin 2 katını aşması", "price_reactive"),
    ("Olağandışı fiyat ve miktar hareketleri hk.", "price_reactive"),
    ("Yönetim Kurulu Görev Dağılımı", "governance_routine"),
    ("Savunma sanayi alanında sözleşme imzalanmıştır", "business_news"),
    ("Bedelsiz Sermaye Artırımı Hk.", "capital_action"),
    ("İcra Kurulu'na üye ataması hakkında", "management_change"),
    ("2. Çeyrek 2023 Finansal ve Operasyonel Sonuçları", "earnings_info"),
    ("Sermaye piyasası aracı ihracına ilişkin Yönetim Kurulu Kararı", "financing"),  # ihracına: ç→c
    ("Şirket Ana Sözleşmesinde değişiklik", "governance_routine"),                  # 'sözleşme' haber değil
    ("Halka Arz Sonuçları", "financing"),
    ("Dünya Bankası'ndan Temin Edilen Krediye İlişkin Sözleşme", "financing"),
    ("Kurumsal Yönetim Derecelendirme Sözleşmesi İmzalanması", "rating"),
    ("Basında yer alan haberler hakkında", "rumor"),
    ("", "other"),
])
def test_classification(text, expected):
    assert classify_summaries(pd.Series([text])).iloc[0] == expected


def test_groups():
    assert group_of("business_news") == "strong_news"
    assert group_of("management_change") == "weak_news"
    assert group_of("price_reactive") == "price_reactive"
