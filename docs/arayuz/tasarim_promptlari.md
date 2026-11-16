# Tasarım araçları için hazır metinler

Ayrıntılı plan: [tasarim_plani.md](tasarim_plani.md). Aşağıdaki metinler İngilizce talimat + Türkçe arayüz
yazıları içerir; araçlar İngilizce talimatı daha iyi anlıyor.

---

## A. Claude Design — tek seferde tüm site

Aşağıdaki metnin tamamını kopyalayıp yapıştırın.

```text
Design a multi-page web app for my undergraduate thesis project: an early-warning system that detects
pump-and-dump stock manipulation on Borsa Istanbul (BIST) using daily market data, company disclosures
(KAP) and enforcement decisions of Turkey's Capital Markets Board (SPK). Every week the system ranks all
listed stocks (300–600 per week) by how suspicious their trading looks, and it was evaluated against real
SPK cases from 2012–2026.

AUDIENCE: my thesis advisor and jury, potential employers (banks, brokerages, regulators), and me.
TONE: serious, calm, trustworthy — like a bank's risk-surveillance dashboard or a regulator's report.
Not flashy, not crypto-style. Desktop-first (used in presentations), responsive down to mobile.
UI LANGUAGE: Turkish by default, with a TR/EN switch in the header. Use the Turkish copy given below.

GLOBAL LAYOUT
- Top bar: logo/name "BIST Manipülasyon Tespiti", horizontal nav, TR/EN toggle, light/dark toggle.
- Nav items: Genel bakış · Zaman makinesi · Hisse detayı · Vaka çalışmaları · Sonuçlar · Canlı test · Yöntem · Hakkında
- Footer on every page: "Skorlar istatistiksel anomali sinyalidir, suçlama değildir. Yatırım tavsiyesi
  değildir." + GitHub link + "Melih Erdem Koçoğlu · Yazılım Mühendisliği Bitirme Projesi 2026–2027".

VISUAL LANGUAGE
- Background off-white (light) / deep navy-charcoal (dark). Primary: dark teal (#2a9d8f).
- Semantic colors used consistently everywhere:
  orange #f4a261 = manipulation period stated by SPK; red #e63946 = system alarm / top-20 threshold;
  green = caught / matched an SPK case; gray = random baseline / no SPK decision.
  Never rely on color alone: badges also carry an icon and text.
- Font: Inter (or IBM Plex Sans), tabular numerals; big KPI numbers 40–56px.
- Cards with 12px radius, hairline borders, no heavy shadows. Clean, minimal charts.

PAGES
1) Genel bakış (landing)
- Hero: "Borsa İstanbul'da manipülasyonu SPK'dan önce fark eden erken uyarı sistemi", one-line
  subtitle, buttons "Zaman makinesini dene" and "Nasıl çalışıyor?".
- 4 KPI cards, each with a small gray "random" comparison:
  "Yakalanan vaka %67 (rastgele %23)", "Fiyat zirvesinden önce %66 (rastgele %20)",
  "SPK'nın ilk cezasından medyan 13 ay önce", "AUC 0,85 (0,5 = rastgele)".
- Explainer "Rastgeleden 3 kat iyi ne demek?": two pairs of 10×10 waffle grids —
  100 cases: system 67 vs random 23; 100 alarms: about 10 are SPK cases vs random 3.
- "Nasıl çalışıyor" 4-step horizontal strip with icons: SPK kararları → Göstergeler → Modeller → Haftalık liste.
- Featured case card: IZFAS 2018 with a sparkline: "45. günde alarm; SPK tedbirinden sonra fiyat %87 düştü".
- Data strip: "17 yıl SPK bülteni · 657 vaka · 775 bin KAP bildirimi · her hafta 300–600 hisse".

2) Zaman makinesi (most important, data-dense dashboard)
- Control bar: week picker (calendar + 2012–2026 timeline slider + prev/next arrows), example chips
  "IZFAS · Haz 2018", "SANEL · May 2019", "KGYO · Tem 2022", model segmented control
  "Kural + PU (önerilen) / Kurallar / PU öğrenme", list length 10/20/50.
- 3 small summary cards: "SPK manipülasyon dönemindeki hisse 1 / 20 (rastgele beklenti 0,1)",
  "O hafta puanlanan hisse 385", "02.06 – 08.06.2018".
- Main table: Sıra · Hisse · Şirket · Şüphe skoru (horizontal bar) · Nedenler (up to 3 small chips such as
  "Hacim 7×", "10 günün 9'u yükseliş", "Haber yok") · Sonradan SPK (badge).
  Badges: green "SPK dönemi · 27 gün sonra karar", amber "2 yıl içinde SPK kararı", gray "—".
  Never label a stock "clean" or "innocent".
- Clicking a row opens a right-side preview panel: 6-month mini chart (price + orange SPK band),
  "Neden şüpheli?" contribution bars, button "Hisse detayına git".
- Footnote: "SPK bağlantısı olmayan hisse masum ya da suçlu anlamına gelmez."

3) Hisse detayı
- Header: big ticker, company name, "N SPK kararı" badge, stock search box.
- KPI cards: best weekly rank, weeks in top 20, number of SPK decisions.
- Main chart with date-range selector and shared time axis, 3 stacked panels:
  (a) price line + orange bands for SPK-stated manipulation periods + black triangle markers for SPK
  decisions (tooltip: type and date) + red vertical line for the selected week/first alarm;
  (b) volume bars; (c) weekly rank with inverted axis (1 on top) and dashed "ilk 20" line.
- "Neden şüpheli?" panel for the selected week: horizontal contribution bars + plain-language sentences.
- SPK decisions vertical timeline: date, type (Suç duyurusu / İdari para cezası / İşlem yasağı / Tedbir),
  stated period, bulletin number.
- KAP disclosures: searchable list with category tags (Gerçek haber / Fiyat hareketi açıklaması / Söylenti / Diğer).

4) Vaka çalışmaları
- Card grid with filter Tümü / Yakalanan / Kaçırılan. Each card: ticker, period, sparkline, status tag
  ("Yakalandı" green / "Kaçırıldı" gray), one sentence.
- Case page (story layout): horizontal milestone timeline "Manipülasyon başladı → İlk alarm (45. gün) →
  Fiyat zirvesi → SPK tedbiri → SPK cezası" with day counts between steps; the big 3-panel chart;
  boxes "Sistem ne gördü?" and "Ders".
- Cases: IZFAS, SANEL, KGYO (caught); KONYA, KUYAS (missed).

5) Sonuçlar
- Period segmented control: 2017–2026 (ana) / 2017–2021 / 2022–2026 / 2012–2016 / 2012–2026.
- KPI cards (same component as landing).
- Grouped bar chart per model: "yakalama" vs "rastgele beklenti"; table below with columns
  AUC [95% CI] · İlk 20'de yakalama · Rastgele · × rastgele · Zirveden önce · İlk 10 isabeti.
  Models: Rastgele, Kurallar, Isolation Forest, LightGBM, PU öğrenme (ağırlıklı), PU öğrenme (bagging),
  Kural + PU (en iyi, highlighted row).
- Histogram "SPK'ya göre zaman": days from first alarm to SPK's first decision / first fine.
- 3 thesis-question cards with answer badges: "Erken tespit mümkün mü? — Evet",
  "PU öğrenme daha iyi mi? — Kısmen", "Habersiz hareket işe yarıyor mu? — Hayır".
- "Deneme günlüğü" table: idea · result (✓ işe yaradı / ✗ katkı yok) · effect (e.g. "AUC +0,05, anlamlı") · date.
  Example rows: "Eski SPK bültenleri (2009–2015) ✓ AUC +0,05", "Kural + PU birleşimi ✓ en iyi model",
  "Kapanış/VWAP göstergeleri ✗", "Piyasa geneline göre göstergeler ✗", "Dönemi bilinmeyen vakaları tahminle etiketleme ✗".

6) Canlı test (coming soon)
- Explanation: "Model donduruldu; her haftanın listesi kaydediliyor ve Haziran 2027'de SPK kararlarıyla karşılaştırılacak."
- Counters: kaydedilen hafta, listeye giren farklı hisse, sonradan SPK kararı gelen.
- Weekly log list. Design an empty state: "İlk hafta kaydı bekleniyor".

7) Yöntem
- Flow diagram: data sources → labels / features → models → weekly ranking → evaluation.
- 4 step cards (Etiketler, Göstergeler, Modeller, Dürüst değerlendirme).
- Box "Rastgele taban nedir?" with a short formula 1 − Π(1 − k/Nₜ) and a tiny example.
- Highlighted story box "İlk hatamız": the first result was not better than random; it was retracted
  and the evaluation rebuilt.
- Data sources table, limitations list, ethics principles.

8) Hakkında
- Project, author (Melih Erdem Koçoğlu), advisor placeholder, GitHub and thesis PDF links.

CONTENT RULES
- In mock data, use real names only for the public SPK cases IZFAS, SANEL, KGYO, KONYA, KUYAS.
  For all other rows use invented tickers (e.g. ABCDE, XYZTR, KLMNO).
- Every performance number appears next to its random-baseline comparison.
- Never write "manipüle edildi" or "temiz" for stocks without an SPK decision.
- Accessible contrast, keyboard navigation, text alternatives for charts.

Deliver: the 8 pages in light mode, plus Zaman makinesi and Hisse detayı in dark mode, at desktop width
(1440px), and Genel bakış + Zaman makinesi at mobile width.
```

