"""Faz 0 envanteri: SPK kararlarından kaç vaka çıkıyor ve kaçının fiyat verisi var?

Önkoşul:
    python -m bistmd.ingest.spk_api
    python -m bistmd.ingest.spk_bulletins
Kullanım:
    python scripts/inventory.py [--skip-prices]
Çıktılar data/interim/ altına yazılır (spk_decisions, spk_cases, inventory.md).
"""

import argparse

import pandas as pd

from bistmd.ingest import prices_isyatirim, universe
from bistmd.labels import spk_bulletins, spk_events
from bistmd.labels.events import build_cases, decisions_from_api, decisions_from_bulletins, merge_decisions
from bistmd.paths import INTERIM

LOOKBACK = pd.DateOffset(months=12)


def price_coverage(cases: pd.DataFrame, download: bool) -> pd.DataFrame:
    tickers = sorted(cases["ticker"].unique())
    if download:
        prices_isyatirim.download(tickers)
    cov = []
    for _, c in cases.iterrows():
        path = prices_isyatirim.OUT_DIR / f"{c.ticker}.parquet"
        if not path.exists():
            cov.append(None)
            continue
        d = pd.read_parquet(path, columns=["date"])["date"]
        win_start = (c.period_start if pd.notna(c.period_start) else c.first_decision - LOOKBACK)
        n = d[(d >= win_start) & (d <= c.first_decision)].size
        cov.append(n)
    out = cases.copy()
    out["price_days_in_window"] = cov
    out["has_price"] = out["price_days_in_window"].fillna(0) >= 20
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-prices", action="store_true")
    args = parser.parse_args()
    INTERIM.mkdir(parents=True, exist_ok=True)

    items = spk_bulletins.parse_all()
    items.to_parquet(INTERIM / "bulletin_items.parquet", index=False)
    api = spk_events.build_events(spk_events.load_records())

    uni = universe.load()
    decisions = merge_decisions(decisions_from_bulletins(items, uni), decisions_from_api(api, uni))
    cases = build_cases(decisions)
    cases = price_coverage(cases, download=not args.skip_prices)
    decisions.to_parquet(INTERIM / "spk_decisions.parquet", index=False)
    cases.to_parquet(INTERIM / "spk_cases.parquet", index=False)

    decisions["year"] = decisions["decision_date"].dt.year
    cases["year"] = cases["first_decision"].dt.year
    ok = cases[cases["has_price"]]
    core = ok[~ok["multi_stock_only"]]
    by_year_type = decisions.pivot_table(index="year", columns="decision_type", values="ticker",
                                         aggfunc="count", fill_value=0)
    by_year_case = cases.groupby("year").agg(vaka=("case_id", "size"), fiyatli=("has_price", "sum"),
                                             tier1=("best_tier", lambda s: (s == 1).sum()))
    by_year_case["ana_set"] = core.groupby("year").size()
    by_year_case = by_year_case.fillna(0).astype(int)
    no_price = cases.loc[~cases["has_price"], ["case_id", "first_decision", "types", "price_days_in_window"]]

    lines = [
        "# Faz 0 — SPK Etiket Envanteri",
        "",
        f"- Bülten sayısı (ayrıştırılan): {items['file'].nunique() if len(items) else 0}",
        f"- Piyasa bozucu / dolandırıcılık kalemi (bülten): {int(items['market_abuse'].sum()) if len(items) else 0}",
        f"- Karar sayısı (bülten + API, tekilleştirilmiş): {len(decisions)}",
        f"- Kod durumu: {decisions['ticker_status'].value_counts().to_dict()}",
        f"- **Vaka sayısı: {len(cases)}** (farklı hisse: {cases['ticker'].nunique()})",
        f"- Tier 1 (suç duyurusu veya para cezası içeren) vaka: {(cases['best_tier'] == 1).sum()}",
        f"- Manipülasyon dönemi bilinen vaka: {cases['period_start'].notna().sum()}",
        f"- **Fiyat verisi olan vaka (pencerede ≥20 gün): {len(ok)}**",
        f"- Sadece çok hisseli (≥4) kalemlerden gelen vaka (ana set dışı): {cases['multi_stock_only'].sum()}",
        f"- **ANA SET — tek/az hisseli, fiyatlı vaka: {len(core)}** "
        f"(Tier 1: {(core['best_tier'] == 1).sum()}, dönemi bilinen: {core['period_start'].notna().sum()})",
        "",
        "## Yıllara göre karar sayısı (karar türü)",
        "",
        by_year_type.to_markdown(),
        "",
        "## Yıllara göre vaka sayısı (ilk karar yılı)",
        "",
        by_year_case.to_markdown(),
        "",
        "## Fiyat verisi bulunamayan vakalar",
        "",
        "Muhtemel nedenler: hisse kodu değişmiş (İş Yatırım güncel kodu kullanıyor), "
        "hatalı kod çıkarımı ya da 2010 öncesi dönem.",
        "",
        no_price.to_markdown(index=False),
    ]
    (INTERIM / "inventory.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:14]))
    print(by_year_case.to_string())


if __name__ == "__main__":
    main()
