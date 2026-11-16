# BIST Manipülasyon Tespiti — Tasarım teslimi (Claude Code için)

Bu klasör, web uygulamasının onaylanmış tasarımını içerir. Amaç: bu tasarımı
projenin gerçek kod tabanında (mevcut yığın neyse onunla) birebir uygulamak.

## Dosyalar nasıl okunmalı

- Her `*.dc.html` dosyası bir sayfanın tam tasarımıdır. Bir tasarım aracının
  şablon biçimindedir: `<x-dc>`, `<helmet>`, `<sc-for>`, `<sc-if>`, `{{değer}}`
  ve en alttaki `class Component extends DCLogic { renderVals() … }` bloğu.
  - `<sc-for list="{{rows}}" as="r">` = bir döngü (`rows.map`).
  - `<sc-if value="{{x}}">` = koşullu render.
  - `renderVals()` içindeki diziler **sahte (mock) veridir** → gerçek API/veri
    katmanına bağlanacak; yapıları veri sözleşmesi için ipucu verir.
  - `support.js` ve `data-props` tasarım aracına aittir; uygulamaya taşınmaz.
- `<helmet><style>` içindeki `.app` / `.app.dark` CSS değişkenleri **tasarım
  token'larıdır** (aşağıda da listelendi). Inline `style="…"` değerleri
  boşluk, boyut ve yerleşim için kaynak alınmalıdır.
- `canvas.json` yalnızca tasarım tuvalinin yerleşimidir; uygulamaya gerekmez.

## Sayfa → dosya eşlemesi

| Rota (öneri) | Sayfa | Dosya |
|---|---|---|
| `/` | Genel bakış | `Main.dc.html` (+ mobil: `Mobil-Genel-bakis.dc.html`) |
| `/zaman-makinesi` | Zaman makinesi | `Zaman-makinesi.dc.html` (+ koyu, + mobil) |
| `/hisse/[kod]` | Hisse detayı | `Hisse-detayi.dc.html` (+ koyu) |
| `/vakalar` | Vaka çalışmaları | `Vaka-calismalari.dc.html` |
| `/vakalar/[kod]` | Vaka sayfası | `Vaka-IZFAS.dc.html` |
| `/sonuclar` | Sonuçlar | `Sonuclar.dc.html` |
| `/canli-test` | Canlı test | `Canli-test.dc.html` (boş durum + dolu durum) |
| `/yontem` | Yöntem | `Yontem.dc.html` |
| `/hakkinda` | Hakkında | `Hakkinda.dc.html` |

`*-koyu.dc.html` dosyaları açık sürümle aynıdır, yalnızca koyu tema açıktır.
`Mobil-*` dosyaları 390 px genişlikteki yerleşimi gösterir; ayrı sayfa değil,
aynı sayfanın responsive hâlidir.

## Tasarım token'ları

Açık tema:
```
--bg #f5f6f3   --surface #ffffff   --surface-2 #eef1ef
--line #dde2df --line-2 #c5ccc9
--text #13212b --muted #4f5c66     --faint #66727b
--teal #2a9d8f (dolgu)  --teal-ink #1b6f65 (metin/buton)  --teal-soft #e2f1ee
--orange #f4a261 (SPK dönemi bandı, yalnız dolgu)  --orange-ink #8a4a10  --orange-soft #fdeddc
--red #e63946 (alarm / ilk 20 eşiği, yalnız çizgi/dolgu)  --red-ink #b0121e  --red-soft #fce7e9
--green-ink #1d6b2e  --green-soft #e3f2e6   (yakalandı / SPK vakası)
--amber-ink #7a5000  --amber-soft #fbefd2   (2 yıl içinde SPK kararı)
--gray-ink #4b555c   --gray-soft #eceeed    (rastgele / karar yok)
--rand #a3abb0 (rastgele taban grafik dolgusu)
```
Koyu tema: bkz. her dosyadaki `.app.dark` bloğu (`--bg #0c141e`, `--surface #121c28` …).

- Yazı tipi: Inter, `font-feature-settings: "tnum" 1` (tablo rakamları).
- KPI sayıları 40–56 px, 600 ağırlık, `letter-spacing: -.02em`.
- Kartlar: 12 px köşe, 1 px ince kenarlık, gölge yok.
- Kontrast: renkli metinler her zaman `*-ink` tonlarıyla (≥ 4.5:1); saf marka
  renkleri yalnızca dolgu, bant ve çizgilerde.

