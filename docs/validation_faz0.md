# Faz 0 — Etiket Çıkarımının Elle Doğrulanması

**Tarih:** 17.10.2026
**Yöntem:** Ana setten (fiyatlı, çok hisseli olmayan vakalar) yıllara dengeli, rastgele
50 vaka seçildi (`random_state=42`, yıl başına ≤5). Her vakanın çıkarılan bilgileri
(hisse kodu, karar türü, dönem) bülten metniyle karşılaştırıldı.
Örneklem: `data/interim/validation/sample50.parquet`.

## Sonuç

| Ölçüt | Sonuç |
|---|---|
| Hisse kodu ve "bu hissede manipülasyon kararı var" bilgisi doğru | **47 / 50 (%94)** |
| Dönem bilgisi çıkarılmış vakalarda dönem doğru | 15 / 16 (1 vakada bitiş tarihi kaymış) |
| Vaka birleştirme hatası (ayrı olaylar tek vakaya) | 2 / 50 |

## Hatalar ve yapılan düzeltmeler

| # | Vaka | Sorun | Düzeltme |
|---|---|---|---|
| 35 | GARAN | Karar hisseye değil, hisseye dayalı **varanta** ait | "varant / dayanak varlıklı" geçen kalemler `warrant` kategorisine alınıp dışlandı |
| 22 | ANELE | Md. 104 cezası, ancak "özel durum açıklaması öncesi" işlemler → içeriden bilgiye yakın | Açıklama öncesi işlemler 107/1 yoksa `insider` sayıldı |
| 48 | TERA | API kaydı "muhtelif pay piyasaları" → belirli bir hisse değil | "Muhtelif" geçen API kayıtları çok hisseli kabul edildi |
| 4, 20 | KCHOL, BNTAS | Tek günlük olaylarda ("22.02.2017 tarihinde") dönem alınmıyordu | Tek gün kalıbı eklendi |
| 20, 23 | BNTAS, GEREL | Farklı yıllardaki ayrı olaylar tek vakada birleşmişti | Dönemleri bilinen ve örtüşmeyen kararlar ayrı vakaya bölünüyor |

Düzeltmeler sonrası ana set: 345 → **335 vaka** (Tier 1: 255, dönemi bilinen: 108).

## Gözlemler (tez için)

- **Manipülasyon türleri çeşitli:** İşlem bazlı (107/1), bilgi bazlı / sosyal medya
  (107/2, ör. Telegram, Twitter paylaşımları), KAP açıklamaları üzerinden (GEREL 2018).
  Bilgi bazlı vakalar ayrı bir alt grup olarak analiz edilebilir.
- **Büyük hisseler de var** (KCHOL, TCELL, VESBE, KORDS): bunlar tek günlük, muhtemelen
  kapanış seansı ya da emir bazlı olaylar. Pompala-boşalt profiline uymuyor; piyasa
  değerine göre alt grup analizi yapılmalı.
- **Etiket gecikmesi:** Karar tarihi ile manipülasyon dönemi arasında 6 ay – 3 yıl fark
  görülüyor (ör. DENTA: işlemler 2013, karar 2016). Zaman bölmesinde dikkate alınmalı.
- Bu doğrulama **kesinlik (precision)** ölçer. SPK'nın karar verdiği ama ayrıştırıcının
  kaçırdığı vakalar (recall) ayrıca, rastgele seçilen bültenlerin tamamı okunarak ölçülmeli.
