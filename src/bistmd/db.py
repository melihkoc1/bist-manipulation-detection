"""Ham ve ara verileri tek bir DuckDB veritabanında (data/db/bist.duckdb) toplar.

Tablolar:
    prices            hisse × gün (İş Yatırım)
    trading_days      işlem günleri takvimi (XU100 verisi olan günler)
    kap_disclosures   KAP bildirimleri, hisse başına bir satır + effective_date
    universe          KAP güncel şirket listesi
    spk_decisions     SPK kararları (bülten + API)
    spk_cases         SPK vakaları

Sızıntı kuralı: Bir bildirimin `effective_date`'i, piyasanın o bilgiyi fiyatlayabildiği
ilk işlem günüdür. Seans kapanışından (18:00) önce yayımlanan bildirim aynı gün, sonra
yayımlanan (veya tatil/hafta sonu) bildirim bir sonraki işlem günü etkili sayılır.

Kullanım:
    python -m bistmd.db
"""

import duckdb
import pandas as pd

from bistmd.paths import DB_PATH, INTERIM, RAW

SESSION_CLOSE = pd.Timedelta(hours=18)


def effective_dates(published_at: pd.Series, trading_days: pd.DatetimeIndex) -> pd.Series:
    """Her yayın zamanı için bilginin fiyatlanabildiği ilk işlem gününü döndürür."""
    day = published_at.dt.normalize()
    after_close = (published_at - day) >= SESSION_CLOSE
    candidate = day + pd.to_timedelta(after_close.astype(int), unit="D")
    idx = trading_days.searchsorted(candidate.values, side="left")
    out = pd.Series(pd.NaT, index=published_at.index, dtype="datetime64[ns]")
    valid = idx < len(trading_days)
    out[valid] = trading_days[idx[valid]]
    return out


def _explode_tickers(kap: pd.DataFrame) -> pd.DataFrame:
    """'GARAN, TGB' → iki satır. Hisse kodu olmayan bildirimler atılır."""
    k = kap[kap["tickers"].notna() & (kap["tickers"].str.strip() != "")].copy()
    k["ticker"] = k["tickers"].str.split(",")
    k = k.explode("ticker")
    k["ticker"] = k["ticker"].str.strip()
    return k[k["ticker"] != ""].drop(columns="tickers")


def build() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    price_glob = (RAW / "prices_isyatirim" / "*.parquet").as_posix()
    con.execute(f"""
        CREATE OR REPLACE TABLE prices AS
        SELECT * FROM read_parquet('{price_glob}', union_by_name = true)
        WHERE close IS NOT NULL
    """)
    con.execute("""
        CREATE OR REPLACE TABLE trading_days AS
        SELECT DISTINCT date FROM prices WHERE xu100 IS NOT NULL ORDER BY date
    """)
    days = pd.DatetimeIndex(con.execute("SELECT date FROM trading_days").df()["date"])

    kap_files = sorted((RAW / "kap_disclosures").glob("*.parquet"))
    if kap_files:
        kap = pd.concat((pd.read_parquet(p) for p in kap_files), ignore_index=True)
        kap = _explode_tickers(kap.drop_duplicates("disclosure_id"))
        kap["effective_date"] = effective_dates(kap["published_at"], days)
        con.register("kap_df", kap)
        con.execute("CREATE OR REPLACE TABLE kap_disclosures AS SELECT * FROM kap_df")
        con.unregister("kap_df")

    universe = RAW / "universe" / "kap_bist.parquet"
    if universe.exists():
        con.execute(f"CREATE OR REPLACE TABLE universe AS SELECT * FROM read_parquet('{universe.as_posix()}')")
    for name in ("spk_decisions", "spk_cases"):
        path = INTERIM / f"{name}.parquet"
        if path.exists():
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_parquet('{path.as_posix()}')")

    for (name,) in con.execute("SHOW TABLES").fetchall():
        n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"{name:16} {n:>12,} satır")
    con.close()


if __name__ == "__main__":
    build()
