"""KAP bildirimlerini konu + özet metnine göre içerik kategorilerine ayırır (kural tabanlı).

Neden gerekli: "Özel Durum Açıklaması (Genel)" konusu tek başına bildirimlerin ~%14'ünü
oluşturuyor ve içinde çok farklı şeyler var. Özellikle:
  - price_reactive: "BİAŞ'da oluşan ağırlıklı ortalama fiyatın, pay başına net aktif değerin
    X katını aşması" gibi açıklamalar fiyat artışının SONUCUDUR (zorunlu bildirim), haber değil.
    Bunları "haber" saymak, fiyatı en çok yükselen hisseleri "haberli" gösterir ve
    "habersiz hareket" sinyalini tersine çevirir.
  - governance_routine: görev dağılımı, bağımsız denetçi seçimi vb. fiyatı açıklamaz.

Kategoriler (kural sırası önemlidir, ilk eşleşen kazanır):
  price_reactive, business_news, corporate_action, capital_action, earnings_info,
  management_change, financing, legal, rating, buyback, investor_presentation,
  governance_routine, liquidity, periodic_stats, labor_minor, other

Gruplar (özellik üretimi için):
  strong_news = business_news + corporate_action + capital_action + earnings_info
  weak_news   = management_change + financing + legal + rating + buyback + investor_presentation
"""

import re

import pandas as pd

# (kategori, desen) — desenler Türkçe küçük harfe çevrilmiş metne uygulanır
SUMMARY_RULES: list[tuple[str, str]] = [
    ("price_reactive", r"net aktif değer|olağan\s?dışı fiyat|fiyat ve miktar hareket|borsa fiyat"),
    ("rumor", r"basında (çıkan|yer alan)|haber(ler)? hakkında|söylenti|sosyal medya|iddia"),
    ("governance_routine", r"esas sözleşme|ana sözleşme|fonun kullan|kullanımına ilişkin rapor|değerleme rapor|"
                           r"değerleme (şirket|kuruluş)|teminat|ipotek|kefalet"),
    ("rating", r"derecelendirme|kredi notu|rating"),
    ("buyback", r"pay (alım|satış) bildirim|hisse (alım|satış) bildirim"),
    ("financing", r"halka arz|satışa konu pay|sermaye artırımı yasağı|kredi|ihra[cç](?!at)|sermaye piyasası aracı|borçlanma"),
    ("liquidity", r"likidite sağla|piyasa yapıcı|fiyat istikrar"),
    ("periodic_stats", r"prim üretimi|yazılan prim|hasar|aylık (üretim|satış|trafik)|trafik sonuç|"
                       r"istatistik|yolcu"),
    ("labor_minor", r"toplu iş sözleşmesi|toplu sözleşme|grev|sendika"),
    ("legal", r"konkordato|müflis|iflas|yeniden yapılandır|yapılandırma|dava|mahkeme|soruşturma|vergi denetim|gümrük|ceza|haciz|icra (takip|dosya|işlem)|iptal davası|tahkim|vergi inceleme"),
    ("corporate_action", r"satma hakkı|girişim (sermayesi|yatırım)|rehin|pay (alınması|alımına)|birleşme|bölünme|devralma|devir|satın al|satın alım|pay alım teklifi|pay devri|hisse devri|"
                         r"iştirak|bağlı ortaklık (kuruluş|satış|alım|edin|pay)|ortaklık yapısı|ana ortak|hakim ortak|"
                         r"pay satışı|pay satın|stratejik ortak|ortak girişim|tasfiye|statü"),
    ("capital_action", r"sermaye (avans|artış|artır)|bedelsiz|bedelli|sermaye artır|sermaye azalt|kayıtlı sermaye|temettü|kâr payı|kar payı|"
                       r"kâr dağıt|kar dağıt|hisse bölün|pay bölün|nominal değer"),
    ("business_news", r"sözleşme|ihale|sipariş|anlaşma|protokol|iş ilişkisi|işbirliği|iş birliği|ortaklık anlaşma|"
                      r"lisans|ruhsat|patent|proje|yatırım (kararı|teşvik|planı)|tesis|fabrika|kapasite|üretime|"
                      r"ürün|ihracat|satış|alacak portföy|temlik|şube|enerji santral|maden|rezerv|arazi|gayrimenkul|"
                      r"teşvik belge|sertifika(?!sı ihracı)|onay|yeni (iş|pazar|ürün)|lansman|teslim|kontrat|iş alımı|"
                      r"kredi anlaşma|alım satım sözleşme|taşınmaz|inşaat|ges yatırım|yatırım işlem|kira bedeli|görüşme|alışveriş merkez|açılış|kiralama|kapanış|irtibat bürosu|marka|hat açıl|organizasyon"),
    ("financing", r"halka arz|eurobond|vdmk|finansman sağla|borçlanma|future flow|hazine işlem|borçlanma aracı|tahvil|bono|kira sertifikası|sukuk|varlığa dayalı|finansman bonosu|kredi|"
                  r"spk (başvuru|onay)|izahname|ihraç|halka arz|derecelendirme notu"),
    ("earnings_info", r"finansal tablo|bilanço|faaliyet raporu|net (dönem )?kâr|net (dönem )?zarar|ciro|satış gelir|"
                      r"gelir tablosu|ebitda|özet finansal|finansal sonuç|mali tablo|beklenti|"
                      r"geleceğe dönük|hedef|tahmin|performans|finansal rapor|çeyrek|dönem sonuç|operasyonel sonuç"),
    ("management_change", r"yönetim kurulu (üye|üyesi)?\s?(değişikli|ataması|istifa|başkan)|üye değişikli|üst (düzey )?yönetim|"
                          r"yönetici (ataması|değişikli)|görevden ayrıl|istifa|genel müdür|ataması|atanması|"
                          r"cfo|ayrılması|göreve|görevlendirme|yönetim değişikli|ceo|icra kurulu|atama|görev değişikli|işten ayrıl|organizasyon değişikli"),
    ("buyback", r"geri alınan pay|alım emri|geri alım|pay alım satım|hisse alım satım|pay alımı|hisse alımı|pay satımı"),
    ("investor_presentation", r"yatırımcı sunum|sunum|bilgilendirme toplantı|analist toplantı|roadshow|webcast"),
    ("governance_routine", r"görev dağılımı|görev taksimi|görev paylaşımı|bağımsız denetim|denetim (şirketi|kuruluşu)|"
                           r"yatırımcı ilişkileri|genel kurul|bağımsız yönetim|piyasa danışman|sorumluluk sigorta|"
                           r"kurumsal yönetim|komite|imza (yetki|sirkü)|esas sözleşme|politika|özel durumlar tebliği|"
                           r"güncelleme|bilgilendirme|ana sözleşme|ticaret sicil|adres|ünvan|unvan|temsil|"
                           r"yönetim kurulu|avusturya|seçimi|mali takvim|tazmin|kaydileştir|tasarruf sahiplerine|"
                           r"portföy yönetim ücret|ödenen|koronavirüs|covid|salgın|pandemi|özel durum açıklaması|"
                           r"henüz sonuçlanmamış|içsel bilgi"),
]

