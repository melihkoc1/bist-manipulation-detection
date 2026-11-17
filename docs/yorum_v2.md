# Değerlendirme v2 — yorum

Sayılar `docs/sonuclar_v2.md` içinde (`scripts/evaluate_v2.py` ve `scripts/compare_v2.py` üretir,
her çalıştırmada yeniden yazılır). Bu dosya elle tutulan yorumdur; scriptler dokunmaz.

## "Neden şüpheli?" açıklamaları — SHAP (17.11.2026, Linear MEL-14)

Tablolar: [aciklamalar.md](aciklamalar.md) (`scripts/explain_v2.py`). Dürüst yıllık PU bagging
modelleri aynı tohumla yeniden eğitildi ve LightGBM'in yerleşik TreeSHAP'iyle (ek paket yok) her
göstergenin katkısı hesaplandı. Haftalık ilk 50'ye giren 52.594 hisse-hafta açıklandı.

**Yeniden üretim:** yeniden eğitilen skorlar kayıtlı skorlarla birebir aynı (en büyük fark 0).
Açıklamalar, değerlendirmede kullanılan modellerin kendisine ait.

**Model en çok neye bakıyor?** (rastgele hisse-günlerde ortalama |katkı| payı, 2012–2026)

| Gösterge | Pay |
|---|---|
| Halka açık payların haftalık devir hızı | %20,7 |
| 3 aylık dipten yükseliş | %13,4 |
| 3 aylık getiri | %5,2 |
| Halka açık payların günlük devir hızı | %5,1 |
| Son 10 günde ortalama fiyatın üstünde kapanış | %4,9 |

- İlk iki gösterge tek başına modelin üçte birini açıklıyor ve üç dönemde de (2012–16, 2017–21,
  2022–26) ilk iki sıra aynı. Model zaman içinde başka bir şeye kaymıyor.
- Düz anlatım: PU modeli "halka açık payları çok hızlı el değiştiren ve dibinden sert kalkmış hisse"
  örüntüsünü arıyor. Bu, pompala-boşalt anlatımıyla birebir örtüşüyor.
- Tavan göstergeleri neredeyse hiç kullanılmıyor (%0–2): devir hızı ve dipten yükseliş aynı bilgiyi
  zaten taşıyor.
- Piyasanın aylık getirisi 2022–26'da daha önemli (%3 → %7): model, genel yükseliş dönemlerinde
  hisseyi piyasaya göre değerlendirmeyi öğrenmiş (2022 zayıflığıyla tutarlı, bkz. sağlamlık testleri).

**Kurallar ile PU neden birbirini tamamlıyor?** İlk 50 satırlarında PU'nun en büyük katkılı
göstergesi yalnızca %4,5 oranında altı kural göstergesinden biri; kural göstergeleri PU'nun toplam
katkısının yalnızca %16'sı. Kurallar "normaline göre artış" (oran) ölçerken PU devir hızının ve
yükselişin **düzeyine** bakıyor. İki yöntem farklı bilgi kullandığı için birleşimleri ikisinden de
iyi (AUC 0,85).

**Sitede:** Zaman makinesi ve hisse sayfasındaki "Neden şüpheli?" paneli artık kural göstergelerinin
altında "Öğrenen model (PU) en çok neye baktı?" bölümünü gösteriyor: skoru en çok artıran 5 ve en çok
azaltan 2 gösterge, o günkü değerleriyle. Sınır: katkılar göstergeleri birlikte değerlendirir; tek bir
katkı sezgiye ters görünebilir (ör. yüksek hacim bir hafta skoru azaltabilir, çünkü diğer göstergeler
zaten aynı bilgiyi taşıyor). Kural + PU skorunun yalnızca öğrenen yarısını açıklar.

## Boş alarm incelemesi (17.11.2026, Linear MEL-16)

Tablolar: [bos_alarmlar.md](bos_alarmlar.md) (`scripts/false_alarms.py`). Kural + PU, 2017–2026,
haftalık ilk 10. Aynı hissenin ≤4 hafta arayla gelen alarm haftaları tek "alarm dönemi" sayıldı:
2393 dönem, bunların 2316'sı (%97) ana set SPK vakasına değmiyor. Şirket adları bilerek yazılmadı.

**1. Veri hatası yok.** Boş alarmların hiçbirinde son 20 günde günlük fiyat sınırını aşan (|getiri|
> %25) bir sıçrama yok. Yani liste, düzeltilmemiş bölünme/bedelsiz gibi veri hatalarıyla dolmuyor.