---

## B. Google Stitch — ekran ekran

Stitch en iyi sonucu tek ekranlık kısa talimatlarla veriyor. Önce 1 numaralı ortak tarzı, sonra her
ekranı ayrı ayrı yapıştırın. Her ekrandan sonra "Use the same style as the previous screen" ekleyin.

**1. Ortak tarz**

```text
Professional financial-surveillance web dashboard, desktop 1440px, calm and trustworthy (bank risk
panel style, not crypto). Off-white background, dark teal primary (#2a9d8f). Semantic colors: orange
#f4a261 = SPK manipulation period, red #e63946 = alarm, green = caught, gray = random baseline.
Inter font, tabular numbers, 12px rounded cards, hairline borders, minimal charts. Turkish UI text.
Top nav: "BIST Manipülasyon Tespiti" | Genel bakış · Zaman makinesi · Hisse detayı · Vaka çalışmaları ·
Sonuçlar · Canlı test · Yöntem · Hakkında | TR/EN toggle. Footer disclaimer: "Skorlar istatistiksel
anomali sinyalidir, suçlama değildir. Yatırım tavsiyesi değildir."
```

**2. Genel bakış**

```text
Landing page. Hero title "Borsa İstanbul'da manipülasyonu SPK'dan önce fark eden erken uyarı sistemi",
buttons "Zaman makinesini dene" and "Nasıl çalışıyor?". Row of 4 KPI cards with gray random comparison:
"Yakalanan vaka %67 (rastgele %23)", "Fiyat zirvesinden önce %66 (rastgele %20)",
"SPK'nın ilk cezasından medyan 13 ay önce", "AUC 0,85 (0,5 = rastgele)". Section "Rastgeleden 3 kat iyi
ne demek?" with two pairs of 10x10 waffle grids (67 vs 23 out of 100 cases; 10 vs 3 out of 100 alarms).
4-step strip with icons: SPK kararları → Göstergeler → Modeller → Haftalık liste. Featured case card
"IZFAS 2018" with sparkline and text "45. günde alarm; SPK tedbirinden sonra fiyat %87 düştü".
```