# Konusu zaten içeriği belirleyen bildirimler (özete bakmaya gerek yok)
SUBJECT_MAP: dict[str, str] = {
    "Olağan Dışı Fiyat ve Miktar Hareketleri": "unusual_move",
    "Haber ve Söylentilere İlişkin Açıklama": "rumor",
    "Finansal Rapor": "financial_report",
    "Pay Alım Satım Bildirimi": "insider_trade",
    "Pay Bazında Devre Kesici Bildirimi": "circuit_breaker",
    "Yeni İş İlişkisi": "business_news",
    "Finansal Duran Varlık Edinimi": "corporate_action",
    "Finansal Duran Varlık Satışı": "corporate_action",
    "Maddi Duran Varlık Alımı": "business_news",
    "Maddi Duran Varlık Satımı": "business_news",
    "İhale Süreci / Sonucu": "business_news",
    "Birleşme İşlemlerine İlişkin Bildirim": "corporate_action",
    "Bölünme İşlemlerine İlişkin Bildirim": "corporate_action",
    "Pay Alım Teklifi Yoluyla Pay Toplanmasına İlişkin Bildirim": "corporate_action",
    "Sermaye Artırımı - Azaltımı İşlemlerine İlişkin Bildirim": "capital_action",
    "Kayıtlı Sermaye Tavanı İşlemlerine İlişkin Bildirim": "capital_action",
    "Kar Payı Dağıtım İşlemlerine İlişkin Bildirim": "capital_action",
    "Geleceğe Dönük Değerlendirmeler": "earnings_info",
    "Değerleme Raporu": "earnings_info",
    "Ortaklık Aleyhine Dava Açılması veya Davaya İlişkin Gelişmeler": "legal",
    "Kredi Derecelendirmesi": "rating",
    "İlişkili Taraf İşlemleri": "business_news",
}
# Özete bakılan konular
SUMMARY_SUBJECTS = {"Özel Durum Açıklaması (Genel)", "Özel Durum Açıklaması", "Diğer"}

GROUPS = {
    "strong_news": ("business_news", "corporate_action", "capital_action", "earnings_info"),
    "weak_news": ("management_change", "financing", "legal", "rating", "buyback", "investor_presentation"),
}


# str.contains uyarı vermesin: tüm gruplar yakalamayan
SUMMARY_RULES = [(c, re.sub(r"\((?!\?)", "(?:", p)) for c, p in SUMMARY_RULES]


def tr_lower(s: pd.Series) -> pd.Series:
    """Türkçe uyumlu küçük harf (İ→i, I→ı) ve rakamları '#' ile değiştirme."""
    return (s.fillna("").str.replace("İ", "i", regex=False).str.replace("I", "ı", regex=False)
            .str.lower().str.replace(r"\d+", "#", regex=True))


def classify_summaries(summary: pd.Series) -> pd.Series:
    text = tr_lower(summary)
    out = pd.Series("other", index=summary.index, dtype="object")
    todo = pd.Series(True, index=summary.index) & (text != "")
    for cat, pat in SUMMARY_RULES:
        hit = todo & text.str.contains(pat, regex=True)
        out[hit] = cat
        todo &= ~hit
    return out


def classify(subject: pd.Series, summary: pd.Series) -> pd.Series:
    """Her bildirim için içerik kategorisi."""
    out = subject.map(SUBJECT_MAP)
    needs_summary = out.isna() & subject.isin(SUMMARY_SUBJECTS)
    if needs_summary.any():
        out[needs_summary] = classify_summaries(summary[needs_summary])
    return out.fillna("routine")


def group_of(category: str) -> str:
    for g, cats in GROUPS.items():
        if category in cats:
            return g
    return category
