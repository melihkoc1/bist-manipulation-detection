# BIST Manipülasyon Tespiti — Proje Planı

> Çalışma adı: **Günlük Piyasa ve KAP Verisiyle BIST'te Piyasa Bozucu Eylemlerin Erken Tespiti**
> Durum: Faz 0 (envanter) — Ekim 2026

---

# BÖLÜM A — Basit Dille Plan

## Proje ne yapıyor? (tek paragraf)

Borsa İstanbul'da bazı küçük hisseler, bir grup tarafından koordineli alımlarla yapay olarak yükseltilir, küçük yatırımcı içeri girince de grup satıp çıkar ("pompala-boşalt", halk arasında "tahtacılık"). SPK bunları aylar ya da yıllar sonra tespit edip bültenlerinde yayımlıyor. Bu proje, **SPK'nın geçmişte yakaladığı vakalardan öğrenerek**, her gün her hisseye bir **"olağandışılık skoru"** veren bir sistem kuruyor. Amaç, şüpheli hareketi SPK kararından çok önce, mümkünse fiyat zirve yapmadan önce fark edebilmek.

## Nasıl çalışacak? (6 adım)

1. **Geçmiş vakaları topla.** SPK bültenlerini tarayıp "hangi hisse, hangi tarihte, ne tür karar (işlem yasağı / para cezası / suç duyurusu)" tablosunu çıkar. Bu tablo modelin "doğru cevap anahtarı".
2. **Piyasa verisini topla.** Tüm hisselerin günlük fiyat-hacim verisi, KAP bildirimleri (şirket haberleri ve Borsa tedbirleri), halka açıklık oranları.
3. **Her hisse için her gün "parmak izi" hesapla.** Hacim normalin kaç katı? Kaç gündür tavan? Piyasa düşerken tek başına mı yükseliyor? Bu yükselişi açıklayan bir haber var mı? Hisse ne kadar küçük ve sığ?
4. **Modelleri eğit ve karşılaştır.** Üç yaklaşım: (a) etiketsiz "olağandışı olanı bul", (b) SPK etiketleriyle klasik öğrenme, (c) "SPK'nın yakalamadığı her hisse temiz değildir" varsayımıyla çalışan PU learning. Hepsini Borsa'nın kendi kural tabanlı sistemiyle kıyasla.
5. **Dürüstçe test et.** Modeli geçmiş yıllarla eğit, sonraki yıllarda dene. Sorulan soru: "SPK'nın yasak getirdiği hisselerde model alarmı **ne kadar önce** verdi?" Ayrıca modeli 2024 sonunda dondurup 2025–2026 kararlarını önceden görüp görmediğine bak.
6. **Sonucu görünür yap.** Her alarm için gerekçe üret ("hacim 12 kat, 6 gündür tavan, KAP'ta haber yok, halka açıklık %8") ve bunu bir dashboard'da göster.

## Tezin cevaplayacağı sorular