**3. Zaman makinesi**

```text
Data-dense dashboard "Zaman makinesi". Control bar: week picker with 2012–2026 timeline slider and
prev/next arrows, chips "IZFAS · Haz 2018", "SANEL · May 2019", "KGYO · Tem 2022", segmented control
"Kural + PU / Kurallar / PU öğrenme", list length 10/20/50. Three summary cards: "SPK manipülasyon
dönemindeki hisse 1 / 20 (rastgele beklenti 0,1)", "O hafta puanlanan hisse 385", "02.06 – 08.06.2018".
Table of 20 rows: Sıra, Hisse, Şirket, Şüphe skoru (horizontal bar), Nedenler (small chips like
"Hacim 7×", "Haber yok"), Sonradan SPK (green badge "SPK dönemi · 27 gün sonra karar", amber badge
"2 yıl içinde SPK kararı", or gray "—"). Row 3 is IZFAS with the green badge; other rows use invented
tickers. Right side panel for the selected row: mini price chart with an orange band, "Neden şüpheli?"
bars, button "Hisse detayına git".
```

**4. Hisse detayı**

```text
Stock detail page for "IZFAS — İzmir Fırça Sanayi ve Ticaret A.Ş." with badge "6 SPK kararı" and a
search box. Three KPI cards: "En iyi haftalık sıra 1", "İlk 20'de geçen hafta 25", "SPK kararı 6".
Large chart with date-range selector and three stacked panels sharing a time axis: price line with an
orange band (03.2018–07.2018) and black triangle markers for SPK decisions, red vertical line at the
first alarm; volume bars; weekly rank with inverted axis and a dashed "ilk 20" line. Side panel
"Neden şüpheli?" with horizontal contribution bars. Below: vertical timeline of SPK decisions
(05.07.2018 İşlem yasağı, 27.12.2018 Suç duyurusu, 27.12.2018 İdari para cezası) and a searchable list
of KAP disclosures with category tags.
```

