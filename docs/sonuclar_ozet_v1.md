# İlk Model Sonuçları (v1) — Özet ve Yorum

**Tarih:** 18.10.2026 · **Veri:** 648 hisse, 2012–2026, 1,59 milyon hisse-gün, KAP 2010–2026 tam
**Protokol:** Eğitim 2012–2021 (dürüst mod: yalnızca 2021 sonuna kadar açıklanmış SPK vakaları
pozitif), doğrulama 2022, test 2023–24, ileriye dönük 2025–26. Model 2021 sonunda dondurulur.
**Senaryo:** Analist her hafta modelin en şüpheli gördüğü k hisseye bakar.
Ayrıntılı tablolar: `docs/sonuclar_w{3,6,12}*.md`.

## 1. Ana tablo (6 aylık pencere, haftalık ilk 20 liste)

| Model | Test recall@20 | İleriye dönük recall@20 | İleriye dönük prec@10 |
|---|---:|---:|---:|
| 0a Kural tabanlı | **0,44** [0,33–0,56] | **0,47** [0,33–0,58] | 0,051 |
| 0b Basit skor | 0,38 | 0,47 | 0,049 |
| 1 Isolation Forest | 0,31 | 0,32 | 0,079 |
| 2 LightGBM (ham profil) | 0,38 | 0,22 | 0,034 |
| 2 LightGBM (profil yok) | 0,36 | 0,42 | 0,066 |
| 3a PU ağırlıklı (profil yok) | 0,42 | 0,43 | **0,072** |
| 3b PU bagging (profil yok) | 0,38 | 0,43 | 0,069 |

Rastgele seçimin precision'ı (pozitif hisse-hafta oranı): ~0,03. Vaka sayısı: test 72, ileriye dönük 60.
Köşeli parantez: %95 bootstrap güven aralığı.

## 2. Bulgular

**B1 — Erken tespit mümkün (Soru 1).** Haftalık 20 hisselik listeyle vakaların ~%40–47'si,
manipülasyon penceresi içinde yakalanıyor. Alarmların %80–95'i fiyat zirvesinden **önce**.
Dönemi bilinen vakalarda ilk alarm, dönem başlangıcından medyan 10–20 gün sonra.

**B2 — Basit kurallar güçlü bir rakip.** Hiçbir ML modeli recall'da kural tabanlı modeli
istatistiksel olarak anlamlı biçimde geçemedi (güven aralıkları örtüşüyor). ML modellerinin
avantajı precision'da: ilk 10 listede ~1,4 kat daha isabetli (0,072 vs 0,051).

**B3 — Aşırı öğrenme: model "hangi hisse"yi öğreniyordu.** İlk LightGBM'in kazancının %53'ü
halka açıklık, piyasa değeri ve sığlık gibi yavaş değişen profil özelliklerinden geliyordu.
Eğitim pozitifleri yalnızca 147 hisseden geldiği için model, manipülasyonun zamanını değil
eğitim dönemindeki manipüle edilmiş hisselerin kimliğini öğrendi; 2023 sonrası değişen hisse
evreninde çöktü (ileriye dönük recall 0,22). Profil özellikleri çıkarılınca 0,42'ye yükseldi.
Kesitsel sıraya çevirmek (0,27) yeterli olmadı.

**B4 — PU learning (Soru 2): küçük ama tutarlı avantaj, anlamlı değil.** Profil özellikleri
çıkarıldığında PU varyantları test ve ileriye dönük dönemde gözetimli LightGBM'e eşit ya da
biraz üstün (test: 0,42 vs 0,36). Vaka sayısı (60–72) bu farkı anlamlı kılmak için yetersiz.

**B5 — KAP / habersiz hareket özellikleri (Soru 3): mevcut haliyle net katkı yok.** KAP
özellikleri çıkarıldığında sonuçlar tutarlı yönde değişmiyor. Muhtemel neden: "Özel Durum
Açıklaması (Genel)" konusu çok geniş (bedelsiz duyurusundan yönetim değişikliğine kadar her şey);
"önemli haber" tanımı fazla kaba. Bildirim özetinin içeriğe göre sınıflandırılması gerekiyor.

**B6 — Pencere duyarlılığı.** 12 aylık pencerede recall daha yüksek (daha uzun yakalama
süresi), 3 aylıkta düşük. Sıralama (kural ≈ PU > gözetimli) pencereden bağımsız değil;
tezde üç pencere birlikte raporlanmalı.

## 3. Sınırlılıklar

- Precision bir **alt sınırdır**: listedeki etiketsiz hisselerin bir kısmı yakalanmamış ya da
  henüz kararı çıkmamış manipülasyon olabilir (özellikle 2025–26).
- Güven aralıkları geniş (±0,12): model farklarının çoğu istatistiksel olarak ayırt edilemiyor.
- Hiperparametreler ayarlanmadı; tüm ML modelleri varsayılan ayarlarla eğitildi.

## 4. Sonraki adımlar

1. **Yürüyen eğitim (walk-forward):** Gerçek bir sistem her yıl yeniden eğitilir. Test için
   ≤2022, ileriye dönük için ≤2024 verisiyle eğitmek daha gerçekçi ve muhtemelen daha iyi.
2. **KAP bildirimlerinin içerik sınıflandırması** (özet metni üzerinden): Soru 3'ün doğru
   cevaplanması için gerekli.
3. **Kural + ML birleşimi:** Kural tabanlı skorun yüksek recall'u ile ML'in precision'ı.
4. Doğrulama dönemiyle sınırlı hiperparametre ayarı; ticker bazlı (GroupKFold) erken durdurma.
5. Kaçırılan vakaların ve en yüksek skorlu etiketsiz hisselerin vaka analizi.
