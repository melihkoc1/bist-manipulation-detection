# PU modelinin açıklamaları (SHAP)

`scripts/explain_v2.py` üretir; yorum `docs/yorum_v2.md`.

Dürüst yıllık PU bagging modelleri (15 torba LightGBM) aynı tohumla yeniden eğitildi; katkılar LightGBM'in yerleşik TreeSHAP'i ile log-odds ölçeğinde, torba ortalaması.

**Yeniden üretim kontrolü:** 52,594 hisse-haftada yeniden eğitilen skor ile kayıtlı skor arasındaki en büyük fark 0.00e+00 (ortalama 0.00e+00).

## Genel önem: göstergenin ortalama |katkı| payı

İlk dört sütun: her yıldan rastgele 20.000 hisse-gün. "İlk 50 satırlarında": haftalık ilk 50'ye giren hisse-haftaların en şüpheli günü. Son sütun: ilk 50'de göstergenin skoru yukarı ittiği satır oranı.

|                         | 2012–2016   | 2017–2021   | 2022–2026   | Tümü   | İlk 50 satırlarında   | İlk 50'de yukarı itme %   |
|:------------------------|:------------|:------------|:------------|:-------|:----------------------|:--------------------------|
| Halka açık devir (hafta) (`float_turnover_5`) | %21.8       | %22.2       | %18.0       | %20.7  | %17.2                 | %89                       |
| 3 aylık dipten yükseliş (`dist_from_60_low`) | %11.4       | %15.0       | %13.6       | %13.4  | %18.1                 | %78                       |
| 3 aylık getiri (`ret_60`) | %5.2        | %6.9        | %3.3        | %5.2   | %7.1                  | %70                       |
| Halka açık devir (gün) (`float_turnover`) | %5.8        | %5.6        | %3.8        | %5.1   | %4.3                  | %88                       |
| 10 günde ortalamanın üstünde kapanış (`close_above_vwap_10`) | %4.1        | %5.7        | %4.8        | %4.9   | %5.5                  | %72                       |
| Günlük oynaklık (1 ay) (`vol_20`) | %7.3        | %3.9        | %2.5        | %4.5   | %4.3                  | %63                       |
| Piyasanın aylık getirisi (`xu_ret_20`) | %3.1        | %3.4        | %6.8        | %4.4   | %2.8                  | %65                       |
| 3 aylık zirveden uzaklık (`drawdown_from_60_high`) | %5.3        | %3.7        | %3.3        | %4.1   | %2.8                  | %53                       |
| Haftalık hacim / 3 ay normali (`value_ratio_5d_60`) | %3.6        | %3.3        | %2.8        | %3.2   | %3.1                  | %41                       |
| Endeks üstü getiri (1 ay) (`excess_ret_20`) | %3.7        | %2.2        | %3.8        | %3.2   | %3.5                  | %73                       |
| Kapanış / ortalama fiyat (hafta) (`close_vs_vwap_5`) | %1.7        | %2.8        | %4.4        | %3.0   | %3.3                  | %71                       |
| 10 günde yükselen gün (`up_days_10`) | %2.3        | %2.3        | %3.7        | %2.8   | %3.5                  | %59                       |
| Oynaklık artışı (`vol_ratio_20_60`) | %3.4        | %2.1        | %2.6        | %2.7   | %2.8                  | %48                       |
| Hafta boyu tepede kapanış (`close_loc_5`) | %3.1        | %2.3        | %2.6        | %2.7   | %2.0                  | %42                       |
| Halka açık devir artışı (`float_turnover_ratio_60`) | %2.1        | %2.9        | %2.2        | %2.4   | %1.5                  | %41                       |
| Uzun işlem arası (3 ay) (`trading_gap_60`) | %1.6        | %1.6        | %3.6        | %2.3   | %2.1                  | %39                       |
| Kapanış oyununun olağan dışılığı (`close_vs_vwap_5_z`) | %1.3        | %2.3        | %2.7        | %2.1   | %2.3                  | %65                       |
| Kapanış / ortalama fiyat (`close_vs_vwap`) | %1.0        | %2.1        | %2.9        | %2.0   | %1.3                  | %68                       |
| 10 günde tavan sayısı (`limit_up_10`) | %0.1        | %1.0        | %3.7        | %1.6   | %2.1                  | %51                       |
| Gün içi tepede kapanış (`close_loc`) | %0.9        | %1.6        | %2.2        | %1.6   | %0.8                  | %38                       |
| Aylık getirinin olağan dışılığı (`ret_20_z`) | %2.0        | %1.4        | %1.0        | %1.5   | %2.2                  | %49                       |
| Haftalık getirinin olağan dışılığı (`ret_5_z`) | %1.7        | %1.1        | %1.0        | %1.3   | %1.5                  | %42                       |
| Günlük hacim / 1 ay normali (`value_ratio_20`) | %1.2        | %1.1        | %1.4        | %1.2   | %1.1                  | %25                       |
| Endeks üstü getiri (1 hafta) (`excess_ret_5`) | %1.5        | %0.8        | %0.9        | %1.1   | %1.4                  | %45                       |
| 1 aylık getiri (`ret_20`) | %1.7        | %0.7        | %0.5        | %1.0   | %1.0                  | %68                       |
| 1 haftalık getiri (`ret_5`) | %1.0        | %0.8        | %0.4        | %0.7   | %1.0                  | %40                       |
| Günlük hacim / 3 ay normali (`value_ratio_60`) | %1.1        | %0.3        | %0.4        | %0.6   | %0.7                  | %64                       |
| Hacmin art arda arttığı gün (`value_up_streak`) | %0.4        | %0.6        | %0.6        | %0.5   | %0.4                  | %43                       |
| Günlük getiri (`ret_1`) | %0.5        | %0.3        | %0.4        | %0.4   | %0.4                  | %43                       |
| Piyasa düşerken sert yükseliş (`up_while_market_down_20`) | %0.0        | %0.0        | %0.0        | %0.0   | %0.0                  | %68                       |
| Art arda tavan (`limit_up_streak`) | %0.0        | %0.0        | %0.0        | %0.0   | %0.0                  | %21                       |
| Tavan (`limit_up`) | %0.0        | %0.0        | %0.0        | %0.0   | %0.0                  | %33                       |
