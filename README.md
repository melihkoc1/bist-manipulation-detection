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

## Veri kaynakları

| Veri | Kaynak | Not |
|---|---|---|
| SPK kararları | idariyaptirimlar.spk.gov.tr API + SPK bültenleri | Bültenler dönem bilgisini de içeriyor |
| Günlük fiyat | İş Yatırım | İşlemden kalkan hisseler dahil; piyasa değeri ve halka açık PD aynı yanıtta |
| Şirket listesi | KAP | Yalnızca güncel şirketler |

Kod değişiklikleri (ör. KOZAL → TRALT) `config/ticker_aliases.csv` dosyasında elle tutulur.

## Gizlilik

SPK kayıtlarındaki kişi adı, TCKN ve MKK sicil bilgileri işlenmiş tablolara taşınmaz.
Ham veriler (`data/`) repoya eklenmez.

## Testler

```bash
python -m pytest
```