**2. Boş alarmlar da gerçekten olağan dışı hareketler.** Rastgele hisse-haftalarla karşılaştırma:

| | İsabet | Boş alarm | Rastgele hisse-hafta |
|---|---|---|---|
| Önceki 60 günde yükseliş (medyan) | %62 | %60 | %12 |
| Borsa "olağan dışı hareket" açıklaması istedi | %43 | %32 | %5 |
| Sonradan pompa-boşalt şekli (≥%50 çıkış, ≥%40 düşüş) | %40 | %33 | %5 |

Boş alarmlar fiyat davranışı bakımından isabetlere çok benziyor ve rastgeleden çok farklı. Model
"spekülatif hareket" yakalıyor; SPK bunların yalnızca bir kısmını cezalandırıyor ya da henüz
cezalandırmadı. Dolayısıyla ilk 10 isabet oranı (%10) gerçek başarının **alt sınırı**.

**3. Model hisse kimliğini ezberlemiyor.** Boş alarmların %57'si başka bir zamanda SPK vakası olan
hisselerde; rastgele hisse-haftalarda da bu oran %55. Alarm, vakanın öncesine/sonrasına da eşit
dağılıyor (%43 vs %42 "vaka alarmdan sonra"). SPK geçmişi denemesindeki (MEL-8) sorun ana modelde yok.

**4. Elle inceleme: 30 dönemlik rastgele örnek** (SPK kaydı hiç olmayan hisseler, 2017–2024; sabit
tohum). Her dönemin fiyat yolu ve KAP başlıkları tek tek okundu:

| Tür | Dönem |
|---|---|
| Somut bir şirket olayı olmadan sert yükseliş, ardından ≥%35 düşüş (pompa-boşalt örüntüsüne benziyor) | 14 |
| Somut şirket olayıyla açıklanabilir hareket (varlık satışı, geri alım, birleşme, sermaye artırımı, ihale/yeni iş) | 9 |
| Yeni halka arz sonrası fiyat oluşumu | 3 |
| Kalıcı yükseliş (yeniden değerleme / pandemi oynaklığı), çöküş yok | 3 |
| Çok düşük halka açıklıklı büyük şirkette sığ hareket | 1 |
| Veri hatası | 0 |

Yaklaşık yarısı SPK kararı olmasa da manipülasyon vakalarına benzeyen örüntüde; ancak SPK kararı
olmadan bunlara "manipülasyon" denemez. Kalanın büyük kısmı habere dayalı ya da yeni halka arz
hareketi. Sınır: "özel durum açıklaması" başlıklı bildirimlerin içeriği okunmadı; sınıflandırma
başlıklara ve fiyat yoluna dayanıyor.

**Çıkarımlar.**
- Habere dayalı hareketler boş alarmların önemli kısmı, ama KAP içerik göstergeleri modele daha önce
  katkı vermemişti (tez sorusu 3). "Somut şirket olayı" oranı isabetlerde de benzer (%45 vs %42), yani
  bu bilgi isabeti boş alarmdan ayırmıyor. Yeni bir KAP göstergesi denemesi bu yüzden öncelikli değil.
- Yeni halka arzlar ayrı bir boş alarm kaynağı; ileride "halka arzdan beri geçen gün" etkisine bakılabilir.
- SPK kararı olmayan pompa-boşalt benzeri dönemler, ileride kullanıcıyla birlikte yazılacak kendi
  ölçütlerimizle etiketleme fikrini (MEL-10) destekliyor.

## Sağlamlık testleri (17.11.2026, Linear MEL-15)

Tablolar: [saglamlik.md](saglamlik.md) (`scripts/robustness.py`). Dürüst skorlar, 2012–2026, 184 vaka.

**1. Liste uzunluğu (k).** Kural + PU her k'da rastgeleyi anlamlı biçimde geçiyor (GA'ların alt sınırı
hep 1'in üstünde). 2017–2026:

| k | 5 | 10 | 20 | 30 | 50 | 100 |
|---|---|---|---|---|---|---|
| Yakalama (rastgele) | 0,40 (0,07) | 0,58 (0,13) | 0,67 (0,23) | 0,73 (0,32) | 0,80 (0,45) | 0,94 (0,67) |
| Lift | 5,9× | 4,6× | 2,9× | 2,3× | 1,8× | 1,4× |

- Liste kısaldıkça sistemin rastgeleye üstünlüğü artıyor: en tepedeki 5 hisse en isabetli kısım.
- Kural + PU, k ≤ 10'da kurallardan da PU'dan da belirgin iyi (k = 10: 0,58 vs 0,49 / 0,46).
- k = 20 seçimi sonuçları en iyi gösteren nokta değil, orta bir nokta.

