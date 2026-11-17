# Boş alarm incelemesi

`scripts/false_alarms.py --k 10` üretir; yorum `docs/yorum_v2.md`. Şirket adları bilerek verilmez: SPK kararı olmayan bir hisse için "manipülasyon" ya da "temiz" denemez.

Kural + PU, dürüst yıllık eğitim, 2017–2026 haftalık ilk 10. Aynı hissenin en fazla 4 hafta arayla gelen alarm haftaları tek döneme birleştirildi. Göstergeler dönemin ilk alarm haftasına göre. Karşılaştırma için aynı yıllardan sıradan bağımsız 5000 rastgele hisse-hafta aynı şekilde ölçüldü.

Toplam 2393 alarm dönemi (5110 hisse-hafta); 2316 dönem ana set SPK vakasına değmiyor.

## Alarmlar SPK kayıtlarına göre nereye düşüyor?

| grup | alarm dönemleri | rastgele hisse-haftalar |
|---|---|---|
| İsabet (ana set SPK vakası) | %3 | %0 |
| SPK yakını (ana set dışı / dönemi bilinmeyen vaka penceresi) | %9 | %6 |
| Hissenin başka zamanda SPK vakası var | %57 | %55 |
| SPK kaydı yok, 2025 ve sonrası | %7 | %10 |
| SPK kaydı yok, 2017–2024 | %24 | %28 |

"Hissenin başka zamanda SPK vakası var" grubunda vakanın alarmdan **sonra** başladığı dönemler: %43 (rastgele: %42); en yakın vaka penceresine medyan uzaklık 662 gün (rastgele: 730 gün).

## Gruplara göre özellikler

|                                                              |   dönem |   ort. süre (hafta) |   haber % |   sermaye işlemi % |   somut şirket olayı % |   Borsa açıklama istedi % |   sıçrama % |   60g yükseliş (medyan) % |   180g en derin düşüş (medyan) % |   pompa-boşalt şekli % |   piyasa değeri / yıl medyanı (medyan) |
|:-------------------------------------------------------------|--------:|--------------------:|----------:|-------------------:|-----------------------:|--------------------------:|------------:|--------------------------:|---------------------------------:|-----------------------:|---------------------------------------:|
| İsabet (ana set SPK vakası)                                  |      77 |                 3.8 |        47 |                 48 |                     45 |                        43 |           0 |                        62 |                              -45 |                     40 |                                   0.8  |
| SPK yakını (ana set dışı / dönemi bilinmeyen vaka penceresi) |     213 |                 2.5 |        47 |                 48 |                     45 |                        28 |           0 |                        59 |                              -38 |                     32 |                                   0.68 |
| Hissenin başka zamanda SPK vakası var                        |    1366 |                 2   |        49 |                 49 |                     39 |                        33 |           0 |                        59 |                              -38 |                     34 |                                   0.77 |
| SPK kaydı yok, 2025 ve sonrası                               |     160 |                 2   |        59 |                 54 |                     54 |                        23 |           0 |                        58 |                              -36 |                     30 |                                   1.57 |
| SPK kaydı yok, 2017–2024                                     |     577 |                 2.1 |        53 |                 46 |                     44 |                        35 |           0 |                        66 |                              -37 |                     33 |                                   1.2  |
| Boş alarmların tümü                                          |    2316 |                 2.1 |        50 |                 49 |                     42 |                        32 |           0 |                        60 |                              -38 |                     33 |                                   0.89 |
| Rastgele hisse-hafta (karşılaştırma)                         |    5000 |                 1   |        48 |                 49 |                     38 |                         5 |           0 |                        12 |                              -28 |                      5 |                                   1    |

Tanımlar: **haber** = son 20 günde güçlü KAP haberi; **sermaye işlemi** = son 60 günde sermaye artırımı/bölünme bildirimi; **somut şirket olayı** = önceki 60 günde ihale, yeni iş, birleşme, varlık alım-satımı, geri alım, halka arz, bedelli sermaye artırımı, pay alım teklifi gibi başlıklı bir KAP bildirimi (içeriği belirsiz "özel durum açıklaması" sayılmadı); **Borsa açıklama istedi** = son 20 günde "olağan dışı fiyat ve miktar hareketi" bildirimi; **sıçrama** = son 20 günde tek günde |getiri| > %25 (günlük fiyat sınırını aşıyor: düzeltilmemiş sermaye işlemi ya da veri hatası şüphesi); **pompa-boşalt şekli** = önceki 60 günde ≥ %50 yükseliş ve sonraki 180 günde zirveden ≥ %40 düşüş (geriye bakarak; model bunu alarm anında bilemez); **piyasa değeri** o yılın tüm hisse medyanına bölündü (enflasyon etkisini kaldırmak için).
