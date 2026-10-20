# Değerlendirme v2 — rastgele tabana karşı

Vakalar: manipülasyon dönemi SPK kararında yazan ana set vakaları (kısa pencere, medyan 22 gün), 2017–2026 başlayan, fiyat verisi olan: **125 vaka**. Haftalık liste: ~556 hisseden ilk k.
Rastgele = her vaka için analitik yakalanma olasılığı. Lift = recall / rastgele. AUC: haftalık kesitsel yüzdelik; pozitif = vaka dönemi haftaları, negatif = hiçbir vaka penceresine (12 ay, ana set dışı dahil) değmeyen haftalar. GA: vaka kümesi bootstrap'i. İsabet@10 lift: haftalık ilk 10'un 6 aylık vaka pencerelerine denk gelme oranı / taban oran.

## Dürüst yıllık eğitim (ana sonuç) — KAP özellikleri yok

| Model | AUC [%95 GA] | recall@20 (rastgele) | lift@20 [%95 GA] | recall@50 (rastgele) | zirveden önce@20 (rastgele) | öncü gün@20 | isabet@10 lift |
|---|---|---|---|---|---|---:|---:|
| random | 0.49 [0.47–0.52] | 0.22 (0.23) | 1.0 [0.7–1.3] | 0.46 (0.45) | 0.18 (0.21) | 14 | 1.0× |
| 0a_kural | 0.81 [0.78–0.84] | 0.65 (0.23) | 2.8 [2.4–3.2] | 0.80 (0.45) | 0.64 (0.21) | 8 | 2.4× |
| 0b_basit | 0.77 [0.73–0.81] | 0.55 (0.23) | 2.4 [2.0–2.8] | 0.78 (0.45) | 0.55 (0.21) | 9 | 2.3× |
| 1_iforest | 0.82 [0.79–0.85] | 0.53 (0.23) | 2.3 [1.9–2.7] | 0.76 (0.45) | 0.52 (0.21) | 7 | 2.3× |
| 2_lightgbm | 0.76 [0.71–0.79] | 0.53 (0.23) | 2.3 [1.9–2.7] | 0.72 (0.45) | 0.53 (0.21) | 10 | 3.1× |
| 3a_pu_agirlikli | 0.81 [0.77–0.84] | 0.57 (0.23) | 2.4 [2.1–2.9] | 0.74 (0.45) | 0.56 (0.21) | 10 | 3.0× |
| 3b_pu_bagging | 0.81 [0.77–0.84] | 0.57 (0.23) | 2.4 [2.1–2.9] | 0.74 (0.45) | 0.57 (0.21) | 11 | 3.1× |

**2017–2021:**

| Model | AUC [%95 GA] | recall@20 (rastgele) | lift@20 [%95 GA] | recall@50 (rastgele) | zirveden önce@20 (rastgele) | öncü gün@20 | isabet@10 lift |
|---|---|---|---|---|---|---:|---:|
| random | 0.50 [0.47–0.53] | 0.20 (0.24) | 0.8 [0.5–1.2] | 0.47 (0.46) | 0.17 (0.21) | 16 | 1.0× |
| 0a_kural | 0.83 [0.79–0.87] | 0.69 (0.24) | 2.9 [2.4–3.4] | 0.82 (0.46) | 0.69 (0.21) | 7 | 3.2× |
| 0b_basit | 0.78 [0.73–0.84] | 0.63 (0.24) | 2.7 [2.2–3.2] | 0.80 (0.46) | 0.63 (0.21) | 8 | 2.9× |
| 1_iforest | 0.85 [0.81–0.88] | 0.60 (0.24) | 2.5 [2.1–3.0] | 0.81 (0.46) | 0.59 (0.21) | 6 | 3.0× |
| 2_lightgbm | 0.76 [0.70–0.80] | 0.57 (0.24) | 2.4 [1.9–2.9] | 0.76 (0.46) | 0.57 (0.21) | 8 | 2.6× |
| 3a_pu_agirlikli | 0.82 [0.77–0.85] | 0.64 (0.24) | 2.7 [2.2–3.3] | 0.81 (0.46) | 0.63 (0.21) | 8 | 2.9× |
| 3b_pu_bagging | 0.82 [0.77–0.85] | 0.64 (0.24) | 2.7 [2.3–3.2] | 0.82 (0.46) | 0.64 (0.21) | 10 | 2.9× |

