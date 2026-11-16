# Web arayüzü — tasarım planı

Bu belge, projenin tanıtım sitesinin ne göstereceğini ve nasıl görüneceğini tarif eder. Tasarım araçlarına
(Claude Design, Google Stitch) verilecek hazır metinler: [tasarim_promptlari.md](tasarim_promptlari.md).

Mevcut durum: `app/` altında Streamlit ile yapılmış 4 sayfalık bir uygulama var (zaman makinesi, hisse
detayı, sonuçlar, yöntem). Çalışıyor ama görünümü standart bir veri bilimi uygulaması gibi. Bu plan, onun
yerine geçecek daha profesyonel bir site içindir.

## 1. Sitenin amacı ve kitlesi

| Kim | Ne görmek ister? | Sitede karşılığı |
|---|---|---|
| Danışman / jüri | Yöntem doğru mu, sonuçlar dürüst mü, tez soruları cevaplandı mı? | Sonuçlar, Yöntem, Deneme günlüğü |
| İşveren / mülakat | Projeyi 1 dakikada anlamak, etkileyici bir örnek görmek | Ana sayfa, Zaman makinesi, Vaka çalışmaları |
| Ben | Sistemin her haftaki çıktısını ve yeni denemelerin sonucunu görmek | Zaman makinesi, Hisse detayı, Canlı test |

**Ton:** Ciddi, sade, güven veren bir finansal gözetim paneli. Kripto sitesi gibi parlak değil; bir banka
risk paneli veya düzenleyici kurum raporu gibi. Önce Türkçe, sağ üstte İngilizce seçeneği.

## 2. Sayfa yapısı (sekmeler)

Üstte yatay menü (masaüstü), mobilde hamburger menü:

1. **Genel bakış** (ana sayfa)
2. **Zaman makinesi** — haftalık şüpheli listesi
3. **Hisse detayı**
4. **Vaka çalışmaları**
5. **Sonuçlar**
6. **Canlı test** — ileriye dönük test (henüz başlamadı; "yakında" durumu tasarlanmalı)
7. **Yöntem**
8. **Hakkında**

Her sayfada sabit öğeler:
- **Üst bar:** proje adı/logo, menü, dil seçici (TR/EN), açık/koyu tema düğmesi.
- **Alt bilgi (footer):** "Skorlar istatistiksel sinyaldir, suçlama değildir. Yatırım tavsiyesi değildir."
  uyarısı, GitHub bağlantısı, yazar adı.

## 3. Sayfalar

### 3.1 Genel bakış

Amaç: 30 saniyede "bu ne, ne kadar iyi" sorusunu cevaplamak.

- **Başlık bölümü:** "Borsa İstanbul'da manipülasyonu SPK'dan önce fark eden erken uyarı sistemi" + 1 cümle
  açıklama + iki düğme: "Zaman makinesini dene" / "Nasıl çalışıyor?"
- **4 ana rakam kartı** (her birinde rastgele seçimle karşılaştırma küçük yazıyla):
  - Yakalanan vaka: **%67** (rastgele: %23)
  - Fiyat zirvesinden önce: **%66** (rastgele: %20)
  - SPK'nın ilk cezasından: **medyan 13 ay önce**
  - AUC: **0,85** (0,5 = rastgele)
- **"Rastgeleden 3 kat iyi" ne demek?** 10×10 kare ızgara görselleri (iki çift):
  - 100 vaka → sistem 67'sini yakalıyor / rastgele 23'ünü
  - 100 alarm → yaklaşık 10'u SPK vakası / rastgele 3'ü
- **Nasıl çalışıyor (4 adım):** SPK kararları → günlük veriden göstergeler → modeller → haftalık liste.
  İkonlu yatay şerit.
- **Öne çıkan vaka kartı:** IZFAS 2018 — küçük grafik + "45. günde alarm, SPK tedbirinden sonra fiyat %87
  düştü" + "Vakayı incele" bağlantısı.
- **Veri büyüklüğü şeridi:** 17 yıl SPK bülteni · 657 vaka · 775 bin KAP bildirimi · her hafta 300–600 hisse.

### 3.2 Zaman makinesi (en önemli sayfa)

Amaç: "Geçmişte herhangi bir haftada sistem ne derdi, sonra ne oldu?"

- **Üst kontrol şeridi:**
  - Hafta seçici: takvim + 2012–2026 zaman çubuğu (kaydırıcı) + "önceki/sonraki hafta" okları
  - Hazır örnek haftalar (çip): IZFAS · Haz 2018, SANEL · May 2019, KGYO · Tem 2022
  - Model seçici (segment): Kural + PU (önerilen) / Kurallar / PU öğrenme
  - Liste uzunluğu: 10 / 20 / 50
