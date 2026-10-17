"""KAP bildirimlerinden hisse × gün özellikleri ("habersiz hareket" dahil).

Bir bildirim yalnızca `effective_date`'inden itibaren (piyasanın onu fiyatlayabildiği
ilk işlem günü) sayılır; bkz. bistmd.db.effective_dates. Pencereler işlem günü
cinsindendir: `n_material_20` = son 20 işlem gününde (bugün dahil) etkili olan önemli
bildirim sayısı.
"""

import numpy as np
import pandas as pd

# Konu → kategori. Listede olmayan konular "rutin" sayılır (bilgi formları, raporlar vb.)
CATEGORIES = {
    "material": {
        "Özel Durum Açıklaması (Genel)", "Yeni İş İlişkisi", "Finansal Duran Varlık Edinimi",
        "Finansal Duran Varlık Satışı", "Maddi Duran Varlık Alımı", "Maddi Duran Varlık Satımı",
        "İhale Süreci / Sonucu", "Birleşme İşlemlerine İlişkin Bildirim", "Bölünme İşlemlerine İlişkin Bildirim",
        "Pay Alım Teklifi Yoluyla Pay Toplanmasına İlişkin Bildirim", "Geleceğe Dönük Değerlendirmeler",
        "Ortaklık Aleyhine Dava Açılması veya Davaya İlişkin Gelişmeler", "Kredi Derecelendirmesi",
        "Kar Payı Dağıtım İşlemlerine İlişkin Bildirim", "Değerleme Raporu", "İlişkili Taraf İşlemleri",
        "Yatırım Kararı", "Satış Sözleşmesi", "Ürün Lansmanı", "Patent / Lisans / Marka",
    },
    "financial_report": {"Finansal Rapor"},
    "unusual_move": {"Olağan Dışı Fiyat ve Miktar Hareketleri"},
    "rumor": {"Haber ve Söylentilere İlişkin Açıklama"},
    "insider_trade": {"Pay Alım Satım Bildirimi"},
    "circuit_breaker": {"Pay Bazında Devre Kesici Bildirimi"},
    "capital": {"Sermaye Artırımı - Azaltımı İşlemlerine İlişkin Bildirim",
                "Kayıtlı Sermaye Tavanı İşlemlerine İlişkin Bildirim"},
}
_SUBJECT_TO_CAT = {s: c for c, subjects in CATEGORIES.items() for s in subjects}

# (kategori, pencere) çiftleri
WINDOWS = [
    ("material", 5), ("material", 20), ("material", 60),
    ("financial_report", 20),
    ("unusual_move", 20), ("unusual_move", 60),
    ("rumor", 60),
    ("insider_trade", 20),
    ("circuit_breaker", 20),
    ("capital", 60),
]
DAYS_SINCE_CAP = 250


def categorize(subject: pd.Series) -> pd.Series:
    return subject.map(_SUBJECT_TO_CAT).fillna("routine")


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

    material = counts["material"] if "material" in counts.columns else pd.Series(0, index=idx)
    pos = np.arange(len(idx), dtype=float)
    last = pd.Series(np.where(material.to_numpy() > 0, pos, np.nan), index=idx).ffill()
    out["days_since_material"] = (pos - last).fillna(DAYS_SINCE_CAP).clip(upper=DAYS_SINCE_CAP).to_numpy()
    return out.reset_index(names="date")


def build(price_features: pd.DataFrame, kap: pd.DataFrame) -> pd.DataFrame:
    """Fiyat özellik tablosuna KAP özelliklerini ve "habersiz hareket" etkileşimlerini ekler.

    `kap`: ticker, effective_date, subject sütunları (bkz. bistmd.db.kap_disclosures).
    """
    k = kap[["ticker", "effective_date", "subject"]].dropna(subset=["effective_date"]).copy()
    k["category"] = categorize(k["subject"])
    by_ticker = dict(tuple(k.groupby("ticker")))
    empty = k.iloc[0:0]
    parts = []
    for ticker, g in price_features.groupby("ticker", sort=False):
        kf = ticker_kap_features(g["date"].sort_values(), by_ticker.get(ticker, empty))
        kf.insert(0, "ticker", ticker)
        parts.append(kf)
    out = price_features.merge(pd.concat(parts, ignore_index=True), on=["ticker", "date"], how="left")

    # Habersiz hareket: güçlü fiyat/hacim hareketi ama gerekçe olabilecek bildirim yok
    no_news = (out["n_material_20"] + out["n_financial_report_20"]) == 0
    out["no_news_20"] = no_news.astype(int)
    out["no_news_ret_20_z"] = out["ret_20_z"].where(no_news, 0)
    out["no_news_value_ratio_5d_60"] = out["value_ratio_5d_60"].where(no_news, 0)
    out["ret_20_z_per_news"] = out["ret_20_z"] / (1 + out["n_material_20"] + out["n_financial_report_20"])
    return out