**2022–2026:**

| Model | AUC [%95 GA] | recall@20 (rastgele) | lift@20 [%95 GA] | recall@50 (rastgele) | zirveden önce@20 (rastgele) | öncü gün@20 | isabet@10 lift |
|---|---|---|---|---|---|---:|---:|
| random | 0.49 [0.44–0.54] | 0.26 (0.21) | 1.2 [0.6–1.9] | 0.43 (0.42) | 0.17 (0.18) | 11 | 1.1× |
| 0a_kural | 0.77 [0.72–0.82] | 0.54 (0.21) | 2.6 [1.9–3.5] | 0.74 (0.42) | 0.51 (0.18) | 11 | 1.7× |
| 0b_basit | 0.74 [0.69–0.79] | 0.34 (0.21) | 1.6 [1.0–2.4] | 0.71 (0.42) | 0.34 (0.18) | 15 | 1.9× |
| 1_iforest | 0.75 [0.69–0.80] | 0.34 (0.21) | 1.6 [1.0–2.4] | 0.63 (0.42) | 0.34 (0.18) | 10 | 1.7× |
| 2_lightgbm | 0.76 [0.69–0.82] | 0.43 (0.21) | 2.0 [1.4–2.8] | 0.63 (0.42) | 0.43 (0.18) | 15 | 3.6× |
| 3a_pu_agirlikli | 0.78 [0.72–0.84] | 0.37 (0.21) | 1.8 [1.1–2.5] | 0.54 (0.42) | 0.37 (0.18) | 15 | 3.1× |
| 3b_pu_bagging | 0.78 [0.72–0.84] | 0.37 (0.21) | 1.8 [1.1–2.5] | 0.54 (0.42) | 0.37 (0.18) | 14 | 3.4× |

## Yıl dışarıda bırakma (hindsight etiketler) — özellikler sinyal taşıyor mu?

| Model | AUC [%95 GA] | recall@20 (rastgele) | lift@20 [%95 GA] | recall@50 (rastgele) | zirveden önce@20 (rastgele) | öncü gün@20 | isabet@10 lift |
|---|---|---|---|---|---|---:|---:|
| random | 0.49 [0.47–0.52] | 0.22 (0.23) | 1.0 [0.7–1.3] | 0.46 (0.45) | 0.18 (0.21) | 14 | 1.0× |
| 0a_kural | 0.81 [0.78–0.84] | 0.65 (0.23) | 2.8 [2.4–3.2] | 0.80 (0.45) | 0.64 (0.21) | 8 | 2.4× |
| 2_lightgbm | 0.82 [0.79–0.85] | 0.67 (0.23) | 2.9 [2.5–3.3] | 0.81 (0.45) | 0.67 (0.21) | 8 | 3.7× |
| 3a_pu_agirlikli | 0.83 [0.80–0.86] | 0.64 (0.23) | 2.8 [2.4–3.2] | 0.78 (0.45) | 0.64 (0.21) | 7 | 3.5× |
| 3b_pu_bagging | 0.84 [0.81–0.87] | 0.61 (0.23) | 2.6 [2.2–3.0] | 0.76 (0.45) | 0.60 (0.21) | 8 | 3.8× |

**2017–2021:**

| Model | AUC [%95 GA] | recall@20 (rastgele) | lift@20 [%95 GA] | recall@50 (rastgele) | zirveden önce@20 (rastgele) | öncü gün@20 | isabet@10 lift |
|---|---|---|---|---|---|---:|---:|
| random | 0.50 [0.47–0.53] | 0.20 (0.24) | 0.8 [0.5–1.2] | 0.47 (0.46) | 0.17 (0.21) | 16 | 1.0× |
| 0a_kural | 0.83 [0.79–0.87] | 0.69 (0.24) | 2.9 [2.4–3.4] | 0.82 (0.46) | 0.69 (0.21) | 7 | 3.2× |
| 2_lightgbm | 0.84 [0.80–0.87] | 0.74 (0.24) | 3.1 [2.7–3.7] | 0.83 (0.46) | 0.74 (0.21) | 8 | 4.1× |
| 3a_pu_agirlikli | 0.85 [0.81–0.88] | 0.73 (0.24) | 3.1 [2.6–3.7] | 0.83 (0.46) | 0.73 (0.21) | 7 | 4.3× |
| 3b_pu_bagging | 0.86 [0.82–0.89] | 0.70 (0.24) | 2.9 [2.5–3.5] | 0.82 (0.46) | 0.70 (0.21) | 8 | 4.3× |