1. Günlük fiyat, hacim ve KAP verisiyle manipülasyon dönemleri **ne kadar erken** tespit edilebilir?
2. Etiketlerin eksik olduğu bu durumda **PU learning**, klasik gözetimli ve gözetimsiz yöntemlerden daha iyi mi?
3. **"Habersiz hareket"** bilgisi (KAP'ta gerekçe yokken fiyat patlaması) tespite ne kadar katkı sağlıyor?
4. *(Opsiyonel)* Aracı kurum dağılımı (AKD) verisi erişilebilirse, tespiti ne kadar iyileştiriyor?

## Neyi yapmıyoruz (sınırlılıklar)

- Sahte emir (spoofing) ve kendi kendine alım-satım (wash trading): emir defteri ve hesap verisi gerektirir, bizde yok.
- Gün içi manipülasyon: sadece günlük veri kullanıyoruz.
- Model **suçlama yapmaz**; sadece istatistiksel anomali skoru üretir. SPK kararı olmayan hiçbir hisse tezde veya sitede "manipüle edildi" diye isimlendirilmez.

## Zaman çizelgesi (Ekim 2026 – Haziran 2027, akademik takvime göre ayarlanır)

| Dönem | Faz | Çıktı |
|---|---|---|
| Ekim (2 hafta) | **0 — Envanter** | Kaç SPK vakası var, kaçının fiyat verisi var → **devam / dur kararı** |
| Kasım | 1 — Veri hattı | Fiyat, KAP, halka açıklık verisi tek veritabanında |
| Aralık | 2 — Etiketler + özellikler | Doğrulanmış etiket tablosu, günlük özellik paneli |
| Ocak – Şubat | 3 — Modeller | Baseline + 3 model, zaman bazlı değerlendirme |
| Mart | 4 — Analiz | Habersiz hareket katkısı, sağlamlık testleri, SHAP |
| Nisan | 5 — Ürün | Günlük çalışan sistem + dashboard |
| Mart – Mayıs | 6 — Tez yazımı | Tez metni (yazım Faz 2'den itibaren paralel yürür) |

**Devam/dur eşiği (Faz 0 sonunda):**
fiyat verisi bulunan farklı olay sayısı **≥ 40 → devam**, **20–40 → gözetimsiz/PU ağırlıklı devam**, **< 20 → çerçeveyi yeniden düşün**.

---

# BÖLÜM B — Teknik Plan

## B1. Teknoloji yığını

| Katman | Seçim | Neden |
|---|---|---|
| Dil | Python 3.11+ | Ekosistem |
| Paket yönetimi | `uv` | Hızlı, kilit dosyası |
| Veri işleme | `pandas` (gerekirse `polars`) | Standart |
| Depolama | **DuckDB** (tek dosya) + ham dosyalar `data/raw/` | Sunucusuz, SQL, Parquet ile uyumlu |
| PDF | `pymupdf` / `pdfplumber` | Bülten metni çıkarma |
| Etiket çıkarma | Kural tabanlı regex + **LLM (Claude API, yapılandırılmış çıktı)** | Hisse kodu, karar türü, dönem |
| ML | `scikit-learn`, `lightgbm`, PU için kendi Elkan–Noto + nnPU implementasyonu | Kontrol ve şeffaflık |
| Açıklanabilirlik | `shap` | Alarm gerekçeleri |
| Dashboard | `streamlit` | Hızlı prototip |
| Zamanlama | GitHub Actions cron veya küçük VPS + cron | Günlük çalışma |
| Test | `pytest` | Özellikle sızıntı testleri |

## B2. Veri kaynakları

| Veri | Kaynak (aday) | Erişim | Risk |
|---|---|---|---|
| SPK kararları | spk.gov.tr → Bültenler (PDF) | Ücretsiz, scraping | PDF formatı yıllar içinde değişmiş olabilir |
| Günlük OHLCV | İş Yatırım tarihsel veri, Yahoo `.IS` | Ücretsiz | **İşlemden kalkan hisseler eksik olabilir** |
| Endeks / sektör | XU100, XUTUM, sektör endeksleri | Ücretsiz | — |
| KAP bildirimleri | kap.org.tr | Ücretsiz, scraping | Rate limit, yapı değişikliği |
| Borsa tedbirleri | KAP'ta Borsa İstanbul duyuruları (VBTS, brüt takas, tek fiyat) | Ücretsiz | Metin ayrıştırma |
| Fiili dolaşım oranı | MKK | Ücretsiz | Geçmiş seri derinliği belirsiz |
| Sermaye / piyasa değeri | KAP şirket bilgileri | Ücretsiz | Bedelsiz/bölünme düzeltmeleri |
| Google Trends | `pytrends` | Ücretsiz (gayriresmî) | Kararsız |
| AKD / takas | Matriks, Foreks | **Ücretli** — hocadan/üniversiteden sorulacak | Opsiyonel |

> Faz 0'da her kaynak için küçük bir erişim denemesi yapılır; çalışmayan kaynak alternatifiyle değiştirilir.

## B3. Veri modeli (DuckDB tabloları)

```text
events            -- SPK kararları (etiket kaynağı)
  event_id, ticker, company_name, bulletin_no, bulletin_date,
  decision_type        -- 'tedbir' | 'idari_para_cezasi' | 'suc_duyurusu' | 'diger'
  period_start, period_end  -- bültende yazıyorsa, yoksa NULL
  n_persons, fine_amount_try,
  source_url, page_no, raw_text,
  extraction_method    -- 'regex' | 'llm' | 'manual'
  verified             -- elle kontrol edildi mi

prices            -- ticker, date, open, high, low, close, adj_close, volume, value_try
index_prices      -- index_code, date, close
kap_disclosures   -- disclosure_id, ticker, published_at (timestamp!), category, title, body, llm_class
market_measures   -- ticker, measure_type, start_date, end_date, source_disclosure_id
free_float        -- ticker, date, free_float_ratio
company_profile   -- ticker, date, shares_outstanding, sector
features          -- ticker, date, <özellik sütunları>, feature_version
labels            -- ticker, date, label_window ('3m'|'6m'|'12m'), label_tier, is_positive
scores            -- ticker, date, model_id, score, rank, shap_top_k (json)
```

## B4. Etiket çıkarma hattı

1. **İndir:** Tüm bülten PDF'lerini `data/raw/spk_bulletins/` altına indir (hedef: 2015–2026).
2. **Metne çevir:** Sayfa bazında metin ve sayfa numarası.
3. **Aday bölümleri bul:** "işlem yasağı", "piyasa bozucu", "6362 sayılı ... 104/106/107", "idari para cezası", "suç duyurusu" anahtar ifadeleriyle.
4. **Yapılandırılmış çıkarım:** LLM'e bölüm metni verilir, sabit bir JSON şemasıyla dönüş alınır (hisse kodu, karar türü, dönem, kişi sayısı, ceza tutarı). Regex ile çapraz kontrol.
5. **Doğrula:** Rastgele %20 + tüm düşük güvenli kayıtlar elle kontrol. **Çıkarımın doğruluk oranı tezde raporlanır** (bu da kendi başına bir sonuç).
6. **Katmanlandır:** `tier_1` = suç duyurusu / para cezası, `tier_2` = sadece tedbir.

## B5. Etiketleri günlere yayma

Bülten çoğu zaman manipülasyon dönemini vermez. Bu yüzden:

- **Dönem yazıyorsa:** doğrudan kullan.
- **Yazmıyorsa:** karar tarihinden önceki **3 / 6 / 12 ay** pencereleri (üçü de raporlanır).
- **Daraltma (sadece etiketleme için):** Pencere içindeki yükseliş+çöküş örüntüsü ile aktif dönem daraltılır. Bu bilgi **asla özellik olarak kullanılmaz**.

## B6. Özellikler (her hisse × her gün)

**Altın kural:** `t` günündeki özellik sadece `t` gününe kadar (dahil) olan bilgiyi kullanır. Seans kapanışından sonra yayımlanan KAP bildirimi `t+1`'e atanır. Bunun için otomatik sızıntı testi yazılır.

| Grup | Örnek özellikler |
|---|---|
| Hacim | `vol_ratio_20/60`, hacim ivmesi (ardışık artış günleri), devir hızı = hacim / halka açık lot |
| Fiyat | `ret_1/5/20`, volatiliteye göre z-skor, ardışık tavan günü, gap sayısı |
| Kapanış davranışı | `close_loc = (C−L)/(H−L)` ve 5 günlük ortalaması |
| Göreli hareket | XU100'e ve sektör endeksine göre artık getiri, rolling beta sapması |
| Likidite / profil | Amihud illikidite, piyasa değeri, halka açıklık oranı, işlem gören gün oranı |
| Habersiz hareket | Son N günde önemli KAP bildirimi var mı / türü, `abs_ret_20` ÷ (1 + haber sayısı) |
| Bildirim türü | Bedelsiz duyurusu, "yeni iş ilişkisi" vb. (LLM ile sınıflandırılmış) |
| Borsa tedbiri | Aktif tedbir var mı, son 90 günde kaç tedbir (sızıntı analizine tabi) |
| İlgi (opsiyonel) | Google Trends z-skoru |

## B7. Modeller

| # | Model | Rolü |
|---|---|---|
| 0a | **Kural tabanlı baseline** (VBTS benzeri eşikler) | "Borsa'nın mevcut yaklaşımını geçiyor muyuz?" |
| 0b | Basit skor: hacim oranı × getiri z-skoru | Akıl sağlığı kontrolü |
| 1 | Isolation Forest | Gözetimsiz |
| 2 | LightGBM | Gözetimli (etiketsizler = negatif) |
| 3 | **PU learning** — Elkan–Noto (LightGBM tabanlı) + nnPU | Ana katkı |

Kapsam dışı, zaman kalırsa: autoencoder, change-point detection, ABD mikro-cap dış doğrulama.

## B8. Değerlendirme protokolü

- **Zaman bölmesi** (Faz 0 sonucuna göre kesinleşir):
  `train ≤ 2021` · `val 2022` · `test 2023–2024` · `ileriye dönük 2025–2026`
  Etiket gecikmesi nedeniyle son dönem eksik pozitif içerir → ayrıca raporlanır.
- **Olay bazlı metrikler:**
  - *Event recall@k:* Karar öncesi penceresinde hissenin en az bir gün haftalık top-k listesine girme oranı (k = 10, 20, 50).
  - *Lead time:* İlk alarm ile karar tarihi / fiyat zirvesi arasındaki gün farkı. Zirveden önce alarm oranı.
- **Liste bazlı metrik:** Haftalık *precision@k* (analist perspektifi).
- **Sağlamlık:** Pencere (3/6/12 ay) × etiket katmanı (tier 1 / tümü) matrisi; bootstrap %95 güven aralıkları; sentetik pompalama enjeksiyonu.
- **Ablation:** Habersiz hareket özellikleri çıkarılınca performans farkı (Soru 3).
- **Vaka analizi:** Etiketsiz en yüksek skorlu örnekler isimsiz olarak "açıklanamayan anomaliler" başlığıyla.

## B9. Ürün (Faz 5)

```text
Her işlem günü 19:00
  ingest_prices → ingest_kap → build_features → score → explain → publish
```

- **Herkese açık:** Sadece geçmiş vakaların vitrini (SPK kararı açıklanmış hisseler, modelin alarm zaman çizelgesi).
- **Şifreli:** Günlük canlı skor listesi.
- Her yerde "istatistiksel anomali skoru" ifadesi ve sorumluluk reddi. Yayına almadan önce hoca ve hukuki görüş.

## B10. Repo yapısı

```text
Manipulation Detection/
├── PLAN.md
├── README.md
├── pyproject.toml
├── .env.example            # API anahtarları (gerçek değerler .env'de, git dışında)
├── data/
│   ├── raw/                # İndirilen PDF/HTML/CSV (git dışında)
│   ├── interim/
│   └── db/bist.duckdb
├── src/bistmd/
│   ├── ingest/             # spk.py, prices.py, kap.py, mkk.py
│   ├── labels/             # extract.py, schema.py, windows.py
│   ├── features/           # volume.py, price.py, news.py, profile.py
│   ├── models/             # baselines.py, iforest.py, lgbm.py, pu.py
│   ├── eval/               # splits.py, metrics.py, robustness.py
│   └── app/                # streamlit dashboard
├── notebooks/              # Keşif, grafik (tezde kullanılacak)
├── tests/                  # Sızıntı testleri dahil
└── thesis/                 # Tez taslakları, şekiller
```

## B11. Faz 0 — İlk iki haftanın somut görevleri

- [ ] SPK bülten arşiv sayfasının yapısını incele, tüm PDF linklerini topla (2015–2026)
- [ ] PDF'leri indir, metne çevir
- [ ] Anahtar ifadelerle aday karar bölümlerini çıkar
- [ ] İlk 30 kararı elle tablola → çıkarım şemasını netleştir
- [ ] Tüm bültenlere otomatik çıkarım uygula → `events` tablosu
- [ ] Her hisse kodu için fiyat verisi var mı kontrol et (İş Yatırım + Yahoo)
- [ ] Envanter raporu: yıl × karar türü dağılımı, farklı hisse sayısı, fiyat verisi kapsama oranı
- [ ] **Devam / dur kararı** → hocayla görüşme
