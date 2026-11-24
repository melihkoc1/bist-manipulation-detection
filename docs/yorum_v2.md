# Değerlendirme v2 — yorum

Sayılar `docs/sonuclar_v2.md` içinde (`scripts/evaluate_v2.py` ve `scripts/compare_v2.py` üretir,
her çalıştırmada yeniden yazılır). Bu dosya elle tutulan yorumdur; scriptler dokunmaz.

## Deneme (25.11.2026): farklı PU yöntemleri — Elkan–Noto eşdeğer, nnPU daha kötü (Linear MEL-82)

**Soru.** Ana modeldeki PU bagging (Mordelet & Vert 2014) yerine başka bir PU yöntemi daha iyi olur mu?

**1) Elkan–Noto ağırlıklı yeniden eğitim** (`3a_pu_agirlikli`, projede baştan beri vardı; skorlar eşli
olarak yeniden karşılaştırıldı). 2017–2026, 123 vaka:

| | AUC | yakalama@20 | İlk 10 isabeti |
|---|---|---|---|
| PU: Elkan–Noto / bagging | 0,833 / 0,833 (+0,000 [−0,004, +0,005]) | 0,592 / 0,624 (−0,016, anlamsız) | 0,097 / 0,102 |
| Kural + PU: Elkan–Noto / bagging | 0,848 / 0,849 (−0,001) | 0,672 / 0,672 | 0,096 / 0,100 |

İki yöntem eşdeğer: PU'nun hangi türü seçildiği sonucu değiştirmiyor.

**2) nnPU** (Kiryo ve ark. 2017; negatif olmayan PU riski). Tasarım sonuçlara bakılmadan Linear'a yazıldı.
Ortamda derin öğrenme kütüphanesi olmadığı için doğrusal sürüm numpy ile yazıldı (sigmoid kayıp, Adam,
20 tur); ön işleme lojistik tabanla aynı. Sınıf oranı π her yıl Elkan–Noto ile tahmin edildi. Adil
karşılaştırma aynı doğrusal öğreniciyle (PU-lojistik, MEL-81).

| | AUC | yakalama@20 | İlk 10 isabeti |
|---|---|---|---|
| nnPU / PU-lojistik (doğrusal, eşit şartlar) | 0,807 / 0,816 (−0,009 [−0,030, +0,015]) | 0,585 / 0,553 (+0,032, anlamsız) | — |
| Kural + nnPU / ana model | 0,833 / 0,849 (**−0,015** [−0,028, −0,003]) | 0,632 / 0,672 (−0,041, anlamsız) | 0,078 / 0,100 |

**π tahmini başarısız oldu.** Tahmin her yıl üst sınıra (0,3) dayandı: c (pozitifin etiketlenme
olasılığı) 0,009–0,017 çıktı. Elkan–Noto'nun "pozitifler etiketsizlerden ayrışabilir ve model kalibre"
varsayımı bu veride tutmuyor. Sonuçları gördükten sonra yapılan duyarlılık analizi (karar için
kullanılmadı): π = 0,05 sabitlenince Kural + nnPU AUC 0,833 (−0,016, anlamlı), yakalama 0,592
(−0,081, anlamlı). Yani nnPU'nun zayıflığı yalnız π'den kaynaklanmıyor.

**Karar: ana model değişmedi.** nnPU kodu depoya alınmadı. Tez için çıkarım: PU yaklaşımı önemli
(gözetimli öğrenmeye göre anlamlı iyi), ama PU'nun türü ikincil; en basit ve π gerektirmeyen bagging
yeterli. nnPU gibi π'ye dayanan yöntemler, gerçek manipülasyon oranı bilinmediği için bu problemde
dezavantajlı.

## Deneme (24.11.2026): lojistik regresyon — basit model yolun çoğunu yürüyor, ağaçlar listenin üstünde önde (Linear MEL-81)

**Amaç.** Jüri için sade ve açıklanabilir bir taban: aynı 32 göstergeyle doğrusal model.