**5. Vaka çalışmaları (liste + vaka sayfası)**

```text
Case studies page: filter tabs "Tümü / Yakalanan / Kaçırılan" and a grid of 5 cards (IZFAS, SANEL,
KGYO tagged green "Yakalandı"; KONYA, KUYAS tagged gray "Kaçırıldı"), each with period, sparkline and
one sentence. Then a case detail view for IZFAS: horizontal milestone timeline "Manipülasyon başladı →
İlk alarm (45. gün) → Fiyat zirvesi → SPK işlem yasağı (+55 gün) → SPK cezası (+230 gün)", a large
price chart with orange period band, and two boxes "Sistem ne gördü?" and "Ders".
```

**6. Sonuçlar**

```text
Results page. Period segmented control "2017–2026 / 2017–2021 / 2022–2026 / 2012–2016 / 2012–2026".
KPI cards. Grouped bar chart: for each model (Rastgele, Kurallar, Isolation Forest, LightGBM,
PU öğrenme, Kural + PU) teal bar "yakalama" next to gray bar "rastgele beklenti" (values 22/23, 65/23,
54/23, 59/23, 62/23, 67/23 %). Table below with AUC and confidence intervals; "Kural + PU" row
highlighted. Histogram "İlk alarmdan SPK kararına kadar geçen gün". Three thesis question cards with
answer badges Evet / Kısmen / Hayır. Table "Deneme günlüğü" with ✓/✗ results.
```

**7. Yöntem ve Canlı test**

```text
Method page: horizontal flow diagram (Veri kaynakları → Etiketler / Göstergeler → Modeller → Haftalık
sıralama → Değerlendirme), four step cards, an info box "Rastgele taban nedir?" with a formula, and a
highlighted story box "İlk hatamız". Separate screen "Canlı test": explanation text, three counters
(kaydedilen hafta, listeye giren hisse, sonradan SPK kararı gelen) and an empty state
"İlk hafta kaydı bekleniyor".
```
