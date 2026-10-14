"""SPK API ham kayıtlarını hisse bazlı olay (event) tablosuna dönüştürür.

Bir olay = (kaynak, hisse kodu, karar tarihi). Aynı kararda birden fazla kişi
olabilir; bunlar tek olayda toplanır (kişi sayısı, toplam ceza).

Gizlilik: Kişi adı, kimlik ve MKK sicil numarası olay tablosuna taşınmaz.
"""

import json
import re

import pandas as pd

from bistmd.paths import RAW

SRC_DIR = RAW / "spk_api"

# "CANTE pay piyasasında", "(BASGZ)", "KRSTL.E" gibi kalıplar
# BIST kodları yalnızca ASCII harf/rakamdan oluşur; "BİAŞ", "İPC" gibi kısaltmalar elenir.
_TICKER_PATTERNS = [
    re.compile(r"\(([A-Z][A-Z0-9]{2,5})(?:\.E)?\)"),
    re.compile(r"(?<![A-Za-z0-9ÇĞİÖŞÜçğıöşü])([A-Z][A-Z0-9]{2,5})(?:\.E)?\s+(?i:pay)(?:ı|ları|larında|ında|ına|larına|lar)?\b"),
]
_NOT_TICKERS = {
    "SPK", "SPKN", "BİST", "BIST", "VİOP", "VIOP", "MKK", "KAP", "TTK", "TCK",
    "AŞ", "TL", "USD", "EUR", "SMMM", "YMM", "BSMV", "ANONİM", "ŞİRKETİ", "GYO", "PSBF",
}

_DATE = r"(\d{1,2}[./]\d{1,2}[./]\d{4})"
_PERIOD = re.compile(_DATE + r"\s*(?:[-–—]|ile|ila)\s*" + _DATE)

MARKET_ABUSE_KEYWORDS = ("bozucu", "piyasa dolandırıcılığı")
_ART_104 = re.compile(r"\b104\b|VI-104")


def extract_tickers(text: str | None) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    for pat in _TICKER_PATTERNS:
        for m in pat.findall(text):
            if m not in _NOT_TICKERS and m not in found:
                found.append(m)
    return found


def extract_period(text: str | None) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Metindeki ilk 'gg.aa.yyyy - gg.aa.yyyy' aralığını döndürür."""
    if not text:
        return None, None
    m = _PERIOD.search(text)
    if not m:
        return None, None
    start, end = (pd.to_datetime(d.replace("/", "."), format="%d.%m.%Y", errors="coerce") for d in m.groups())
    if pd.isna(start) or pd.isna(end) or start > end:
        return None, None
    return start, end


def _load(name: str) -> list[tuple[int, dict]]:
    """(dosya yılı, kayıt) çiftleri. API'deki `id` sadece yıl içinde benzersiz."""
    rows: list[tuple[int, dict]] = []
    for path in sorted(SRC_DIR.glob(f"{name}_*.json")):
        year = int(path.stem.rsplit("_", 1)[1])
        rows.extend((year, r) for r in json.loads(path.read_text(encoding="utf-8")))
    return rows


def _is_market_abuse(violation: str | None, text: str | None) -> bool:
    # SPKn md. 104 (piyasa bozucu eylemler) yalnızca ihlal alanında aranır;
    # açıklama metnindeki rastgele "104" sayıları yanlış pozitif üretmesin.
    if violation and _ART_104.search(violation):
        return True
    joined = f"{violation or ''} {text or ''}".lower()
    return any(k in joined for k in MARKET_ABUSE_KEYWORDS)


def load_records() -> pd.DataFrame:
    """Her kişi-karar satırı için bir kayıt (kişisel bilgiler hariç)."""
    out: list[dict] = []

    for year, r in _load("islem_yasagi"):
        text = r.get("aciklama")
        tickers = [r["payKodu"]] if r.get("payKodu") else extract_tickers(text)
        start, end = extract_period(text)
        for t in tickers or [None]:
            out.append({
                "source": "islem_yasagi",
                "record_id": f"iy:{year}:{r['id']}",
                "decision_date": pd.to_datetime(r["kurulKararTarihiStr"], format="%d.%m.%Y"),
                "decision_no": r.get("kurulKararNo"),
                "ticker": t,
                "market_abuse": True,  # işlem yasağı tanım gereği piyasa dolandırıcılığı şüphesine dayanır
                "violation": None,
                "fine_try": None,
                "period_start": start,
                "period_end": end,
                "lawsuit": r.get("davaBilgisi"),
                "lawsuit_stage": r.get("yargilamaAsamasi"),
                "text": text,
            })

    for year, r in _load("idari_para_cezasi"):
        text = r.get("aciklama")
        tickers = extract_tickers(text)
        start, end = extract_period(text)
        for t in tickers or [None]:
            out.append({
                "source": "idari_para_cezasi",
                "record_id": f"ipc:{year}:{r['id']}",
                "decision_date": pd.to_datetime(r["kurulKararTarihiStr"], format="%d.%m.%Y"),
                "decision_no": r.get("kurulKararNo"),
                "ticker": t,
                "market_abuse": _is_market_abuse(r.get("ihlal"), text),
                "violation": (r.get("ihlal") or "").strip() or None,
                "fine_try": r.get("tutar"),
                "period_start": start,
                "period_end": end,
                "lawsuit": r.get("davaBilgisi"),
                "lawsuit_stage": r.get("yargilamaAsamasi"),
                "text": text,
            })

    return pd.DataFrame(out)


def build_events(records: pd.DataFrame) -> pd.DataFrame:
    """Piyasa bozucu eylem kayıtlarını (kaynak, hisse, karar tarihi) bazında olaylara toplar."""
    df = records[records["market_abuse"] & records["ticker"].notna()]
    events = (
        df.groupby(["source", "ticker", "decision_date"], as_index=False)
        .agg(
            decision_no=("decision_no", "first"),
            n_records=("record_id", "nunique"),
            total_fine_try=("fine_try", "sum"),
            period_start=("period_start", "min"),
            period_end=("period_end", "max"),
            lawsuit_any=("lawsuit", lambda s: (s == "Var").any()),
            sample_text=("text", "first"),
        )
    )
    events["label_tier"] = events["source"].map({"idari_para_cezasi": 1, "islem_yasagi": 2})
    return events.sort_values(["decision_date", "ticker"]).reset_index(drop=True)
