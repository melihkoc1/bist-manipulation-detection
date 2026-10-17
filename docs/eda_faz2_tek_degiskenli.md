# Faz 2 — Tek Değişkenli Ön Analiz: Özellikler Manipülasyon Dönemlerini Ayırıyor mu?

**Tarih:** 17.10.2026 · **Veri:** 632 hisse, 2014–2026, 1,39 milyon hisse-gün
**Pozitifler:** SPK kararında manipülasyon dönemi açıkça yazan 108 ana set vakası →
3.776 hisse-gün. Diğer tüm hisse-günler "normal" (etiketsiz) kabul edildi.

AUC = rastgele seçilen bir manipülasyon gününün özellik değerinin, rastgele seçilen bir
normal günden yüksek olma olasılığı (0,5 = ayırt etmiyor, 1 = mükemmel).

| Özellik | Medyan (manipülasyon) | Medyan (normal) | AUC |
|---|---:|---:|---:|
| `dist_from_60_low` — 60 günlük dibe uzaklık | 0,502 | 0,140 | **0,791** |
| `ret_20_z` — 20 günlük getiri, oynaklığa göre | 1,422 | 0,058 | **0,769** |
| `excess_ret_20` — XU100'e göre fazla getiri | 0,156 | −0,011 | **0,766** |
| `up_days_10` — son 10 günde yükselen gün | 6 | 4 | 0,731 |
| `close_loc_5` — kapanışın gün içi aralıktaki yeri | 0,583 | 0,440 | 0,707 |
| `value_ratio_5d_60` — 5 günlük hacmin 60 günlük medyana oranı | 2,21 | 1,13 | 0,674 |
| `amihud_60` — sığlık (illikidite) | 0,012 | 0,002 | 0,672 |
| `value_ratio_60` — günlük hacim / 60 günlük medyan | 1,87 | 0,99 | 0,653 |
| `float_turnover_ratio_60` — halka açık devir hızı oranı | 1,51 | 0,97 | 0,609 |
| `limit_up_10` — son 10 günde tavan sayısı | 0 | 0 | 0,559 |
| `log_mcap_usd` — piyasa değeri (USD) | 17,76 | 18,36 | 0,431 ↓ |
| `free_float` — halka açıklık oranı | 0,27 | 0,33 | 0,437 ↓ |

↓ AUC < 0,5: manipülasyon günlerinde değer **daha düşük** (küçük ve sığ hisseler).

## Yorum

- Beklenen "parmak izi" veride görülüyor: yükselen fiyat, artan hacim, günün yükseğine
  yakın kapanış, sığ ve küçük hisse, düşük halka açıklık.
- `close_loc_5` (AUC 0,71): kapanışın sürekli günün yüksek tarafında olması, kapanış
  fiyatına yönelik işlemlere işaret ediyor olabilir.
- Tavan serisi tek başına zayıf (0,56): vakaların çoğunda pompalama tavan tavan değil,
  daha "sessiz" ilerliyor.

## Dikkat (tezde belirtilmeli)

1. **Bu bir model sonucu değil**, tanımlayıcı istatistiktir. Gerçek performans zamana göre
   bölünmüş test setinde ölçülecek.
2. **Kısmi döngüsellik:** SPK'nın incelediği dönemler zaten fiyatın yükseldiği dönemler.
   Getiri özelliklerinin yüksek AUC'si kısmen bu seçimden kaynaklanır. Asıl soru, modelin
   bu dönemlerin **başında** (öncü süre) alarm verip veremediğidir.
3. "Normal" günlerin bir kısmı aslında yakalanmamış manipülasyon olabilir (PU learning
   motivasyonu). Bu, AUC'yi aşağı çeker; gerçek ayrışma muhtemelen daha güçlüdür.

Kod: `src/bistmd/features/price.py` · Çıktı: `data/interim/features_price_preview.parquet`
