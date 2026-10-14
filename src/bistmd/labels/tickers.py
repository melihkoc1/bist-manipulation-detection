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


def prepare_universe(universe: pd.DataFrame) -> pd.DataFrame:
    u = universe.copy()
    u["norm"] = u["title"].map(normalize)
    return u


def resolve(ticker: str | None, header: str, universe: pd.DataFrame) -> tuple[str | None, str]:
    listed = set(universe["ticker"])
    if ticker and ticker in listed:
        return ticker, "listed"
    if ticker:
        name = company_before_ticker(header, ticker)
        match = best_match(name, universe) if name else None
        return (match, "renamed") if match else (ticker, "unlisted")
    name = company_without_ticker(header)
    match = best_match(name, universe) if name else None
    return (match, "by_name") if match else (None, "unresolved")