**2022–2026:**

| Model | AUC [%95 GA] | recall@20 (rastgele) | lift@20 [%95 GA] | recall@50 (rastgele) | zirveden önce@20 (rastgele) | öncü gün@20 | isabet@10 lift |
|---|---|---|---|---|---|---:|---:|
| random | 0.49 [0.44–0.54] | 0.26 (0.21) | 1.2 [0.6–1.9] | 0.43 (0.42) | 0.17 (0.18) | 11 | 1.1× |
| 0a_kural | 0.77 [0.72–0.82] | 0.54 (0.21) | 2.6 [1.9–3.5] | 0.74 (0.42) | 0.51 (0.18) | 11 | 1.7× |
| 2_lightgbm | 0.79 [0.72–0.84] | 0.46 (0.21) | 2.2 [1.5–3.0] | 0.74 (0.42) | 0.46 (0.18) | 16 | 3.5× |
| 3a_pu_agirlikli | 0.80 [0.73–0.85] | 0.40 (0.21) | 1.9 [1.3–2.7] | 0.63 (0.42) | 0.40 (0.18) | 15 | 2.7× |
| 3b_pu_bagging | 0.80 [0.72–0.85] | 0.37 (0.21) | 1.8 [1.1–2.5] | 0.60 (0.42) | 0.34 (0.18) | 16 | 3.4× |

## Tez sorusu 3 — KAP özellik kümeleri (dürüst, 2017–2026)

| model         |   ('auc', 'all') |   ('auc', 'none') |   ('auc', 'nonews') |   ('lift@20', 'all') |   ('lift@20', 'none') |   ('lift@20', 'nonews') |   ('plift@10', 'all') |   ('plift@10', 'none') |   ('plift@10', 'nonews') |
|:--------------|-----------------:|------------------:|--------------------:|---------------------:|----------------------:|------------------------:|----------------------:|-----------------------:|-------------------------:|
| 2_lightgbm    |            0.737 |             0.757 |               0.755 |                1.931 |                 2.275 |                   2.137 |                 2.563 |                  3.108 |                    3.033 |
| 3b_pu_bagging |            0.776 |             0.807 |               0.804 |                1.965 |                 2.448 |                   2.241 |                 2.794 |                  3.121 |                    3.061 |

## Eşleştirilmiş karşılaştırmalar (aynı vakalar, bootstrap %95 GA, 2017–2026)

| karşılaştırma                                  |   vaka |   AUC farkı | AUC GA           | AUC anlamlı   |   recall@20 farkı | recall GA        | recall anlamlı   |
|:-----------------------------------------------|-------:|------------:|:-----------------|:--------------|------------------:|:-----------------|:-----------------|
| Soru 2: PU bagging vs gözetimli                |    123 |      +0.050 | [+0.030, +0.073] | evet          |            +0.041 | [-0.024, +0.106] | hayır            |
| Soru 2: PU ağırlıklı vs gözetimli              |    123 |      +0.051 | [+0.031, +0.072] | evet          |            +0.041 | [-0.016, +0.098] | hayır            |
| ML vs kural: PU bagging vs kural               |    123 |      -0.007 | [-0.040, +0.022] | hayır         |            -0.081 | [-0.154, -0.008] | evet             |
| ML vs kural: LightGBM vs kural                 |    123 |      -0.056 | [-0.101, -0.019] | evet          |            -0.122 | [-0.203, -0.041] | evet             |
| Gözetimsiz: Isolation Forest vs kural          |    123 |      +0.006 | [-0.020, +0.033] | hayır         |            -0.106 | [-0.179, -0.033] | evet             |
| Etiket bolluğu: LightGBM hindsight vs dürüst   |    123 |      +0.067 | [+0.041, +0.098] | evet          |            +0.146 | [+0.073, +0.228] | evet             |
| Soru 3: LightGBM habersiz hareket vs KAP yok   |    123 |      -0.001 | [-0.017, +0.015] | hayır         |            -0.016 | [-0.081, +0.049] | hayır            |
| Soru 3: LightGBM tüm KAP vs KAP yok            |    123 |      -0.020 | [-0.050, +0.010] | hayır         |            -0.065 | [-0.154, +0.024] | hayır            |
| Soru 3: PU bagging habersiz hareket vs KAP yok |    123 |      -0.003 | [-0.009, +0.003] | hayır         |            -0.033 | [-0.065, -0.008] | evet             |