- **Hafta özeti (3 küçük kart):** "SPK manipülasyon dönemindeki hisse: 1 / 20 (rastgele beklenti 0,1)",
  "O hafta puanlanan hisse: 385", seçili tarih aralığı.
- **Ana tablo** (satıra tıklayınca sağda önizleme paneli açılır):
  - Sıra · Hisse kodu · Şirket adı · Şüphe skoru (yatay çubuk) · Nedenler (en fazla 3 küçük etiket, ör.
    "Hacim 7×", "10 günün 9'u yükseliş", "Haber yok") · Sonradan SPK (rozet)
  - SPK rozetleri: yeşil "SPK dönemi · 27 gün sonra karar", sarı "2 yıl içinde SPK kararı", gri "—".
    Gri rozet asla "temiz/masum" yazmaz.
- **Sağ önizleme paneli:** seçili hissenin son 6 aylık mini grafiği (fiyat + SPK dönemi bandı), "Neden
  şüpheli?" çubukları, "Hisse detayına git" düğmesi.
- Tablo altında küçük not: "SPK bağlantısı olmayan hisse masum ya da suçlu anlamına gelmez."

### 3.3 Hisse detayı

- **Başlık:** Hisse kodu (büyük), şirket adı, varsa "N SPK kararı" rozeti; hisse arama kutusu.
- **Özet kartları:** en iyi haftalık sıra, ilk 20'de geçen hafta sayısı, SPK karar sayısı.
- **Ana grafik** (tarih aralığı seçicili, ortak zaman ekseni, 3 katman):
  1. Fiyat çizgisi + turuncu bantlar (SPK'nın belirttiği manipülasyon dönemleri) + siyah üçgenler
     (SPK kararları, üzerine gelince tür ve tarih) + kırmızı dikey çizgi (seçili hafta / ilk alarm)
  2. Hacim çubukları
  3. Haftalık sıra (ters eksen: 1 üstte), "ilk 20" kesik çizgisi
- **"Neden şüpheli?" paneli** (seçili hafta için): göstergelerin skora katkısını gösteren yatay çubuklar
  (pozitif kırmızı, negatif gri) + düz Türkçe cümleler.
- **SPK karar zaman çizelgesi:** dikey timeline — tarih, karar türü (suç duyurusu / para cezası / işlem
  yasağı / tedbir), belirtilen dönem, bülten no.
- **KAP bildirimleri:** aranabilir liste; her bildirimde sınıf etiketi (Gerçek haber / Fiyat hareketi
  açıklaması / Söylenti / Diğer).

### 3.4 Vaka çalışmaları

- **Kart ızgarası:** her kartta hisse kodu, dönem, küçük grafik, durum etiketi ("Yakalandı" yeşil /
  "Kaçırıldı" gri-turuncu), tek cümle. Üstte filtre: Tümü / Yakalanan / Kaçırılan.
- **Vaka sayfası** (hikâye anlatımı):
  - Yatay zaman çizelgesi: Manipülasyon başladı → İlk alarm (45. gün) → Fiyat zirvesi → SPK tedbiri →
    SPK cezası. Aralarında gün sayıları.
  - Büyük grafik (hisse detayındakiyle aynı bileşen).
  - "Sistem ne gördü?" (tetiklenen göstergeler) ve "Ders" kutuları.
- Vakalar: IZFAS, SANEL, KGYO (yakalanan), KONYA, KUYAS (kaçırılan).

### 3.5 Sonuçlar

- **Dönem seçici:** 2017–2026 (ana) / 2017–2021 / 2022–2026 / 2012–2016 / 2012–2026.
- **Ana rakam kartları** (genel bakıştakiyle aynı bileşen).
- **Model karşılaştırma:** gruplu çubuk grafik (her model için "yakalama" ve "rastgele beklenti") +
  altında tablo (AUC [güven aralığı], ilk 20'de yakalama, rastgele, × rastgele, zirveden önce, ilk 10 isabeti).
  En iyi model satırı vurgulu.
- **SPK'ya göre zaman:** histogram — ilk alarmdan SPK'nın ilk kararına / ilk cezasına kadar geçen gün.
- **Tez soruları:** 3 kart (soru, kısa cevap: Evet / Kısmen / Hayır rozeti, 1–2 cümle kanıt).
- **Deneme günlüğü:** denenen her fikir için satır — fikir, sonuç (✓ işe yaradı / ✗ katkı yok), etki
  (ör. "AUC +0,05, anlamlı"), tarih. Bu tablo yeni denemelerle büyüyecek.
- **Sağlamlık testleri:** (ileride) liste uzunluğu, yıl, hisse büyüklüğüne göre küçük grafikler.

### 3.6 Canlı test (ileride dolacak)

- Açıklama: "Model 2026-11-XX tarihinde donduruldu. O tarihten sonra her haftanın listesi kaydediliyor;
  Haziran 2027'de SPK'nın açıkladığı kararlarla karşılaştırılacak."
- Sayaçlar: kaydedilen hafta, listeye giren farklı hisse, sonradan SPK kararı gelen.
- Haftalık kayıt listesi (her hafta tıklanabilir).
- Henüz veri yokken: boş durum tasarımı ("İlk hafta kaydı bekleniyor").

### 3.7 Yöntem

- Akış şeması: veri kaynakları → etiketler / göstergeler → modeller → haftalık sıralama → değerlendirme.
- 4 adım kartı: Etiketler (SPK bültenleri), Göstergeler, Modeller (kurallar, Isolation Forest, LightGBM,
  PU öğrenme, kural + PU), Dürüst değerlendirme.
- "Rastgele taban nedir?" kutusu: kısa açıklama + formül + küçük örnek.
- "İlk hatamız" kutusu: ilk sonucun rastgeleden iyi olmadığını fark edip geri çekme hikâyesi.
- Veri kaynakları tablosu, sınırlılıklar listesi, etik ilkeler.

### 3.8 Hakkında

- Proje: Yazılım Mühendisliği bitirme projesi, 2026–2027. Yazar: Melih Erdem Koçoğlu. Danışman: [ad].
- Bağlantılar: GitHub, (ileride) tez PDF'i.

## 4. Görsel dil

- **Renkler:**
  - Zemin: açık temada kırık beyaz / çok açık gri; koyu temada koyu lacivert-antrasit.
  - Ana renk: koyu petrol mavisi / teal (#2a9d8f civarı) — düğmeler, vurgular.
  - **Anlamlı renkler (tüm sitede tutarlı):**
    - Turuncu (#f4a261) = SPK'nın belirttiği manipülasyon dönemi
    - Kırmızı (#e63946) = sistemin alarmı / ilk 20 eşiği
    - Yeşil = yakalandı / SPK dönemiyle eşleşti
    - Gri = rastgele beklenti / SPK kararı yok
  - Renk tek başına anlam taşımamalı: her rozette ikon veya yazı da olmalı.
- **Yazı tipi:** Inter veya IBM Plex Sans; rakamlarda eşit genişlikli (tabular) rakamlar. Büyük ana
  rakamlar 40–56 px.
- **Bileşenler:** yumuşak köşeli kartlar (12 px), ince kenarlıklar, gölge yok veya çok hafif; tablolar
  sıkı ama okunur; grafikler sade (ince ızgara, gereksiz süs yok).
- **Yoğunluk:** Zaman makinesi ve hisse detayı veri yoğun (panel gibi); genel bakış ve vaka sayfaları
  ferah (hikâye gibi).

## 5. Uyulması gereken kurallar

- Her sayfada "suçlama değildir / yatırım tavsiyesi değildir" uyarısı görünmeli.
- SPK kararı olmayan bir hisse için "manipüle edildi" ya da "temiz" ifadesi kullanılmamalı.
- Tasarım örneklerinde (mock-up) şirket adları: yalnızca SPK kararı kamuya açık vakalar (IZFAS, SANEL,
  KGYO, KONYA, KUYAS) gerçek adla; diğer satırlarda uydurma kodlar (ör. ABCDE, XYZTR).
- Her başarı rakamının yanında rastgele karşılaştırması bulunmalı.
- Erişilebilirlik: yeterli kontrast, klavyeyle gezinme, grafiklerde metin alternatifi.

## 6. Ekran öncelikleri

Masaüstü öncelikli (sunum ve bilgisayardan gösterim). Tablet uyumlu. Mobilde temel görüntüleme yeterli:
tablolar kart listesine dönüşür, grafik tam genişlik.

## 7. Tasarımdan sonra: nasıl hayata geçirilir?

İki yol var; karar tasarımlar görüldükten sonra verilecek:

| Yol | Artı | Eksi |
|---|---|---|
| A. Mevcut Streamlit uygulamasına tasarımı uygulamak (özel CSS, düzen) | Hızlı; mevcut kod kullanılır | Streamlit'in görünüm sınırları var, tasarımın bir kısmı birebir yapılamaz |
| B. Ayrı bir web sitesi (React/Next.js) + veri hattından üretilen hazır veri dosyaları (JSON) | Tasarım birebir uygulanır; sunucu gerekmez, statik site | Daha çok iş (yaklaşık 1–2 hafta) |

Not: Hangi yol seçilirse seçilsin site yerelde çalışacak; gerçek haftalık listeler internete açık
yayımlanmayacak (bkz. Bölüm 5).