**2. Yıllar.** Lift 15 yılın 12'sinde güven aralığıyla rastgelenin üstünde. Zayıf yıllar:
- **2012–2013** (lift 1,2× ve 1,6×, GA 1'i içeriyor): ilk dürüst modeller çok az geçmiş vakayla
  eğitildi; ayrıca bu yılların vakaları uzun süreli (2012'de rastgele bile %72 yakalıyor).
- **2022** (1,6×, GA [0,9–2,4]): Borsa İstanbul'un çok güçlü yükseldiği yıl. Birçok hisse aynı
  anda yükseldiği için manipüle edilen hisseler ayrışmıyor (KONYA vakasıyla tutarlı).
- **2020** (2,0×): pandemi dalgalanması; yine anlamlı ama ortalamanın altında.
- En güçlü yıllar 2017–2018, 2021, 2023, 2025 (3,6–5,6×).

**3. Şirket büyüklüğü** (dönem başındaki piyasa değeri, o yılın medyanına oranla; 3 eşit grup;
179 vaka, 5 vakada piyasa değeri yok). Lift küçük/orta/büyük hisselerde 2,6× / 2,5× / 2,7×.
Sistem yalnızca küçük, sığ hisselerde çalışan bir şey değil. Küçük hisselerde yakalama oranı daha
yüksek (%80) ama rastgele taban da daha yüksek.

**4. Vaka süresi** (en önemli bulgu):

| Süre | Vaka | Yakalama | Rastgele | Lift |
|---|---|---|---|---|
| Kısa (≤45 gün) | 124 | 0,65 | 0,16 | 4,1× |
| Orta (46–120) | 40 | 0,78 | 0,44 | 1,8× |
| Uzun (>120) | 20 | 0,95 | 0,79 | 1,2× |

- Vakaların üçte ikisi kısa ve sistemin asıl değeri orada (4,1×).
- Uzun vakaları rastgele liste de neredeyse her zaman "yakalıyor". Bu, ilk değerlendirmenin
  (v1) neden yanıltıcı olduğunu sayılarla gösteriyor: uzun pencerelerde başarı oranı tek başına
  bir şey söylemez.
- Uzun vakalarda PU bagging rastgeleden ayırt edilemiyor (1,1×, GA [0,8–1,3]).

**Sonuç.** Ana bulgu (rastgeleden ~3 kat iyi) liste uzunluğu, yıl, şirket büyüklüğü ve vaka
süresi kesitlerinde ayakta kalıyor. Zayıf noktalar açıkça belli: piyasa genelinde güçlü yükseliş
yılları (2022) ve uzun süren, yavaş manipülasyonlar.

## Deneme (17.11.2026): birleşim ağırlıklarını geçmişten öğrenmek — kazanç yok (Linear MEL-12)

> Bu deneyin kodu depoya alınmadı. Ana birleşim eşit ağırlıklı kalıyor.

**Soru.** Ana birleşimde (kural + PU) ağırlıklar sonuçlara bakılmadan eşit seçildi. Ağırlıkları
veriden öğrenmek daha iyi olur mu?

**Yöntem (dürüst).**
- Her Y yılı için ağırlıklar yalnızca Y−1 sonuna kadar açıklanmış, dönemi bilinen vakalar ve
  Y'den önceki haftalar üzerinde seçildi; Y yılı bu ağırlıklarla puanlandı.
- Izgara araması (0,1 adım), hedef: haftalık AUC. Geçmişte 10'dan az vaka varsa eşit ağırlık.
- Üç varyant: kural + PU; kural + PU + LightGBM; kural + Isolation Forest + PU.

**Seçilen ağırlıklar.** Kural + PU için 2017'den sonra her yıl yaklaşık 0,3 / 0,7 (PU ağırlıklı).
LightGBM eklenince ona hiç ağırlık verilmedi (0,0). Isolation Forest varyantında yaklaşık
0,2 / 0,4 / 0,4.

**Sonuç** (2017–2026, 123 vaka, eşli bootstrap, fark = öğrenilmiş − eşit ağırlıklı kural + PU):

| Varyant | AUC | recall@20 | AUC farkı [%95 GA] | recall farkı [%95 GA] |
|---|---|---|---|---|
| Eşit ağırlık (ana) | 0,849 | 0,67 | — | — |
| Kural + PU, öğrenilmiş | 0,850 | 0,68 | +0,000 [−0,005, +0,005] | +0,008 [−0,016, +0,041] |
| Kural + PU + LightGBM, öğrenilmiş | 0,850 | 0,68 | +0,000 [−0,005, +0,005] | +0,008 [−0,016, +0,041] |
| Kural + IForest + PU, öğrenilmiş | 0,856 | 0,67 | +0,007 [−0,003, +0,019] | +0,000 [−0,041, +0,049] |

**Yorum.** Hiçbir fark anlamlı değil. Eşit ağırlık, öğrenilen ağırlıklara çok yakın bir sonuç
veriyor; bu, birleşimin sonuçlara göre ayarlanmadan seçilmiş olmasının bir maliyeti olmadığını
gösteriyor. Ana model eşit ağırlıklı kural + PU olarak kalıyor (daha basit ve önceden kayıtlı).

## Deneme (17.11.2026): hissenin SPK geçmişi göstergesi — olumsuz sonuç (Linear MEL-8)

> Bu deneyin kodu depoya alınmadı. Sayılar, deneme sırasında yerelde çalıştırılan kodla elde edildi.

**Soru.** Daha önce SPK vakası olan hisseler yeniden manipüle edilmeye daha mı yatkın? Bu bilgi
modellere eklenince tespit iyileşir mi?

**Göstergeler** (yalnızca o gün bilinen bilgi):
- `spk_prior_cases`: SPK'nın bu hisse için daha önce açıkladığı vaka sayısı.
- `spk_days_since_prior`: son açıklanan vakanın ilk kararından beri geçen gün (üst sınır 10 yıl).
- Bir vaka, ilk kararının ilan gününden **sonraki** günden itibaren sayıldı.
- Günün içinde bulunduğu vakanın kendisi sayılmadı. SPK aynı dönem için kararını zaten
  açıkladıysa, o dönemi "tespit etmek" bir başarı değildir; bu, sonucu yapay olarak şişirirdi.
- Her iki kural birim testleriyle doğrulandı.

**Sinyal var mı?** 2017–2026'da SPK dönemindeki hisse-haftaların %53'ünde hissenin önceki bir
vakası var; diğer haftalarda bu oran %41. Yani zayıf bir sinyal var.

**Eğitim deneyi** (dürüst yıllık eğitim, 2017–2026, 123 vaka, eşleştirilmiş bootstrap; fark = deney − ana):

| Model | AUC (ana → deney) | Fark [%95 GA] | recall@20 (ana → deney) | Fark [%95 GA] |
|---|---|---|---|---|
| LightGBM | 0,806 → 0,767 | −0,040 [−0,084, −0,004] anlamlı | 0,59 → 0,46 | −0,13 [−0,20, −0,07] anlamlı |
| PU bagging | 0,833 → 0,794 | −0,040 [−0,084, −0,006] anlamlı | 0,62 → 0,50 | −0,11 [−0,17, −0,04] anlamlı |
| Kural + PU | 0,849 → 0,837 | −0,013 [−0,035, +0,006] anlamsız | 0,67 → 0,62 | −0,05 [−0,09, −0,02] anlamlı |

- **Kontrol.** Ana LightGBM skorları aynı kodla yeniden üretildi ve birebir aynı çıktı. Fark,
  veri değişikliğinden değil göstergeden geliyor.
- **Ne oldu?** Modellerin haftalık ilk 20'sinde önceki vakası olan hisselerin payı %44'ten %49'a
  çıktı (tüm hisselerde %41). Model, geçmişi olan hisseleri öne çekti. Bu, gerçek manipülasyon
  haftalarını değil, "sicili olan" hisselerin sıradan haftalarını listeye taşıdı.
- **Yorum.** Bu, daha önce çıkarılan şirket profili göstergelerindeki sorunun aynısı: hisse
  kimliğine bağlı bilgi, modelin "nasıl hareket ettiğine" değil "kim olduğuna" bakmasına yol
  açıyor. Sonuç: **hisse kimliği / sicili göstergeleri modele eklenmez**; model yalnızca işlem
  davranışından öğrenir. Bu, etik açıdan da tercih edilen yaklaşım (bir hissenin geçmişi, bugünkü
  hareketinin şüpheli sayılması için gerekçe olmamalı).

## Deneme (25.10.2026): dönemi bilinmeyen vakaların eğitim etiketi — olumsuz sonuç

> Bu deneyin kodu depoya alınmadı. Ana sonuçlar varsayılan yöntemle (karardan önceki 6 ay) üretildi.
> Aşağıdaki sayılar, deneme sırasında yerelde çalıştırılan kodla elde edildi.

**Soru.**
- 402 fiyatlı ana set vakasının 230'unda SPK manipülasyon dönemini yazmıyor.
- Bu vakalarda eğitim etiketi "ilk karardan önceki 6 ay"dı.
- Bu etiket ne kadar doğru, daha iyisi yapılabilir mi?

**Bulgu 1 — SPK'nın ilk kararı dönemden çok sonra gelebiliyor.** Dönemi bilinen 172 vakada:

| İlk SPK kararı | Vaka | Dönem sonu → ilk karar (medyan) | 6 aylık pencere gerçek dönemle örtüşüyor |
|---|---|---|---|
| Tedbir / işlem yasağı | 79 | 36 gün | %61 |
| Ceza / suç duyurusu | 93 | 338 gün | %18 |

- Dönem başlangıcı, ilk karardan medyan 344 gün önce (%75'lik dilim: 704 gün).
- Dönemi bilinmeyen vakaların çoğunda ilk karar ceza. Bu vakalarda 6 aylık pencere büyük olasılıkla gerçek dönemi kaçırıyor.
- Ölçüm: 6 aylık pencerede etiketlenen günlerin yalnızca **%11'i** gerçek dönemin içinde.
- Bu pencereler, dürüst eğitimdeki pozitif günlerin yaklaşık %61'ini oluşturuyor.

**Denenen dönem tahmincisi.**
- **Arama alanı.** İlk karar tedbir ise karardan önceki 6 ay, ceza ise 24 ay.
- **Seçilen aralık.** Alan içinde hissenin endekse göre en sert yükseldiği aralık:
  - puan: endeks üstü log getiri / √gün;
  - uzunluk: 5–120 işlem günü.
- **Ön kayıt.** Kurallar sonuçlara bakılmadan sabitlendi.

**Tahmincinin doğruluğu** (dönemi bilinen vakalarda dönem gizlenerek):

| Yöntem | Gerçek dönemle örtüşme | Etiketlenen günlerin gerçek dönemde olma oranı | Gerçek dönemin kapsanan kısmı |
|---|---|---|---|
| 6 ay (varsayılan) | %38 | %11 | %32 |
| Tahmin | %38 | **%32** | %15 |

- Tahminci, etiket isabetini yaklaşık 3 katına çıkarıyor.
- Ama kısa dönemler seçiyor: medyan 8 gün, gerçekte 48 gün.

**Eğitim deneyi** (dürüst yıllık eğitim, 2017–2026, 123 vaka, eşleştirilmiş bootstrap). Dönemi bilinmeyen vakalar için üç etiket yöntemi denendi:
- **6 ay:** varsayılan yöntem.
- **Çıkar:** arama alanı eğitimden çıkarıldı.
- **Tahmin:** tahmin edilen aralık pozitif, alanın geri kalanı eğitim dışı.

| Model | AUC (6 ay / çıkar / tahmin) | recall@20 (6 ay / çıkar / tahmin) |
|---|---|---|
| LightGBM | 0,806 / 0,801 / 0,813 | 0,59 / 0,55 / 0,58 |
| PU bagging | 0,833 / 0,828 / 0,833 | 0,62 / 0,57 / 0,58 |
| Kural + PU | 0,849 / 0,844 / 0,844 | 0,67 / 0,65 / 0,68 |

- **Varsayılana göre.** Ne "çıkar" ne "tahmin", 6 aylık varsayılandan anlamlı biçimde farklı. Örnek: kural + PU tahmin − 6 ay: AUC −0,005 [−0,011, +0,002].
- **Tahmin, çıkar'dan anlamlı biçimde iyi** (AUC):
  - LightGBM: +0,012 [+0,004, +0,021]
  - PU bagging: +0,005 [+0,001, +0,009]
- **Sonuç.** Tahmin edilen dönemler gerçek bilgi taşıyor, ama kaba 6 aylık pencerelerden daha fazlasını değil.

**Yorum (tez için).**
- **Gürültüye dayanıklılık.** Modeller etiket gürültüsüne dayanıklı: etiket günlerinin ~%90'ı yanlış yerde olsa da 6 aylık pencereler zarar vermiyor. Olası nedenler:
  - Model "bu dönem manipülasyon" kadar "bu tür hisseler şüpheli davranır" bilgisini de öğreniyor. Manipüle edilen hisseler, asıl dönem dışında da sık sık anormal hareket ediyor.
  - PU öğrenme, eksik ve gürültülü pozitif varsayımıyla tasarlanmış.
- **Neyin işe yaradığı.** Bu bulgu, eski bültenlerle elde edilen iyileşmeyle birlikte okunmalı: performansı etiketlerin temizliği değil, **vaka sayısı** belirliyor.

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
