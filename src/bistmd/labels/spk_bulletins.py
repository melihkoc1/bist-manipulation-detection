"""SPK bülten PDF'lerinden piyasa bozucu eylem / piyasa dolandırıcılığı kararlarını çıkarır.

Bültenlerde "SUÇ DUYURUSU, İDARİ PARA CEZASI İLE DİĞER YAPTIRIM VE TEDBİRLER"
başlıklı bölüm; altında "İdari Para Cezaları", "Suç Duyuruları", "İşlem Yasakları",
"Diğer Yaptırım, Tedbir ve İşlem Yasakları" alt bölümleri ve "a) ..., b) ..."
şeklinde kalemler bulunur. Her kalemden hisse kodu, karar türü, kanun maddesi
ve (varsa) işlem dönemi çıkarılır.

Gizlilik: Kişi tabloları (ad, TCKN, MKK sicil) saklanmaz; kalem metni ilk tablo
başlığında kesilir ve yalnızca yerel ara dosyalarda tutulur.
"""

import re
from pathlib import Path

import pandas as pd
import pymupdf

from bistmd.labels.spk_events import extract_tickers
from bistmd.paths import RAW

BULLETIN_DIR = RAW / "spk_bulletins"

_HEADER = re.compile(r"BÜLTENİ\s+(\d{4})\s*/\s*(\d+)\s+(\d{1,2}/\d{1,2}/\d{4})")
_SANCTIONS_START = re.compile(r"\n\s*[A-Z]\.\s+SUÇ DUYURUSU,\s+İDARİ PARA CEZASI")
_NEXT_TOP_SECTION = re.compile(r"\n\s*[A-Z]\.\s+[A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ /,()]{6,}\s*\n")
_SUBSECTION = re.compile(r"\n\s*\d\.\s+(İdari Para Cezaları|Suç Duyuruları|İşlem Yasakları|Diğer Yaptırım[^\n]*|Lisans[^\n]*)")
_ITEM = re.compile(r"\n\s*([a-zçğıöşü]{1,2})\)\s")
_FOOTER = re.compile(r"_{20,}.*?Faks:\s*\(212\)[^\n]*\n\s*\d*\s*", re.DOTALL)
# Kişi tablosunun başladığını gösteren ifadeler: buradan sonrası saklanmaz
_TABLE_START = re.compile(r"Ad-Soyad|Ad Soyad|Unvan\s*/|IPC Uygulanan|İPC Uygulanan|Şahıs\s*/|TC Kimlik", re.IGNORECASE)

_DATE = r"(\d{1,2}[./]\d{1,2}[./]\d{4})"
_PERIOD = re.compile(_DATE + r"\s*(?:[-–—]|ile|ila)\s*" + _DATE)
_ARTICLE = re.compile(r"\b(10[4-7])\s*/\s*(\d)\b|\b(10[4-7])\s*(?:inci|üncü|ncı|nci)?\s*madde")
_AMOUNT = re.compile(r"\b\d{1,3}(?:\.\d{3})+,\d{2}\b")

SUBSECTION_TYPES = {
    "İdari Para Cezaları": "idari_para_cezasi",
    "Suç Duyuruları": "suc_duyurusu",
    "İşlem Yasakları": "islem_yasagi",
}


def _subsection_type(title: str) -> str | None:
    if title in SUBSECTION_TYPES:
        return SUBSECTION_TYPES[title]
    if title.startswith("Diğer Yaptırım"):
        return "diger_tedbir"
    return None  # Lisans iptalleri vb.


def _to_date(s: str) -> pd.Timestamp:
    return pd.to_datetime(s.replace("/", "."), format="%d.%m.%Y", errors="coerce")


_SINGLE_DAY = re.compile(_DATE + r"\s+tarihinde\s+(?:gerçekleştirilen|meydana gelen)")


