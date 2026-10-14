"""Bülten ve API kaynaklarını birleştirip karar (decision) ve vaka (case) tabloları üretir.

- Karar: bir hisse hakkında bir bültende/API'de yayımlanan tek bir karar
  (suç duyurusu, idari para cezası, işlem yasağı/tedbir).
- Vaka: aynı hissede aynı manipülasyon dönemine ait kararlar kümesi. SPK genelde
  önce tedbir (işlem yasağı), aylar sonra ceza / suç duyurusu yayımlar; bunlar
  tek vaka sayılır. Dönem bilgisi yoksa karar tarihleri `case_gap_days` içinde
  birbirine yakın olan kararlar birleştirilir.
"""

import pandas as pd

from bistmd.labels.tickers import prepare_universe, resolve
from bistmd.paths import ROOT

TIER = {"suc_duyurusu": 1, "idari_para_cezasi": 1, "islem_yasagi": 2, "diger_tedbir": 2, "piyasa_tedbiri": 3}
ALIASES_PATH = ROOT / "config" / "ticker_aliases.csv"
_COLS = ["source", "ref", "ticker", "ticker_raw", "ticker_status", "decision_type", "decision_date",
         "period_start", "period_end", "articles", "total_amount_try", "multi_stock"]
# Bu kadar veya daha fazla hisseyi tek kalemde sayan kararlar genelde emir bazlı (spoofing benzeri)
# eylemlerdir; pompala-boşalt değildir. Ana etiket setinin dışında tutulur.
MULTI_STOCK_MIN = 4


def _resolve_tickers(df: pd.DataFrame, header_col: str, universe: pd.DataFrame) -> pd.DataFrame:
    """Kodları güncel koda eşler; elle tutulan eşlemeler (config/ticker_aliases.csv) önceliklidir."""
    aliases = dict(pd.read_csv(ALIASES_PATH)[["old_ticker", "new_ticker"]].values) if ALIASES_PATH.exists() else {}
    u = prepare_universe(universe)
    out = df.copy()
    out["ticker_raw"] = out["ticker"]
    resolved = []
    for t, h in zip(out["ticker"], out[header_col].fillna("")):
        t = None if pd.isna(t) else t
        if t in aliases:
            resolved.append((aliases[t], "renamed"))
        else:
            resolved.append(resolve(t, h, u))
    out["ticker"] = [r[0] for r in resolved]
    out["ticker_status"] = [r[1] for r in resolved]
    return out


def decisions_from_bulletins(items: pd.DataFrame, universe: pd.DataFrame) -> pd.DataFrame:
    df = items[items["category"].isin(["manipulation", "market_measure"])].copy()
    df = _resolve_tickers(df, "header", universe)
    df = df[df["ticker"].notna()]
    df["decision_type"] = df["section"].where(df["category"] == "manipulation", "piyasa_tedbiri")
    df["decision_date"] = df["bulletin_date"]
    df["source"] = "bulletin"
    df["ref"] = df["bulletin_year"].astype(str) + "/" + df["bulletin_no"].astype(str)
    df["multi_stock"] = df["n_tickers"] >= MULTI_STOCK_MIN
    return df[_COLS]


def decisions_from_api(events: pd.DataFrame, universe: pd.DataFrame) -> pd.DataFrame:
    df = _resolve_tickers(events, "sample_text", universe)
    df["decision_type"] = df["source"]
    df["source"] = "api"
    df["ref"] = df["decision_no"]
    df["articles"] = None
    df = df.rename(columns={"total_fine_try": "total_amount_try"})
    df["multi_stock"] = False
    return df[_COLS]


def merge_decisions(bulletin: pd.DataFrame, api: pd.DataFrame, tol_days: int = 21) -> pd.DataFrame:
    """API kararlarından bültende zaten olanları (aynı hisse+tür, ±tol gün) düşer."""
    keep = []
    for _, r in api.iterrows():
        same = bulletin[(bulletin.ticker == r.ticker)
                        & (bulletin.decision_type.isin([r.decision_type, "diger_tedbir"]
                                                       if r.decision_type == "islem_yasagi" else [r.decision_type]))]
        close = (same.decision_date - r.decision_date).abs() <= pd.Timedelta(days=tol_days)
        keep.append(not close.any())
    merged = pd.concat([bulletin, api[keep]], ignore_index=True)
    # Aynı bültende aynı hisse için birden fazla kalem olabilir (farklı kişi grupları)
    merged = (merged.groupby(["ticker", "decision_type", "decision_date"], as_index=False)
              .agg(source=("source", "first"), ref=("ref", "first"),
                   period_start=("period_start", "min"), period_end=("period_end", "max"),
                   ticker_raw=("ticker_raw", "first"), ticker_status=("ticker_status", "first"),
                   articles=("articles", lambda s: ",".join(sorted({a for x in s.dropna() for a in x.split(",") if a}))),
                   total_amount_try=("total_amount_try", "sum"), n_items=("ref", "size"),
                   multi_stock=("multi_stock", "all")))
    merged["tier"] = merged["decision_type"].map(TIER)
    return merged.sort_values(["ticker", "decision_date"]).reset_index(drop=True)


def build_cases(decisions: pd.DataFrame, case_gap_days: int = 540) -> pd.DataFrame:
    """Hisse bazında, ardışık kararlar arası boşluk `case_gap_days`'i aşınca yeni vaka başlar."""
    rows = []
    for ticker, g in decisions.sort_values("decision_date").groupby("ticker"):
        case_no, last = 0, None
        for _, r in g.iterrows():
            if last is not None and (r.decision_date - last).days > case_gap_days:
                case_no += 1
            last = r.decision_date
            rows.append({**r.to_dict(), "case_id": f"{ticker}-{case_no}"})
    d = pd.DataFrame(rows)
    cases = (d.groupby(["case_id", "ticker"], as_index=False)
             .agg(first_decision=("decision_date", "min"), last_decision=("decision_date", "max"),
                  period_start=("period_start", "min"), period_end=("period_end", "max"),
                  best_tier=("tier", "min"),
                  types=("decision_type", lambda s: ",".join(sorted(set(s)))),
                  n_decisions=("decision_date", "size"),
                  # Vakadaki tüm kararlar çok hisseli kalemlerden geliyorsa ana sete alınmaz
                  multi_stock_only=("multi_stock", "all")))
    return cases.sort_values("first_decision").reset_index(drop=True)