## Bileşen envanteri

- **TopBar**: logo + yatay nav (aktif sayfa `aria-current`), TR/EN segment, tema düğmesi. Dar ekranda nav sarılır; mobilde hamburger.
- **Footer**: uyarı metni + GitHub + yazar satırı (her sayfada).
- **KpiCard**: etiket, büyük sayı, sistem vs rastgele mini çubuklar, gri "rastgele …" satırı. Genel bakış ve Sonuçlar'da aynı bileşen.
- **Badge**: green / amber / gray / red / teal / orange — her zaman ikon + metin.
- **Chip** (neden etiketi), **SegmentedControl**, **ExampleChip**.
- **Waffle** 10×10 ızgara (`role="img"` + açıklayıcı `aria-label`).
- **SuspicionTable**: Sıra · Hisse/Şirket (satırı seçen `<button>`) · skor çubuğu · nedenler (≤3 chip) · Sonradan SPK rozeti. 50'lik listede 20. satırdan sonra kırmızı kesikli "İlk 20 eşiği" ayırıcı.
- **PreviewPanel**: 6 aylık mini grafik (fiyat + turuncu SPK bandı + kırmızı seçili hafta çizgisi), "Neden şüpheli?" katkı çubukları + düz cümleler, "Hisse detayına git".
- **StockChart (3 panel, ortak zaman ekseni)**: (a) fiyat + turuncu SPK bantları + siyah üçgen SPK kararları (tooltip: tür + tarih) + kırmızı dikey alarm çizgisi; (b) hacim çubukları; (c) haftalık sıra, ters eksen (1 üstte), kesikli "ilk 20" çizgisi. Tarih aralığı seçici (6A/1Y/2Y/Tümü).
- **DecisionTimeline** (dikey), **KapList** (arama + kategori filtresi + etiket), **MilestoneTimeline** (yatay, adımlar arası gün sayıları), **CaseCard**, **Histogram**, **ExperimentLog** tablosu, **EmptyState**.

## Davranış

- Zaman makinesi: hafta seçici (takvim + 2012–2026 kaydırıcı + önceki/sonraki), örnek chip'ler haftayı değiştirir, model segmenti listeyi değiştirir, 10/20/50 liste uzunluğu; satır tıklaması önizleme panelini günceller. Özet kartlar seçili haftaya ve liste uzunluğuna göre hesaplanır (rastgele beklenti = k × SPK dönemindeki hisse sayısı / Nₜ).
- Mobilde tablo yerine satır kartları; dokununca kart içinde açılır (grafik + nedenler).
- TR varsayılan, EN çevirisi i18n anahtarlarıyla. Tema tercihi saklanır.
- Erişilebilirlik: tüm etkileşimler gerçek `<button>`/`<a>`/`<input>`, klavyeyle gezilebilir; her grafikte metin alternatifi.

## İçerik kuralları (değiştirilmemeli)

- Gerçek isim yalnızca SPK vakaları için: IZFAS, SANEL, KGYO, KONYA, KUYAS. Diğer tüm satırlar uydurma kodlar (ABCDE, XYZTR…).
- Her performans sayısının yanında rastgele taban karşılaştırması.
- SPK kararı olmayan hisse için asla "manipüle edildi" ya da "temiz" yazılmaz; rozet "—".
- Zaman makinesi altında: "SPK bağlantısı olmayan hisse masum ya da suçlu anlamına gelmez."

## Yer tutucular / sahte veriler (gerçek veriyle değiştirilecek)

- Sonuçlar: model başına AUC/GA, yakalama, ilk 10 isabeti; histogram değerleri; deneme günlüğü tarihleri.
- KPI "13 ay" kartındaki `rastgele [x] ay`; "ilk karar" medyanı `[x] gün`.
- SANEL ve KGYO için `[x] gün sonra karar`; KONYA/KUYAS dönemleri `[dönem]`.
- IZFAS SPK karar tarihleri ve bülten numaraları `[no]`, KAP listesi, kilometre taşı gün sayıları (45. gün ve %87 hariç).
- Danışman adı, üniversite, GitHub ve tez PDF bağlantıları.