Not: Eşleştirilmiş karşılaştırmada 123 vaka var (ana tablodaki 125'ten 2'si, aynı hissede örtüşen
başka bir vakayla aynı haftaları paylaştığı için ayrı pozitif haftası kalmıyor).

## Yorum (21.10.2026)

**Soru 1 — Erken tespit: EVET, anlamlı.** Dönemi bilinen 125 vakada tüm yöntemler rastgeleyi açıkça
geçiyor. En iyi yöntem (kural tabanlı) vakaların %65'ini haftalık ilk 20 listede yakalıyor (rastgele
%23 → 2,8× [2,4–3,2]); %64'ünü fiyat zirvesinden önce (rastgele %21). İlk alarm, manipülasyon
başladıktan medyan 7–11 gün sonra. AUC 0,76–0,82. Etki 2022–2026'da zayıflıyor ama rastgelenin
üstünde kalıyor (kural lift 2,6 [1,9–3,5]).

**Soru 2 — PU learning: KISMEN EVET.** Dürüst modda iki PU varyantı da gözetimli LightGBM'den
anlamlı biçimde daha iyi sıralıyor (AUC +0,05 [+0,03, +0,07]). Recall farkı (+4 puan) anlamlı değil.
Hindsight modunda (tüm etiketler) fark kapanıyor (LightGBM 0,82 vs PU 0,83–0,84). Yorum: PU, etiketlerin
eksik olduğu gerçek kullanım koşulunda fayda sağlıyor — teorik beklentiyle tutarlı.

**ML vs kurallar: kurallar hâlâ en iyi recall'a sahip.** PU modelleri AUC'de kural tabanlı modele eşit
(fark −0,007, anlamsız) ama recall@20'de 8 puan geride (anlamlı). LightGBM her iki ölçüte göre kuralların
anlamlı biçimde altında. ML'in avantajı haftalık ilk 10'un isabetinde (lift ~3,0× vs kural 2,4×;
eşleştirilmiş test yapılmadı).

**Etiket bolluğu ML'i belirgin iyileştiriyor.** Aynı LightGBM, tüm etiketlerle (hindsight) eğitildiğinde
AUC +0,067, recall +14,6 puan (ikisi de anlamlı). ML'in darboğazı model değil, eğitim anındaki etiket
sayısı. SPK kararları biriktikçe ML'in kuralları geçmesi beklenebilir (hindsight'ta LightGBM recall
0,67 vs kural 0,65).

**Soru 3 — Habersiz hareket: HAYIR.** Ne "yalnızca habersiz hareket" ne "tüm KAP" özellikleri anlamlı
bir iyileşme sağlıyor; PU bagging'de habersiz hareket özellikleri recall'u hafifçe düşürüyor (−3 puan,
anlamlı). Önceki (v1) bulgu yeni ölçümle teyit edildi.

**Sınırlılıklar:** Sonuçlar yalnızca dönemi kararda yazan vakalar için (125/≈330). Bunlar muhtemelen
daha belirgin ve kısa süreli olaylar; dönemi yazmayan vakalarda başarı ölçülemiyor. Pozitif
haftaların yarısından fazlası 2019–2022'de; 2023 sonrası dönemi bilinen vaka az (11).
