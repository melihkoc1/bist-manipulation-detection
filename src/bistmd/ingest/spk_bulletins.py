"""SPK haftalık bülten PDF'lerini indirir (spk.gov.tr/spk-bultenleri).

Kullanım:
    python -m bistmd.ingest.spk_bulletins --start 2016 --end 2026
"""

import argparse
import re
import time
from urllib.parse import unquote, urljoin

import requests

from bistmd.paths import RAW

SITE = "https://spk.gov.tr"
OUT_DIR = RAW / "spk_bulletins"
HEADERS = {"User-Agent": "bistmd-research/0.1 (university thesis project)"}
# Dosya adı örnekleri: 2018-1.pdf, 2010_1.pdf, "2024 15.pdf", 20-2024.pdf
_PDF_RE = re.compile(r'href="([^"]*/data/[0-9a-f]+/([^"/]+)\.pdf)"', re.IGNORECASE)
_NAME_RE = [
    re.compile(r"^(?P<y>\d{4})[-_ ](?P<n>\d{1,3})$"),
    re.compile(r"^(?P<n>\d{1,3})[-_ ](?P<y>\d{4})$"),
]


def parse_name(name: str) -> tuple[int, int] | None:
    """Dosya adından (yıl, bülten no) çıkarır; bülten değilse None."""
    name = unquote(name).strip()
    for pat in _NAME_RE:
        m = pat.match(name)
        if m:
            return int(m["y"]), int(m["n"])
    return None
_PAGE_RE = re.compile(r'href="[^"]*\?s=(\d+)"')


def year_page(year: int) -> str:
    # Son yıllar üst seviyede, öncekiler "geçmiş yıllar" altında listeleniyor.
    top = f"{SITE}/spk-bultenleri/{year}-yili-spk-bultenleri"
    archive = f"{SITE}/spk-bultenleri/gecmis-yillara-ait-bultenler/{year}-yili-spk-bultenleri"
    return top if year >= 2025 else archive


def list_bulletins(year: int, session: requests.Session) -> dict[int, str]:
    """{bülten no: pdf url} döndürür, tüm sayfaları gezer."""
    base = year_page(year)
    found: dict[int, str] = {}
    pages, seen = [1], set()
    while pages:
        page = pages.pop()
        if page in seen:
            continue
        seen.add(page)
        html = session.get(base, params={"s": page} if page > 1 else None, timeout=60).text
        for href, name in _PDF_RE.findall(html):
            parsed = parse_name(name)
            if parsed and parsed[0] == year:
                found[parsed[1]] = urljoin(SITE, href.replace(" ", "%20"))
        pages.extend(int(p) for p in _PAGE_RE.findall(html) if int(p) not in seen)
        time.sleep(0.5)
    return dict(sorted(found.items()))


def download(start: int, end: int, pause: float = 1.0) -> None:
    session = requests.Session()
    session.headers.update(HEADERS)
    for year in range(start, end + 1):
        out = OUT_DIR / str(year)
        out.mkdir(parents=True, exist_ok=True)
        bulletins = list_bulletins(year, session)
        new = 0
        for no, url in bulletins.items():
            path = out / f"{year}-{no:03d}.pdf"
            if path.exists():
                continue
            resp = session.get(url, timeout=120)
            resp.raise_for_status()
            path.write_bytes(resp.content)
            new += 1
            time.sleep(pause)
        print(f"{year}: {len(bulletins)} bülten listelendi, {new} yeni indirildi")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=2016)
    parser.add_argument("--end", type=int, default=2026)
    args = parser.parse_args()
    download(args.start, args.end)


if __name__ == "__main__":
    main()
