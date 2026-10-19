"""KAP bildirimlerinden hisse × gün özellikleri ("habersiz hareket" dahil).

Bir bildirim yalnızca `effective_date`'inden itibaren (piyasanın onu fiyatlayabildiği
ilk işlem günü) sayılır; bkz. bistmd.db.effective_dates. Pencereler işlem günü
cinsindendir: `n_strong_news_20` = son 20 işlem gününde (bugün dahil) etkili olan güçlü
haber sayısı.

İçerik kategorileri `bistmd.features.kap_content` içinde. Önemli ayrım: fiyat artışının
SONUCU olan bildirimler (`price_reactive`: "fiyat, net aktif değerin X katını aştı";
`unusual_move`: borsanın istediği olağan dışı hareket açıklaması) HABER sayılmaz, çünkü
fiyatı yükselen her hisse için üretilirler ve "habersiz hareket" sinyalini bozarlar.
"""

import numpy as np
import pandas as pd

from bistmd.features import kap_content

# (içerik kategorisi veya grubu, pencere)
WINDOWS = [
    ("strong_news", 5), ("strong_news", 20), ("strong_news", 60),
    ("weak_news", 20), ("weak_news", 60),
    ("capital_action", 60),
    ("financial_report", 20),
    ("price_reactive", 20), ("price_reactive", 60),
    ("unusual_move", 20), ("unusual_move", 60),
    ("rumor", 60),
    ("insider_trade", 20),
    ("circuit_breaker", 20),
]
DAYS_SINCE_CAP = 250


def categorize(subject: pd.Series, summary: pd.Series | None = None) -> pd.Series:
    """Bildirim başına özellik grubu (strong_news / weak_news / diğer kategoriler / routine)."""
    summary = summary if summary is not None else pd.Series(pd.NA, index=subject.index)
    cats = kap_content.classify(subject, summary)
    return cats.map(kap_content.group_of)


def ticker_kap_features(dates: pd.Series, events: pd.DataFrame) -> pd.DataFrame:
    """Tek hissenin işlem günleri ve o hisseye ait (effective_date, category) olayları."""
    idx = pd.DatetimeIndex(dates)
    out = pd.DataFrame(index=idx)
    counts = (events.groupby(["effective_date", "category"]).size().unstack(fill_value=0)
              if len(events) else pd.DataFrame(index=idx))
    counts = counts.reindex(idx, fill_value=0)
    for cat, w in WINDOWS:
        col = counts[cat] if cat in counts.columns else pd.Series(0, index=idx)
        out[f"n_{cat}_{w}"] = col.rolling(w, min_periods=1).sum().to_numpy()

    strong = counts["strong_news"] if "strong_news" in counts.columns else pd.Series(0, index=idx)
    pos = np.arange(len(idx), dtype=float)
    last = pd.Series(np.where(strong.to_numpy() > 0, pos, np.nan), index=idx).ffill()
    out["days_since_strong_news"] = (pos - last).fillna(DAYS_SINCE_CAP).clip(upper=DAYS_SINCE_CAP).to_numpy()
    return out.reset_index(names="date")


def build(price_features: pd.DataFrame, kap: pd.DataFrame) -> pd.DataFrame:
    """Fiyat özellik tablosuna KAP özelliklerini ve "habersiz hareket" etkileşimlerini ekler.

    `kap`: ticker, effective_date, subject, summary sütunları (bkz. bistmd.db.kap_disclosures).
    """
    k = kap[["ticker", "effective_date", "subject", "summary"]].dropna(subset=["effective_date"]).copy()
    content = kap_content.classify(k["subject"], k["summary"])
    k["category"] = content.map(kap_content.group_of)
    # Bedelsiz / sermaye artırımı hem "güçlü haber" hem de ayrı bir sayaç olarak sayılır
    # (klasik "bahane haber"); çoğaltılan satır yalnızca capital_action penceresini besler.
    extra = k[content == "capital_action"].assign(category="capital_action")
    k = pd.concat([k, extra], ignore_index=True).drop(columns=["subject", "summary"])
    by_ticker = dict(tuple(k.groupby("ticker")))
    empty = k.iloc[0:0]
    parts = []
    for ticker, g in price_features.groupby("ticker", sort=False):
        kf = ticker_kap_features(g["date"].sort_values(), by_ticker.get(ticker, empty))
        kf.insert(0, "ticker", ticker)
        parts.append(kf)
    out = price_features.merge(pd.concat(parts, ignore_index=True), on=["ticker", "date"], how="left")

    # Habersiz hareket: güçlü fiyat/hacim hareketi ama gerekçe olabilecek haber yok
    news20 = out["n_strong_news_20"] + out["n_financial_report_20"]
    no_news = news20 == 0
    out["no_news_20"] = no_news.astype(int)
    out["no_news_ret_20_z"] = out["ret_20_z"].where(no_news, 0)
    out["no_news_value_ratio_5d_60"] = out["value_ratio_5d_60"].where(no_news, 0)
    out["ret_20_z_per_news"] = out["ret_20_z"] / (1 + news20)
    return out
