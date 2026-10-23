# Değerlendirme v2 — yorum

Sayılar `docs/sonuclar_v2.md` içinde (`scripts/evaluate_v2.py` ve `scripts/compare_v2.py` üretir,
her çalıştırmada yeniden yazılır). Bu dosya elle tutulan yorumdur; scriptler dokunmaz.

## Güncelleme (23.10.2026): kural + ML birleşik skoru

**Yöntem.**
- Her hafta modellerin sıra yüzdelikleri eşit ağırlıkla ortalanır (`scripts/ensemble_v2.py`).
- Ağırlıklar ve ana birleşim (kural + PU bagging) sonuçlara bakılmadan önceden belirlendi; test verisinde ayar yok.

**Sonuç (dürüst, 2017–2026, 123 vaka).** Kural + PU, en iyi genel model:

| | AUC | recall@20 (rastgele 0,23) | isabet@10 lift |
|---|---|---|---|
| Kural | 0,81 | 0,65 | 2,4× |
| PU bagging | 0,83 | 0,62 | 3,5× |
| **Kural + PU** | **0,85** | **0,67** | **3,4×** |

Eşleştirilmiş testler:
- Kural + PU, kuraldan AUC'de anlamlı biçimde iyi: +0,037 [+0,024, +0,049].
- Kural + PU, PU bagging'den de anlamlı biçimde iyi: +0,016 [+0,003, +0,030].
- Recall farkları (+2,4 ve +4,9 puan) anlamlı değil.
- Pratik anlamı: birleşim, kuralların yakalama oranını ve ML'in liste isabetini aynı anda veriyor.

Diğer birleşimler:
- Kural + Isolation Forest + PU: en yüksek AUC (0,86), ama recall biraz daha düşük (0,64).
- Kural + LightGBM: kural + PU'dan zayıf.

Dönemlere göre:
- 2012–2026 (184 vaka): kural + PU recall 0,71 (kural ile aynı), AUC 0,81 (kural 0,75), isabet 3,5× (kural 2,7×).
- 2022–2026: kural + PU isabeti 3,0× (kural 1,7×, PU 3,9×), recall 0,51 (kural 0,54, PU 0,46). Yani bu dönemde iki ucun arasında kalıyor.

## Güncelleme (23.10.2026): 2009–2015 bültenleri ve kapanış/VWAP özellikleri

**Ne değişti.**
- 2009–2015 SPK bültenleri eklendi (eski biçim: numaralı kararlar, hisse kodu yerine unvan, eski SPKn md. 47/I-A-2).
  - Ana set 335 → 413 vakaya çıktı.
  - Dönemi bilinen ve fiyatı olan vaka sayısı:
    - 2017–2026: 125 (önceki ana küme; dönemlerden hiçbiri değişmedi).
    - 2012–2016: 59 yeni vaka.
- Yeni özellikler:
  - Kapanışın gün içi ağırlıklı ortalamaya (VWAP) göre konumu.
  - Kural modeline bir "kapanış oyunu" kuralı (`0c_kural_vwap`). Eşik, etiketlere bakılmadan dağılımdan seçildi.
- Değerlendirme 2012–2026'ya genişletildi. Ana karşılaştırmalar önceki sürümle aynı vaka kümesi (2017–2026) üzerinde.

**Daha çok etiket ML'i anlamlı biçimde iyileştirdi.** Aynı 123 vaka üzerinde, VWAP'sız modellerle
(yalnızca etiket etkisi):
- LightGBM AUC +0,049 [+0,023, +0,079].
- PU bagging AUC +0,024 [+0,005, +0,046].
- İkisi de anlamlı. Recall@20 artışları (+5,7 ve +1,6 puan) anlamlı değil.

Önceki bulgu ("ML'in darboğazı etiket sayısı") doğrudan teyit edildi. Hindsight ile dürüst LightGBM
arasındaki AUC farkı da +0,067'den +0,032'ye düştü.

**ML artık kurallarla başa baş.**
- Önceki sürümde:
  - LightGBM kuralların anlamlı biçimde altındaydı.
  - PU bagging recall@20'de kuralların 8 puan gerisindeydi (anlamlı).
- Şimdi:
  - Hiçbir ML–kural farkı anlamlı değil. PU bagging: AUC +0,021, recall −2,4 puan.
  - ML'in haftalık ilk 10 isabeti belirgin biçimde daha yüksek: PU bagging 3,5×, kural 2,4× (eşleştirilmiş test yapılmadı).
  - En zayıf dönem olan 2022–2026'da isabet farkı en büyük: PU bagging 3,9×, kural 1,7×.

**VWAP özellikleri: tek başına güçlü, mevcut özelliklere katkısı küçük.**
- Tek değişkenli AUC 0,70–0,75. Bu, kapanış konumu ve hacim oranından yüksek.
- Model içindeki katkısı küçük:
  - Kural modeline eklenince AUC +0,007 (anlamlı ama küçük), recall −3,3 puan (anlamsız).
  - LightGBM ve PU bagging'de VWAP'lı ile VWAP'sız arasında anlamlı fark yok.
