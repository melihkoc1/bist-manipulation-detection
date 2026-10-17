# BIST Manipülasyon Tespiti

Günlük piyasa ve KAP verisiyle Borsa İstanbul'da piyasa bozucu eylemlerin erken tespiti
(lisans bitirme projesi). Plan: [PLAN.md](PLAN.md).

> Model çıktıları **istatistiksel anomali skorudur**, suçlama değildir. SPK kararı
> bulunmayan hiçbir hisse "manipüle edildi" olarak nitelendirilmez.

## Kurulum

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"   # Windows
```

## Faz 0 — Etiket envanteri

```bash
python -m bistmd.ingest.spk_api --start 2016 --end 2026      # SPK idari yaptırımlar API'si
python -m bistmd.ingest.spk_bulletins --start 2016 --end 2026 # SPK bülten PDF'leri (~1 saat)
python -m bistmd.ingest.universe                              # KAP güncel şirket listesi
python scripts/inventory.py                                   # birleştir + fiyat kapsaması
```

Çıktı: `data/interim/inventory.md`, `spk_decisions.parquet`, `spk_cases.parquet`.
Etiket doğrulaması: [docs/validation_faz0.md](docs/validation_faz0.md).

## Faz 1 — Veri hattı

```bash
python -c "from bistmd.ingest import universe, prices_isyatirim as p; p.download(sorted(universe.load().ticker))"  # ~4 saat
python -m bistmd.ingest.kap_disclosures --start 2010-01-01   # KAP bildirimleri (~1-2 saat)
python -m bistmd.db                                          # data/db/bist.duckdb
```

KAP bildirimlerinin `effective_date` alanı, bilginin fiyatlanabildiği ilk işlem günüdür
(18:00 sonrası ve tatil günü bildirimleri bir sonraki işlem gününe atanır).

## Veri kaynakları

| Veri | Kaynak | Not |
|---|---|---|
| SPK kararları | idariyaptirimlar.spk.gov.tr API + SPK bültenleri | Bültenler dönem bilgisini de içeriyor |
| Günlük fiyat | İş Yatırım | İşlemden kalkan hisseler dahil; piyasa değeri ve halka açık PD aynı yanıtta |
| Şirket listesi | KAP | Yalnızca güncel şirketler |
| KAP bildirimleri | kap.org.tr bildirim sorgu API'si | Üst veri (saat, konu, özet); sorgu başına 2.000 kayıt sınırı → günlük sorgu |

Kod değişiklikleri (ör. KOZAL → TRALT) `config/ticker_aliases.csv` dosyasında elle tutulur.

## Gizlilik

SPK kayıtlarındaki kişi adı, TCKN ve MKK sicil bilgileri işlenmiş tablolara taşınmaz.
Ham veriler (`data/`) repoya eklenmez.

## Testler

```bash
python -m pytest
```
