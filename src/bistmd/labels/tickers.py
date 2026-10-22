"""SPK kararlarındaki hisse kodlarını güncel koda eşler ve kodsuz kalemlere ad üzerinden kod bulur.

Durumlar:
- listed:   kod KAP'ın güncel listesinde var
- renamed:  kod listede yok ama şirket adı listedeki başka bir koda eşleşiyor (ör. KOZAL → TRALT)
- by_name:  kararda kod yoktu, şirket adından bulundu
- unlisted: listede yok, ad eşleşmesi de yok (işlemden kalkmış ya da hatalı kod çıkarımı)
"""

import re
from difflib import SequenceMatcher

import pandas as pd

_STOP = {
    "A", "Ş", "AŞ", "ANONİM", "ŞİRKETİ", "ŞİRKET", "VE", "SANAYİ", "SAN", "TİCARET", "TİC",
    "HOLDİNG", "YATIRIM", "ORTAKLIĞI", "ORTAKLIK", "İMALAT", "PAZARLAMA", "DIŞ", "İTHALAT", "İHRACAT",
}


def _upper_tr(s: str) -> str:
    return s.replace("i", "İ").replace("ı", "I").upper()


def normalize(name: str) -> str:
    tokens = re.findall(r"[A-ZÇĞİÖŞÜ0-9]+", _upper_tr(name))
    return " ".join(t for t in tokens if t not in _STOP)


def company_before_ticker(header: str, ticker: str) -> str | None:
    """'... Formet Çelik Kapı Sanayi ve Ticaret A.Ş. (FORMT) pay ...' → şirket adı"""
    m = re.search(rf"([A-ZÇĞİÖŞÜ][^()]{{3,150}}?)\s*\({re.escape(ticker)}\)", header)
    if not m:
        return None
    # Önceki cümle/kalem parçalarını at: son ', ' veya ' ve ' sonrası
    name = re.split(r",\s|;\s", m.group(1))[-1]
    return name.strip()


def company_without_ticker(header: str) -> str | None:
    """'Mepet Metro Petrol ve Tesisleri Sanayi Ticaret A.Ş. paylarında ...' → şirket adı"""
    m = re.search(r"([A-ZÇĞİÖŞÜ][^()]{3,150}?(?:A\.Ş\.|AŞ))(?:['’]?n[iı]n)?\s+pay", header)
    return m.group(1).strip() if m else None


def best_match(name: str, universe: pd.DataFrame, threshold: float = 0.85) -> str | None:
    target = normalize(name)
    if not target:
        return None
    scores = universe["norm"].map(lambda u: SequenceMatcher(None, target, u).ratio())
    i = scores.idxmax()
    return universe.at[i, "ticker"] if scores[i] >= threshold else None


# İlk kelimesi tek başına ayırt edici olmayan unvanlarda ilk iki kelime karşılaştırılır
_GENERIC_FIRST = {"TÜRK", "TÜRKİYE", "İSTANBUL", "ANADOLU", "EGE", "AKDENİZ", "DOĞU", "BATI", "ULUSLARARASI"}


def match_company(name: str, universe: pd.DataFrame) -> str | None:
    """Eski bültenlerdeki unvanlar için daha sıkı eşleme: ayırt edici ilk kelime(ler) aynı olmalı
    (ör. "Metro Menkul Kıymetler" ≠ "Ata Menkul Kıymetler", benzerlik 0,86 olsa da).
    İlk kelime yazımı farklıysa ("Altınyunus" / "Altın Yunus") yalnızca çok yüksek benzerlik kabul edilir."""
    target = normalize(name)
    toks = target.split()
    if not toks:
        return None
    key = tuple(toks[:2]) if toks[0] in _GENERIC_FIRST and len(toks) > 1 else tuple(toks[:1])
    cand = universe[universe["norm"].str.split().map(lambda t: tuple(t[:len(key)]) == key)]
    if not cand.empty:
        scores = cand["norm"].map(lambda u: SequenceMatcher(None, target, u).ratio())
        if scores.max() >= 0.6:
            return cand.at[scores.idxmax(), "ticker"]
    return best_match(name, universe, threshold=0.9)


def prepare_universe(universe: pd.DataFrame) -> pd.DataFrame:
    u = universe.copy()
    u["norm"] = u["title"].map(normalize)
    return u


def resolve(ticker: str | None, header: str, universe: pd.DataFrame,
            company: str | None = None) -> tuple[str | None, str]:
    """company: eski biçim bültenlerde kalemden çıkarılmış şirket unvanı (kod yazılmaz)."""
    if company:
        match = match_company(company, universe)
        return (match, "by_name") if match else (None, "unresolved")
    listed = set(universe["ticker"])
    if ticker and ticker in listed:
        return ticker, "listed"
    if ticker:
        name = company_before_ticker(header, ticker)
        match = best_match(name, universe) if name else None
        return (match, "renamed") if match else (ticker, "unlisted")
    name = company_without_ticker(header)
    match = best_match(name, universe) if name else None
    if match:
        return match, "by_name"
    # Yedek: "X A.Ş. hisse senedinde" gibi kalıplar (2012–2015 bültenleri); yalnızca aksi halde
    # düşecek kalemlere uygulanır, sıkı eşleme kullanılır
    from bistmd.labels.spk_bulletins import company_names
    for name in company_names(header):
        match = match_company(name, universe)
        if match:
            return match, "by_name"
    return None, "unresolved"