- Yorum: VWAP sinyalinin bilgisi, mevcut getiri / kapanış konumu özellikleriyle büyük ölçüde örtüşüyor.
- Tez için bu da bir bulgu. Günlük veride "kapanış oyunu" izi var, ama ek bilgi taşımıyor.

**2012–2016 (yeni değerlendirilebilen yıllar, 59 vaka).**
- Kurallar ve Isolation Forest en iyisi:
  - Kural: recall@20 0,81, rastgele 0,40.
  - Isolation Forest: AUC 0,75.
- Dürüst ML bu yıllarda zayıf (LightGBM lift 1,7, PU 1,5). Bunun nedeni, ilk yıllarda eğitime giren etiketin az olması.
- Bu dönemde rastgele taban da yüksek (0,40), çünkü vaka dönemleri daha uzun. Bu yüzden lift'ler düşük görünüyor.
- 2012–2026 genelinde kural lift'i 2,5 [2,2–2,8] (184 vaka).

**Tez soruları — güncel cevap.**
- Soru 1 (erken tespit): **evet.** 184 vaka ve 15 yıl üzerinde, tüm yöntemler rastgelenin açıkça üstünde.
- Soru 2 (PU learning): **kısmen evet, daha güçlü.** PU, gözetimliden AUC'de anlamlı biçimde iyi (+0,028 [+0,013, +0,044]).
  - PU artık kurallarla istatistiksel olarak eşit.
  - En isabetli haftalık listeyi veriyor.
- Soru 3 (habersiz hareket): **hayır** (değişmedi).
  - Habersiz hareket özellikleri etkisiz.
  - Tüm KAP özellikleri LightGBM'i anlamlı biçimde kötüleştiriyor (AUC −0,035).

**Sınırlılıklar.**
- 2017–2026 vakalarının yalnızca dönemi kararda yazanları değerlendirilebiliyor.
- Borsadan çıkmış bazı şirketlerin eski vakaları (ör. Petrol Ofisi, Latek) eşlenemedi ya da fiyatı yok.
- Hakkında 2009 öncesinde karar verilmiş vakalar, fiyat verisi 2010'da başladığı için dışarıda.

## İlk yorum (21.10.2026, 2016–2026 bültenleriyle)

**Soru 1 — Erken tespit: EVET, anlamlı.**
- Dönemi bilinen 125 vakada tüm yöntemler rastgeleyi açıkça geçiyor.
- En iyi yöntem (kural tabanlı):
  - Vakaların %65'ini haftalık ilk 20 listede yakalıyor (rastgele %23 → 2,8× [2,4–3,2]).
  - %64'ünü fiyat zirvesinden önce yakalıyor (rastgele %21).
- İlk alarm, manipülasyon başladıktan medyan 7–11 gün sonra.
- AUC 0,76–0,82.
- Etki 2022–2026'da zayıflıyor ama rastgelenin üstünde kalıyor (kural lift 2,6 [1,9–3,5]).

**Soru 2 — PU learning: KISMEN EVET.**
- Dürüst modda iki PU varyantı da gözetimli LightGBM'den anlamlı biçimde daha iyi sıralıyor (AUC +0,05 [+0,03, +0,07]).
- Recall farkı (+4 puan) anlamlı değil.
- Hindsight modunda (tüm etiketler) fark kapanıyor (LightGBM 0,82, PU 0,83–0,84).
- Yorum: PU, etiketlerin eksik olduğu gerçek kullanım koşulunda fayda sağlıyor. Bu, teorik beklentiyle tutarlı.

**ML ve kurallar: kurallar hâlâ en iyi recall'a sahip.**
- PU modelleri AUC'de kural tabanlı modele eşit (fark −0,007, anlamsız), ama recall@20'de 8 puan geride (anlamlı).
- LightGBM her iki ölçüte göre de kuralların anlamlı biçimde altında.
- ML'in avantajı haftalık ilk 10'un isabetinde (lift ~3,0×, kural 2,4×).

**Etiket bolluğu ML'i belirgin iyileştiriyor.**
- Aynı LightGBM, tüm etiketlerle (hindsight) eğitildiğinde AUC +0,067, recall +14,6 puan. İkisi de anlamlı.
- ML'in darboğazı model değil, eğitim anındaki etiket sayısı.

**Soru 3 — Habersiz hareket: HAYIR.**
- Ne "yalnızca habersiz hareket" ne "tüm KAP" özellikleri anlamlı bir iyileşme sağlıyor.

**Sınırlılıklar:**
- Sonuçlar yalnızca dönemi kararda yazan vakalar için geçerli (125/≈330). Bunlar muhtemelen daha belirgin ve kısa süreli olaylar.
- Pozitif haftaların yarısından fazlası 2019–2022'de.