**Tasarım** (sonuçlara bakılmadan sabitlendi, Linear'a yazıldı): her yıl yalnız eğitim verisinden
öğrenilen ön işleme (eksikler medyanla, %1–%99 kırpma, standartlaştırma); L2 lojistik regresyon,
C = 1, ayar yok. İki model:
- `2b_lojistik`: etiketsiz günler negatif (LightGBM'in karşılığı).
- `3c_pu_lojistik`: PU bagging kurgusu (15 torba, 20 kat etiketsiz), taban öğrenici lojistik regresyon.

**Sonuç** (2017–2026, 123 vaka, deney − karşılığı, eşli bootstrap; rastgele yakalama 0,232):

| Model | Karşılığı | AUC | yakalama@20 | İlk 10 isabeti |
|---|---|---|---|---|
| Lojistik (etiketsiz = negatif) | LightGBM | 0,813 / 0,806 (+0,009, anlamsız) | 0,536 / 0,592 (−0,073, anlamsız) | 0,092 / 0,098 |
| PU-lojistik | PU-LightGBM | 0,817 / 0,833 (−0,016, anlamsız) | 0,560 / 0,624 (−0,065, anlamsız) | 0,099 / 0,102 |
| Kural + PU-lojistik | Ana model | 0,841 / 0,849 (−0,009, anlamsız) | 0,640 / 0,672 (−0,033, anlamsız) | 0,093 / 0,100 |

**Yorum.**
- Doğrusal model, ağaç modellerinin AUC'sine çok yakın; sinyalin büyük kısmı basit, doğrusal
  bir ilişkiyle yakalanabiliyor.
- Ağaç modelleri listenin üstünde (ilk 20) tutarlı biçimde 3–7 puan önde. Fark tek tek anlamlı
  değil, ama her üç karşılaştırmada aynı yönde. Göstergeler arasındaki etkileşimler (ör. "sert
  yükseliş VE yüksek devir") en şüpheli birkaç hisseyi ayırmada işe yarıyor.
- Karar: ana model değişmedi. Lojistik modeller karşılaştırma tabanı olarak depoda kaldı (`2b_lojistik`, `3c_pu_lojistik`).

**Katsayılar** (2026 modeli, ≤2025 verisi, standartlaştırılmış; 15 torbanın ortalaması). Şüpheyi en
çok artıranlar: son 10 günde yükselen gün sayısı (+0,22), kapanışın ağırlıklı ortalama fiyata göre
yüksekliği (+0,18), 3 aylık dipten yükseliş (+0,17), halka açık devir (+0,13), 20 günlük getiri
z-skoru (+0,13). Azaltanlar: 60 günlük zirveden uzaklık (−0,17; zirveye yakın hisse daha şüpheli),
kapanışın gün aralığındaki yeri (−0,16), tavan sayısı (−0,11).

Dikkat: katsayılar diğer göstergeler sabitken okunur. Tavan sayısının eksi çıkması "tavan iyi" demek
değil: tavan bilgisi zaten yükselen gün sayısı ve getiri göstergelerinde var; aynı yükseliş içinde
tavanla gelen hareket biraz daha az şüpheli sayılıyor; nedeni (ör. haberle gelen ani sıçramalar)
ayrıca incelenmedi.

## Deneme (19.11.2026): fiyat ile temel değerin kopması (PD/DD, kâr verimi) — zararlı (Linear MEL-18)

**Veri.** İş Yatırım mali tablo servisinden çeyreklik özkaynak ve dönem kârı, 2009 → 2026. Sanayi
şirketleri için XI_29 tablosu (ana ortaklığa ait özkaynak, dönem kârı), bankalar için UFRS tablosu.
Fiyat verisindeki 863 hissenin 631'inde tablo bulundu; kalanların çoğu fiyat geçmişi boş ya da
yatırım ortaklığı / aracı kurum gibi tablosu farklı şirketler. Vakaların %94'ünde (411 vakanın 385'i) tablo var.

**Tasarım** (sonuçlara bakılmadan sabitlendi, Linear'a yazıldı):
- Bilinme tarihi sabit ve ihtiyatlı (yasal sürelerin üzerinde): 1. ve 3. çeyrek dönem sonu +60 gün,
  6 ay +75, yıllık +100. KAP yayın tarihi eşleştirmesi bilerek kullanılmadı (yanlış eşleşme sızıntı yaratabilir).
- Birincil set A: `log_pb` (log piyasa değeri / özkaynak), `neg_equity`, `pb_dev_250` (log_pb'nin
  hissenin son 250 işlem günü medyanından sapması: asıl "temelden kopma" göstergesi), `ey_ttm`
  (son 12 ay net kâr / piyasa değeri).
- Sağlamlık seti B: A'dan `log_pb` çıkarılır (hisseye özgü kalıcı seviye, ezber riski).
- Karar kuralı aynı: Kural + PU'da AUC veya yakalama@20'de anlamlı artış.

**Betimsel kontrol** (2012+, 411 vaka). Getirisi en yüksek %5'lik günler kendi içinde:

| | PD/DD medyanı | `pb_dev_250` > 0,5 | Zararda (son 12 ay) |
|---|---|---|---|
| SPK vaka günleri | 6,5 | %65 | %29 |
| Vaka olmayan günler | 4,8 | %57 | %28 |

Vaka günleri, benzer yükselişteki diğer günlerden daha pahalı ve temelden daha kopuk görünüyordu;
bu umut verici bir işaretti.

**Sonuç** (2017–2026, deney − ana, eşli bootstrap):

| Set | Model | AUC | yakalama@20 |
|---|---|---|---|
| A | PU | **−0,030** [−0,055, −0,004] | **−0,106** [−0,187, −0,016] |
| A | Kural + PU | −0,013 [−0,027, +0,000] | **−0,057** [−0,114, −0,008] |
| B | PU | **−0,024** [−0,045, −0,002] | **−0,114** [−0,195, −0,041] |
| B | Kural + PU | −0,010 [−0,022, +0,000] | −0,024 [−0,081, +0,033] |

Kalın: anlamlı. İlk 10 isabeti A'da 0,100 → 0,097, B'de 0,100 → 0,096.

**Karar: eklenmedi.** Betimsel fark gerçek ama model bunu genelleyemiyor. Yorum: PD/DD ve kâr verimi
yavaş değişen, hisseye özgü özellikler. Model, geçmiş vakaların "ne tür şirket" olduğunu (küçük,
pahalı, zararlı) öğreniyor; yeni yıllarda bu şirketler değişince işe yaramıyor. Şirket profili ve SPK
geçmişi denemelerindeki ezber sorununun aynısı; seviye göstergesi (`log_pb`) çıkarılınca da sürüyor,
çünkü `ey_ttm` ve `neg_equity` de hisseye özgü. Kod depoya alınmadı.

## Deneme (19.11.2026): Borsa İstanbul VBTS tedbirleri gösterge olarak — kazanç yok (Linear MEL-11)

**Veri.** KAP'ta düzenleyici kurum (DDK) bildirimleri 2010-01 → 2026-11 indirildi (217.411 bildirim).
Volatilite Bazlı Tedbir Sistemi (VBTS) duyurularının 2.633'ünün metni tek tek indirildi; hisse kodu ve
tarihler yalnız metinde. 2.624'ü ayrıştırıldı: 563 hissede 4.347 tedbir aralığı (2017-10 → 2026-11).
Seviye: 1 açığa satış / kredili işlem yasağı (2.437), 2 brüt takas (1.067), 3 emir paketi veya tek
fiyat (843).

**Tasarım** (sonuçlara bakılmadan sabitlendi, Linear'a yazıldı):
- Yalnız gösterge olarak üç değişken: `vbts_level` (o gün yürürlükteki en ağır tedbir), `vbts_active`,
  `vbts_new_20` (son 20 işlem gününde başlayan tedbir sayısı).
- Tedbir, duyurunun bilinme gününden (18:00 sonrası yayın → ertesi işlem günü) önce kullanılmadı.
- Hissenin uzun dönem tedbir geçmişi bilerek kullanılmadı (SPK geçmişi denemesindeki ezber sorunu).
- SPK tedbir kararları kullanılmadı (vakaların kendisi, sızıntı); yakın izleme ve şirket uyarıları
  finansal durumla ilgili olduğu için dışarıda bırakıldı.
- Karar kuralı aynı: Kural + PU'da AUC veya yakalama@20'de anlamlı artış.

**Betimsel kontrol** (2018+, 320 vaka, 27.764 vaka günü):

| | Aktif tedbir | Seviye ≥ 2 | Seviye 3 |
|---|---|---|---|
| SPK vaka günleri | %9,6 | %5,1 | %3,3 |
| Diğer günler | %5,7 | %2,4 | %1,2 |

Vakaların %35'inin penceresinde en az bir gün tedbir var. Ancak 60 günlük getirisi en yüksek %5'lik
günler kendi içinde karşılaştırılınca fark kayboluyor: aktif tedbir vaka günlerinde %26,5, vaka
olmayanlarda %28,3. Tedbir, sert fiyat hareketinin bir yansıması; model bu hareketi zaten görüyor.

**Sonuç** (deney − ana, eşli bootstrap):

| Model | Dönem | AUC | yakalama@20 |
|---|---|---|---|
| PU | 2017–2026 | −0,001 [−0,002, +0,001] | −0,016 [−0,049, +0,016] |
| Kural + PU | 2017–2026 | −0,001 [−0,002, +0,000] | +0,000 |
| Kural + PU | 2018–2026 (115 vaka) | −0,001 [−0,002, +0,000] | +0,000 |

Kural + PU AUC'si 0,849 (değişmedi), ilk 10 isabeti 0,100 → 0,099.

**Karar: eklenmedi.** Borsa'nın tedbiri, modelin fiyat ve devir göstergelerinden zaten çıkardığı
oynaklığı özetliyor; yeni bilgi taşımıyor. Kod depoya alınmadı. Yeniden üretmek için: KAP
`byCriteria` sorgusunda `memberType: "DDK"`, bildirim sayfalarından "İlgili Şirketler" ve Türkçe
tedbir cümlesi ("... payları gg/aa/yyyy tarihli işlemlerden ... gg/aa/yyyy tarihli işlemlere kadar ...").

## Deneme (18.11.2026): ana set dışı vakalar zayıf etiket olarak — küçük AUC artışı, ana model değişmedi (Linear MEL-10)

**Veri.** Fiyatı olan 513 vakanın 111'i ana set dışında: 100 çok hisseli karar (61'i 2025, 8'i 2026'da
açıklandı) ve 11 "3. seviye" pazar tedbiri (2014–2019). Bu vakaların günleri şimdiye kadar eğitimde ve
değerlendirmede dışarıda bırakılıyordu.

**Tasarım** (sonuçlara bakılmadan sabitlendi, Linear'a yazıldı): yalnız eğitimde, Y yılı modeli için
Y−1 sonuna kadar açıklanmış ana set dışı vakaların günleri (bilinen dönem veya 6 aylık pencere)
pozitif sayıldı. 2026 modelinde pozitif gün 34.315 → 45.626. Değerlendirme değişmedi (aynı 123 vaka).
Karar kuralı: Kural + PU'da AUC veya yakalama@20'de anlamlı artış varsa benimse.

**Sonuç** (2017–2026, deney − ana, eşli bootstrap):

| Model | AUC | yakalama@20 | İlk 10 isabeti |
|---|---|---|---|
| PU | **+0,007** [+0,002, +0,013] | −0,016 [−0,057, +0,024] | 0,102 → 0,105 |
| Kural + PU | **+0,003** [+0,0002, +0,007] | −0,008 [−0,024, +0,000] | 0,100 → 0,097 |

Kural + PU AUC'si 0,849 → 0,853. 123 vakanın 72'sinde vaka içi AUC arttı, 51'inde azaldı.

**Karar: ana model değişmedi** (kullanıcıyla birlikte, 18.11.2026). Önceden yazılan kurala göre AUC
artışı "anlamlı" sayılıyor; bu sapma bilerek yapıldı ve gerekçesi:
- Artış çok küçük ve güven aralığının alt sınırı sıfıra çok yakın (+0,0002).
- Uygulamada önemli olan ölçüler (ilk 20'de yakalama, ilk 10 isabeti) artmadı, hafifçe düştü.
- Canlı test için model 17.11.2026'da donduruldu; ana modeli değiştirmek geriye dönük sonuçlarla
  canlı testi birbirinden koparırdı.

**Yorum.** Daha çok etiket yönü doğru: PU'nun sıralama başarısı anlamlı arttı. Ama bu vakalar
çoğunlukla emir bazlı (çok hisseli) işlemler; pompala-boşalt örüntüsüne tam uymadıkları için üst
sıraları iyileştirmiyorlar. Gerçek kazanç, pompala-boşalt türünden yeni etiketlerden gelebilir
(ör. kendi kriterlerimizle tanımlanacak örüntü etiketleri, ileride).

## Deneme (17.11.2026): yükseliş sırasında içeriden satış — kazanç yok (Linear MEL-9)

**Veri durumu.** KAP üst verisinde 18.617 "Pay Alım Satım Bildirimi" var (376 hisse). Yön (alış/satış)
yalnız özetten anlaşılabiliyor: yalnız satış 1.726, yalnız alım 6.795 (1.924'ü şirketin kendi
paylarını geri alımı), belirsiz 10.096. Bildirimlerin çoğu aracı kurum ve yatırım ortaklıklarının
rutin işlem bildirimleri. Tutar ve kişi bilgisi bildirim gövdesinde; o veri indirilmedi.

**Tanım** (sonuçlara bakılmadan sabitlendi, Linear'a yazıldı): son 60 işlem gününde etkili olan
satış ve alım bildirimi sayısı; "yükselişte satış" = satış bildirimi var ve 3 aylık getiri > %30.

**Betimsel kontrol** (2012–2026, hisse-gün):

| Grup | Son 60 günde satış bildirimi | Satış + yükseliş |
|---|---|---|
| SPK vaka günleri | %1,1 | %0,2 |
| Rastgele günler | %1,7 | %0,4 |
| 3 ayda +%50 yükselmiş, vaka dışı | %2,8 | %2,8 |

SPK vakalarında satış bildirimi rastgele günlerden bile **az**. Vaka-yıl bazında 200 vakanın
yalnız %2'sinde bildirilmiş bir satış var.

**Model** (PU aynı ayarlarla + 3 gösterge, dürüst yıllık eğitim, 2017–2026, 123 vaka, deney − ana):

| Model | AUC | yakalama@20 |
|---|---|---|
| PU | −0,002 [−0,012, +0,005] | −0,041 [−0,089, +0,000] |
| Kural + PU | −0,000 [−0,006, +0,003] | −0,008 [−0,024, +0,000] |

Hiçbiri anlamlı değil; kazanç yok. Deney kodu depoya alınmadı.

**Yorum.**
- SPK'nın ceza verdiği pompala-boşalt vakalarında satan taraf çoğunlukla bildirim yükümlülüğü
  olmayan kişiler (yönetici veya büyük ortak değil). Bu yüzden KAP'ta "içeriden satış" izi bırakmıyor.
- Bildirim gövdelerini indirip tutar ve kişiyi ayrıştırmak (aşama 2) şu an önerilmiyor: daha temiz
  bir yön bilgisi, vakaların %2'sinde var olan bir olayı büyütmez. Kişi bazında işlem verisi ancak
  aracı kurum dağılımıyla (AKD, MEL-19) gelir.

## Deneme (17.11.2026): yükselişi bütün olarak izleyen göstergeler — kazanç yok (Linear MEL-13)

Tanım sonuçlara bakılmadan sabitlendi ve Linear'a yazıldı. Yükselişin başı = son 60 işlem günündeki en
düşük kapanış günü. Beş yeni gösterge eklendi: dipten beri geçen gün, dipten beri toplam halka açık
devir, dipten beri günlük ortalama log getiri, dipten beri yükselen gün oranı, dipten beri tavan sayısı.
Göstergeler yalnızca o güne kadarki veriyi kullanıyor (100 rastgele noktada veriyi keserek yeniden
hesaplama: uyumsuzluk 0). Yalnız PU bagging bu göstergelerle aynı ayarlarla, dürüst yıllık eğitimle
yeniden skorlandı; Kural + PU yeniden kuruldu (`scripts/exp_compare.py`). Deney kodu depoya alınmadı.

Sonuçlar (2017–2026, 123 vaka, deney − ana, eşli bootstrap %95 GA):

| Model | AUC | yakalama@20 | Karar |
|---|---|---|---|
| PU | −0,013 [−0,028, +0,000] | **−0,073** [−0,130, −0,016] | ✗ anlamlı kötüleşme |
| Kural + PU | −0,005 [−0,013, +0,001] | −0,024 [−0,065, +0,016] | ✗ kazanç yok |

Ana model 2017–2026: Kural + PU AUC 0,849 → 0,844, yakalama@20 0,67 → 0,63 (rastgele 0,23),
isabet@10 0,100 → 0,091.

**Yorum.**
- Yükselişin boyu ve hızı zaten mevcut göstergelerde var: "3 aylık dipten yükseliş" (SHAP'ta 2. sıra)
  ile yeni gösterge birleşimi neredeyse aynı bilgi (korelasyon 0,995). Haftalık devir hızı da yükseliş
  boyunca devri büyük ölçüde yansıtıyor.
- Yeni göstergeler aynı bilgiyi gürültülü biçimde tekrar ettiği için az etiketli PU modeli onlara
  bölünüp daha kötü ayırıyor (MEL-12'deki "sade model daha iyi" bulgusuyla tutarlı).
- Sonuç: yükseliş dönemini fiyat/hacimden yeniden tanımlamak yeni bilgi getirmiyor; kalan kazanç büyük
  olasılıkla dışarıdan yeni bilgiden (içeriden satış, Borsa tedbirleri) veya daha çok etiketten gelecek.

## Deneme (17.11.2026): model paketi — yakın tarih ağırlığı, lambdarank, zamana dürüst ayar — kazanç yok (Linear MEL-12)

Üç fikir PU bagging üzerinde denendi; ayarlar sonuçlara bakılmadan önce sabitlendi ve Linear'a
yazıldı. Her biri dürüst yıllık eğitimle 2012–2026 skorlandı, Kural + PU birleşimi yeniden kuruldu
ve ana skorlarla aynı vakalarda eşli bootstrap ile karşılaştırıldı (`scripts/exp_compare.py`).
Deney kodu depoya alınmadı.

1. **Yakın tarih ağırlığı:** eğitim satırlarına 0,5^(yaş / 3 yıl) ağırlığı (eski yılların etkisi azalır).
2. **Lambdarank:** PU torbaları, "şüpheli mi?" yerine "o gün hangisi daha şüpheli?" sorusunu doğrudan
   öğrenen sıralama hedefiyle eğitildi (grup = işlem günü).
3. **Zamana dürüst ayar seçimi:** iki ek ayar (sade: num_leaves 15 / min_child 100; karmaşık: 63 / 20)
   baştan sona skorlandı. Her Y yılı için, Y'den önceki haftalarda ve yalnızca Y−1 sonuna kadar
   açıklanmış vakalarla haftalık AUC'si en iyi olan ayar seçildi. (Protokol notu: doğrulama penceresi
   başta "yalnız Y−1" diye yazılmıştı; sonuçlar görülmeden "2012..Y−1" yapıldı, çünkü tek yılda bilinen
   vaka çok az.) Seçim 2014'ten itibaren 13 yılın 12'sinde "sade" ayarı oldu.

Sonuçlar (2017–2026, 123 vaka, deney − ana, eşli bootstrap %95 GA):

| Deneme | PU AUC | Kural + PU AUC | Kural + PU yakalama@20 | Karar |
|---|---|---|---|---|
| Yakın tarih ağırlığı | −0,010 [−0,026, +0,004] | −0,005 [−0,014, +0,002] | −0,016 | ✗ anlamsız kötüleşme |
| Lambdarank | **−0,018** [−0,031, −0,005] | **−0,007** [−0,013, −0,001] | **−0,057** [−0,106, −0,016] | ✗ anlamlı kötüleşme |
| Sade ayar | **+0,006** [+0,002, +0,010] | +0,001 [−0,001, +0,003] | 0,000 | ✗ ana modelde kazanç yok |
| Karmaşık ayar | **−0,007** [−0,011, −0,003] | −0,002 [−0,004, +0,000] | −0,016 | ✗ |
| Zamana dürüst seçim | **+0,005** [+0,002, +0,010] | +0,001 [−0,001, +0,003] | 0,000 | ✗ ana modelde kazanç yok |

**Yorum.**
- Eski yıllar da bilgi taşıyor: SPK vakaları az olduğu için eski vakaların etkisini azaltmak modeli
  zayıflatıyor. Manipülasyon örüntüsü zaman içinde pek değişmiyor (SHAP bulgusuyla tutarlı).
- Lambdarank açıkça kötü: her günün grubunda pozitif çok nadir; sıralama hedefi bu kadar seyrek
  etikette sınıflandırmadan daha az bilgi çıkarıyor.
- Sade ağaçlar PU'yu tek başına biraz iyileştiriyor (AUC +0,006), ama kurallarla birleşince fark
  kayboluyor; ilk 10 isabeti de değişmiyor. Ana model ve önceden belirlenmiş ayarlar korundu.
- Sonuç: model tarafında "ucuz" iyileştirmeler tükendi; kalan kazanç büyük olasılıkla daha çok etiketten
  (MEL-10) veya yeni bilgiden (içeriden satış, Borsa tedbirleri) gelecek.

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
