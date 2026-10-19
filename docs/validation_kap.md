# KAP Bildirim İçerik Sınıflandırmasının Doğrulanması

**Tarih:** 19.10.2026 · **Kod:** `src/bistmd/features/kap_content.py`
**Veri:** "Özel Durum Açıklaması (Genel)" konulu 106.560 hisse-bildirim (2010–2026). Bu konu, tüm
bildirimlerin en kalabalık ve en heterojen grubu; konusu zaten içeriği belirleyen bildirimler
(finansal rapor, yeni iş ilişkisi, vb.) doğrudan konudan sınıflandırıldı.

## Neden gerekli?

İlk modelde bu konunun tamamı "önemli haber" sayılmıştı. İçeriğe bakınca bildirimlerin
~%10'unun şu tür olduğu görüldü: *"BİAŞ'da oluşan ağırlıklı ortalama fiyatın, pay başına net
aktif değerin 2 katını aşması"*. Bu, yatırım ortaklıklarının fiyat yükselince **zorunlu olarak**
yaptığı bir bildirimdir: fiyat artışının **sonucudur**, haber değildir. Haber sayıldığında en
çok yükselen hisseler "haberli" görünüyor ve "habersiz hareket" sinyali ters çalışıyordu.
Ek olarak ~%14'ü yönetişim rutini (görev dağılımı, bağımsız denetçi seçimi vb.).

## Yöntem

Sıralı Türkçe regex kuralları (ilk eşleşen kazanır). Kategoriler: `price_reactive`,
`business_news`, `corporate_action`, `capital_action`, `earnings_info`, `management_change`,
`financing`, `legal`, `rating`, `buyback`, `investor_presentation`, `governance_routine`,
`liquidity`, `periodic_stats`, `labor_minor`, `other`.
Özellik üretiminde gruplar: **güçlü haber** (iş, kurumsal işlem, sermaye işlemi, kâr/sonuç),
**zayıf haber** (yönetim değişikliği, finansman, dava, derecelendirme, geri alım, sunum),
**fiyat-tepkisel**, geri kalanı rutin. LLM kullanılmadı (API anahtarı yok).

**Kapsam:** özetlerin %81,1'i bir kategoriye atandı (%18,9 `other`; bunun 6,1 puanı özeti boş
bildirim). Kalan, uzun kuyruklu kendine özgü açıklamalar.

## Doğrulama (elle)

Benzersiz özetlerden rastgele örnekler tek tek okunarak, atanan **grubun** (güçlü / zayıf /
fiyat-tepkisel / rutin) doğru olup olmadığına karar verildi.

| Örneklem | n | Doğru | Doğruluk |
|---|---:|---:|---:|
| 1. tur (kural geliştirme sırasında; `seed=7`) | 100 | 87 | %87 |
| 2. tur (1. turdaki hatalar düzeltildikten sonra, **görülmemiş** özetler; `seed=11`) | 60 | 56 | **%93** (Wilson %95 GA: %84–97) |

Örneklem dosyaları: `data/interim/kap_validation_sample*.csv`.

**1. turda bulunan ve düzeltilen hata türleri:** Türkçe ek yüzünden eşleşmeme ("ihracına":
ç→c); "ana/esas sözleşme" değişikliğinin "sözleşme" kelimesiyle iş haberi sayılması; değerleme
raporlarının kâr haberi sayılması; "icra kurulu"nun hukuki sayılması; halka arz sonuçlarının
kâr haberi sayılması.
**2. turda kalan hatalar** (4/60; sonradan düzeltildi, yeni örneklemle ölçülmedi): teminat/ipotek
tablosu, değerleme şirketi seçimi, halka arz yasağı bildirimi, derecelendirme sözleşmesi.

## Sınırlılıklar

- İki turun sonrasındaki kural düzeltmeleri (4 hata) bağımsız bir örneklemde doğrulanmadı.
- %19 `other` rutin kabul ediliyor; bunun bir kısmı gerçek haber olabilir.
- Doğrulayıcı tek kişi (model); ikinci bir değerlendirici (kullanıcı) ile uyum ölçülmedi.
- Kategoriler anahtar kelimeye dayalı; "sözleşme imzalandı" ile "sözleşme feshedildi" ayırt edilmiyor.
