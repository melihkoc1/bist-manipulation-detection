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

---

## 5. Ek (18.10.2026): Yıllık yeniden eğitim

Her değerlendirme yılı için model, o yılın başına kadarki veriyle ve o tarihe kadar SPK'nın
açıkladığı vakalarla yeniden eğitildi (eğitim pozitifleri: ≤2021 13.855 → ≤2025 29.576 hisse-gün).
Profil özellikleri çıkarılmış yapılandırma; 6 aylık pencere.

| Model | Test recall@20 (statik → yıllık) | İleriye dönük recall@20 (statik → yıllık) | İleriye dönük prec@10 (yıllık) |
|---|---|---|---|
| 0a Kural tabanlı | 0,44 → 0,44 | 0,47 → 0,47 | 0,051 |
| 2 LightGBM | 0,36 → **0,46** [0,35–0,57] | 0,42 → 0,40 | 0,078 |
| 3a PU ağırlıklı | 0,42 → 0,40 | 0,43 → 0,42 | 0,076 |
| 3b PU bagging | 0,38 → 0,39 | 0,43 → 0,40 | 0,070 |
| 2 LightGBM — ham profil | — | 0,27 (yıllık) | 0,038 |

**B7 — Yeniden eğitim tabloyu değiştirmiyor.** Yıllık yeniden eğitim LightGBM'i testte kural
tabanlı modelin seviyesine çıkarıyor (0,46 vs 0,44) ama genel resim aynı: ML modelleri recall'da
kurallarla **eşit**, precision'da ~1,5 kat **daha iyi** (0,07–0,08 vs 0,05). "İlk test ML'e haksızlık
ediyordu" hipotezi büyük ölçüde desteklenmedi.

**B8 — Profil ezberi yeniden eğitimle düzelmiyor.** Ham profil özellikleriyle yıllık eğitilen
LightGBM yine çöküyor (ileriye dönük 0,27). B3 bulgusu sağlam.

**B9 — KAP özellikleri mevcut haliyle hafif zarar veriyor (Soru 3).** Yıllık eğitimde KAP
özellikleri çıkarıldığında recall ve precision tutarlı biçimde biraz **artıyor** (ör. LightGBM
ileriye dönük prec@10: 0,078 → 0,103; PU bagging recall@20: 0,40 → 0,45). Farklar güven
aralıkları içinde, ama yön tutarlı: kaba bildirim sayıları gürültü ekliyor. Soru 3'ün anlamlı
test edilmesi için bildirimlerin içerik bazında sınıflandırılması gerekiyor.

---

## 6. Ek (19.10.2026): KAP içerik sınıflandırması ve tez sorusu 3 ("habersiz hareket")

İlk KAP özellikleri hatalıydı: fiyat artışının sonucu olan zorunlu bildirimler ("fiyat, net aktif
değerin X katını aştı", ~%10 hacim) haber sayılıyordu (bkz. `docs/validation_kap.md`, güvenilirlik
%93, n=60). Özellikler içeriğe göre yeniden üretildi ve dört KAP kümesi, yıllık yeniden eğitimle
(6 aylık pencere, profil özellikleri çıkarılmış) karşılaştırıldı. Değerler val+test+ileriye dönük
dönemlerin ortalaması, 4 ML modeli.

| KAP özellik kümesi | recall@20 (ort.) | precision@10 (ort.) |
|---|---:|---:|
| KAP yok (yalnızca fiyat/hacim/likidite) | 0,392 | 0,093 |
| Yalnızca "habersiz hareket" (4 özellik) | **0,409** | 0,092 |
| Yalnızca "olağan dışı hareket" sayaçları | 0,374 | 0,088 |
| Tüm KAP özellikleri (19) | 0,375 | 0,084 |

Eşleştirilmiş fark (KAP kümesi − KAP yok; 36 model×dönem×k hücresi): habersiz hareket recall
+0,007 (17 hücre artan, 12 azalan), precision −0,0004; tüm KAP recall −0,019, precision −0,005.

**B10 — Tez sorusu 3 cevabı: "habersiz hareket" özellikleri ölçülebilir ek katkı sağlamıyor.**
Fark sıfırdan ayırt edilemiyor (güven aralıkları ±0,12; bu örneklem büyüklüğüyle ancak ≥10 puanlık
farklar tespit edilebilir). Tüm KAP özelliklerinin eklenmesi hafifçe zarar veriyor.

**Tanımlayıcı bulgular (model dışı):**
- Fiyatı güçlü yükselen günlerde (ret_20_z > 2), habersiz olanların manipülasyon oranı %2,02,
  haberli olanların %1,76 → 1,15 kat (yön beklenen yönde, etki küçük).
- Hareketli günlerde (ret_20_z > 1,5 veya hacim oranı > 3), Borsa'nın istediği "olağan dışı fiyat
  ve miktar hareketi" açıklaması olanların manipülasyon oranı %1,92, olmayanların %0,74 (2,6 kat).
  Ama bu bilgi modele ek başarı getirmedi; açıklama zaten fiyat/hacim hareketinin sonucu olduğu için
  fiyat-hacim özellikleriyle büyük ölçüde örtüşüyor olabilir (test edilmedi).
- Hareketli günlerde güçlü haber olan/olmayan oranları neredeyse eşit (%0,84 vs %0,95): pompalanan
  hisselerde de haber akışı sürüyor. BIST'te manipülasyonlara sıklıkla bahane haber eşlik ediyor
  olabilir (kanıtlanmadı; yalnızca olası açıklama).
- Tüm KAP kümesinde LightGBM kazancının %33'ü KAP özelliklerinden geliyordu (en çok "son güçlü
  haberden beri gün" ve "finansal rapor sayısı"). Bunlar şirketin bildirim aktivitesini, yani
  büyüklük/kimlik göstergesini temsil ediyor olabilir; B3'teki profil ezberinin KAP versiyonu.

**Teknik not:** `n_capital_action_60` sayacı %44 oranında dolu; içeriğinin büyük kısmı temettü
bildirimleri. Bedelsiz sermaye artırımını ayrı ölçmek için daha ince bir kural gerekiyor (yapılmadı).
Bu sayaç ilk sürümde hatayla tamamen sıfırdı; düzeltildi (`tests/test_features.py`).