def extract_periods(text: str) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Metindeki tüm tarih aralıklarının en erken başlangıç / en geç bitişini döndürür.
    Aralık yoksa tek günlük olayları ("22.02.2017 tarihinde gerçekleştirilen işlemler") alır."""
    starts, ends = [], []
    for a, b in _PERIOD.findall(text):
        s, e = _to_date(a), _to_date(b)
        if pd.notna(s) and pd.notna(e) and s <= e:
            starts.append(s)
            ends.append(e)
    if not starts:
        days = [d for d in map(_to_date, _SINGLE_DAY.findall(text)) if pd.notna(d)]
        if not days:
            return None, None
        return min(days), max(days)
    return min(starts), max(ends)


def extract_articles(text: str) -> list[str]:
    found = []
    for a, para, b in _ARTICLE.findall(text):
        art = f"{a}/{para}" if a else b
        if art not in found:
            found.append(art)
    if "VI-104.1" in text or "Piyasa Bozucu" in text or "piyasa bozucu" in text:
        if not any(x.startswith("104") for x in found):
            found.append("104")
    return found


def read_text(path: Path) -> str:
    with pymupdf.open(path) as doc:
        text = "\n".join(page.get_text() for page in doc)
    return _FOOTER.sub("\n", text)


def parse_bulletin_text(text: str) -> tuple[dict, list[dict]]:
    """(bülten meta, kalem listesi) döndürür."""
    meta: dict = {"bulletin_year": None, "bulletin_no": None, "bulletin_date": None}
    m = _HEADER.search(text)
    if m:
        meta = {
            "bulletin_year": int(m.group(1)),
            "bulletin_no": int(m.group(2)),
            "bulletin_date": _to_date(m.group(3)),
        }

    start = _SANCTIONS_START.search(text)
    if not start:
        return meta, []
    rest = text[start.end():]
    end = _NEXT_TOP_SECTION.search(rest)
    section = rest[: end.start()] if end else rest

    subs = list(_SUBSECTION.finditer(section))
    items: list[dict] = []
    for i, sub in enumerate(subs):
        kind = _subsection_type(sub.group(1).strip())
        if kind is None:
            continue
        body = section[sub.end(): subs[i + 1].start() if i + 1 < len(subs) else len(section)]
        marks = list(_ITEM.finditer(body))
        # Bazı alt bölümlerde tek kalem vardır ve harflendirilmez.
        spans = [(mk.group(1), mk.end(), marks[j + 1].start() if j + 1 < len(marks) else len(body))
                 for j, mk in enumerate(marks)] or [("", 0, len(body))]
        for label, s, e in spans:
            full = body[s:e]
            cut = _TABLE_START.search(full)
            header = re.sub(r"\s+", " ", full[: cut.start()] if cut else full[:1500]).strip()
            # Hisse kodu bazen sadece tabloda geçer ("KTLEV Pay Piyasasında ...")
            tickers = extract_tickers(header) or extract_tickers(full)
            flat = re.sub(r"\s+", " ", full)
            if len(tickers) == 1:
                periods = {tickers[0]: extract_periods(flat)}
            else:
                periods = {t: period_for_ticker(flat, t) for t in tickers}
            amounts = [float(a.replace(".", "").replace(",", ".")) for a in _AMOUNT.findall(full)]
            item = {
                "section": kind,
                "item": label,
                "tickers": tickers,
                "periods": periods,
                "articles": extract_articles(full),
                "mentions_trading_ban": bool(re.search(r"işlem yasağı|işlem yapma yasağı", full, re.IGNORECASE)),
                "total_amount_try": sum(amounts) if kind == "idari_para_cezasi" and amounts else None,
                "header": header[:600],
            }
            item["category"] = classify(item)
            items.append(item)
    return meta, items


def period_for_ticker(text: str, ticker: str) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Çok hisseli kalemlerde hisse kodunu izleyen ilk tarih aralığını bulur:
    "... (COMDO) pay piyasasında 06.07.2015-10.08.2015 döneminde, ... (DGKLB) ..." """
    m = re.search(rf"\b{re.escape(ticker)}\b\)?[^()]{{0,80}}?{_DATE}\s*(?:[-–—]|ile|ila)\s*{_DATE}", text)
    if not m:
        return None, None
    s, e = _to_date(m.group(1)), _to_date(m.group(2))
    return (s, e) if pd.notna(s) and pd.notna(e) and s <= e else (None, None)


_INSIDER = re.compile(r"özel durum açıklaması(?:nın)? öncesinde|bilgi suistimali niteliğinde|içsel bilgi", re.IGNORECASE)
_PRICE_MOVE = re.compile(r"fiyat ve miktar hareketleri", re.IGNORECASE)
_WARRANT = re.compile(r"varant|dayanak varlıklı", re.IGNORECASE)


def classify(item: dict) -> str | None:
    """'manipulation' | 'insider' | 'warrant' | 'market_measure' | None

    - manipulation: SPKn 104 (piyasa bozucu eylem) / 107 (piyasa dolandırıcılığı) ya da
      pay piyasası işlemleri nedeniyle getirilen işlem yasağı
    - insider: SPKn 106 / özel durum açıklaması öncesi işlemler (kapsam dışı, ayrı tutulur).
      Md. 104 ile cezalandırılsa da açıklama öncesi işlemler pompala-boşalt değildir.
    - warrant: hissenin kendisi değil ona dayalı varant piyasasındaki işlemler (kapsam dışı)
    - market_measure: SPK'nın "gözlenen fiyat ve miktar hareketleri" nedeniyle hisse
      bazında aldığı tedbirler (brüt takas, internetten emir yasağı vb.) — zayıf etiket
    """
    arts = item["articles"]
    header = item["header"]
    low = header.lower()
    if _WARRANT.search(header):
        return "warrant"
    if any(a.startswith("106") for a in arts) or _INSIDER.search(header):
        if not any(a.startswith("107/1") for a in arts):
            return "insider"
    if any(a.startswith(("104", "107")) for a in arts):
        return "manipulation"
    if item["section"] in ("islem_yasagi", "diger_tedbir"):
        if item["mentions_trading_ban"] and ("pay piyasas" in low or "tedbirler tebliği" in low):
            return "manipulation"
        if _PRICE_MOVE.search(header):
            return "market_measure"
    return None


def parse_all(bulletin_dir: Path = BULLETIN_DIR) -> pd.DataFrame:
    """Tüm bültenlerdeki kalemleri hisse başına bir satır olacak şekilde döndürür."""
    rows: list[dict] = []
    for path in sorted(bulletin_dir.glob("*/*.pdf")):
        try:
            meta, items = parse_bulletin_text(read_text(path))
        except Exception as exc:  # bozuk PDF tüm akışı durdurmasın
            print(f"UYARI: {path.name} okunamadı: {exc}")
            continue
        for it in items:
            base = {k: v for k, v in it.items() if k not in ("tickers", "periods")}
            for t in it["tickers"] or [None]:
                start, end = it["periods"].get(t, (None, None)) if t else (None, None)
                rows.append({**meta, "file": path.name, **base, "ticker": t,
                             "n_tickers": len(it["tickers"]),
                             "period_start": start, "period_end": end,
                             "market_abuse": it["category"] == "manipulation"})
    df = pd.DataFrame(rows)
    if not df.empty:
        df["articles"] = df["articles"].map(lambda a: ",".join(a))
    return df
