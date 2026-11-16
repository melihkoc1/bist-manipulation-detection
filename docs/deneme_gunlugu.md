# Deneme günlüğü

Projede denenen her fikir, işe yarasın ya da yaramasın, tek sayfada. Amaç: "bunu neden
yapmadınız?" sorusuna "denedik, şu sonucu verdi" diye cevap verebilmek. Ayrıntılar bağlantılı
belgelerde. Olumsuz sonuçlanan denemelerin kodu depoya alınmadı; sayılar deneme sırasında
üretildi ve aşağıdaki belgelerde kayıtlı.

Kısaltmalar: **AUC** = sıralama başarısı (0,5 rastgele); **yakalama** = vakanın haftalık ilk 20'ye
en az bir kez girmesi; **rastgele** = aynı uzunlukta rastgele listenin yakalama olasılığı.
Karşılaştırmalar aynı vakalar üzerinde eşli bootstrap ile; "anlamlı" = %95 güven aralığı 0'ı içermiyor.

| Tarih | Fikir | Sonuç | Sayılar | Karar | Ayrıntı |
|---|---|---|---|---|---|
| 18.10.2026 | Şirket profili göstergeleri (piyasa değeri, halka açıklık, sığlık) | ✗ Zararlı | LightGBM kazancının %53'ü bunlardan; yeni dönemde yakalama 0,42 → 0,22'ye çöktü | Çıkarıldı. Model "hangi hisse" olduğunu ezberliyordu | [arsiv_v1 §B3, B8](arsiv_v1/sonuclar_ozet_v1.md) |
| 18.10.2026 | Profil göstergelerini kesitsel sıraya çevirmek | ✗ Yetmedi | yakalama 0,27 | Profil göstergeleri tamamen çıkarıldı | [arsiv_v1 §B3](arsiv_v1/sonuclar_ozet_v1.md) |
| 18.10.2026 | Etiket penceresi 3 / 6 / 12 ay | — Duyarlılık | Uzun pencere yakalamayı mekanik olarak artırıyor | 6 ay varsayılan; dönemi bilinen vakalarla değerlendirme | [arsiv_v1 §B6](arsiv_v1/sonuclar_ozet_v1.md) |
| 18.10.2026 | Yıllık yeniden eğitim (statik model yerine) | ✓ Benimsendi | LightGBM test yakalaması 0,36 → 0,46 | Tüm değerlendirme yıllık, yalnızca geçmişte açıklanmış vakalarla | [arsiv_v1 §5](arsiv_v1/sonuclar_ozet_v1.md) |
| 19.10.2026 | KAP bildirim sayıları (kaba) | ✗ Hafif zararlı | KAP çıkarılınca LightGBM ilk-10 isabeti 0,078 → 0,103 | İçerik sınıflandırması yapıldı | [arsiv_v1 §B9](arsiv_v1/sonuclar_ozet_v1.md) |
| 19.10.2026 | KAP içerik sınıflandırması + "habersiz hareket" (tez sorusu 3) | ✗ Katkı yok | Habersiz hareket yakalama +0,007 (anlamsız); tüm KAP −0,019 | Ana modelde KAP göstergesi yok; Soru 3 = Hayır | [arsiv_v1 §6](arsiv_v1/sonuclar_ozet_v1.md), [yorum_v2](yorum_v2.md) |
| 20.10.2026 | İlk değerlendirme ("vakaların %40–47'si yakalandı") | ✗ Geri çekildi | Rastgele liste de %49 yakalıyordu | Rastgele taban her tabloya eklendi; değerlendirme baştan kuruldu | [arsiv_v1 §7](arsiv_v1/sonuclar_ozet_v1.md) |
| 20.10.2026 | PU öğrenme (gözetimli öğrenme yerine) | ✓ İşe yaradı | AUC +0,03, anlamlı | Ana modelin parçası | [yorum_v2](yorum_v2.md) |
| 20.10.2026 | Tüm etiketlerle eğitim (hindsight, tanı amaçlı) | — Tanı | LightGBM AUC +0,067, yakalama +14,6 puan | Darboğaz model değil, etiket sayısı → daha çok etiket | [yorum_v2](yorum_v2.md) |
| 22.10.2026 | Eski SPK bültenleri (2009–2015) | ✓ İşe yaradı | Vaka 335 → 413; LightGBM AUC +0,05, PU +0,02 (anlamlı) | Kalıcı | [yorum_v2](yorum_v2.md) |
| 22.10.2026 | Kapanış / VWAP ("kapanış oyunu") göstergeleri | ✗ Katkı yok | Modellerde anlamsız fark | Gösterge tabloda duruyor, ana modelde etkisiz | [yorum_v2](yorum_v2.md) |
| 23.10.2026 | Kural + PU birleşimi (eşit ağırlık) | ✓ En iyi model | AUC 0,85; hem kuraldan hem PU'dan anlamlı iyi | Ana model | [yorum_v2](yorum_v2.md) |
| 24.10.2026 | Dönemi bilinmeyen vakaların dönemini tahmin ederek etiketlemek | ✗ Kazanç yok | Kural + PU AUC −0,005 (anlamsız) | 6 aylık pencere kaldı | [yorum_v2](yorum_v2.md) |
| 17.11.2026 | Hissenin SPK geçmişi (önceki vaka sayısı) | ✗ Zararlı | PU AUC −0,04, yakalama −0,11 (anlamlı) | Eklenmedi. Profil sorununun aynısı | [yorum_v2](yorum_v2.md) |
| 17.11.2026 | Birleşim ağırlıklarını geçmiş yıllardan öğrenmek | ✗ Kazanç yok | AUC +0,000 (anlamsız); LightGBM'e 0 ağırlık | Eşit ağırlık kaldı | [yorum_v2](yorum_v2.md) |
| 17.11.2026 | Sağlamlık testleri (k, yıl, büyüklük, süre) | ✓ Ana bulgu sağlam | Her k'da ve her büyüklük grubunda anlamlı; zayıf: 2022, uzun vakalar | Tezde raporlanacak | [saglamlik.md](saglamlik.md), [yorum_v2](yorum_v2.md) |
