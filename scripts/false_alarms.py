"""Boş alarm incelemesi (MEL-16): listenin başındaki SPK vakası olmayan hisseler ne?

Kural + PU modelinin 2017–2026 haftalık ilk K listesi alınır. Aynı hissenin ≤4 hafta arayla
gelen alarm haftaları tek "alarm dönemi"ne birleştirilir. Her dönem SPK kayıtlarına göre gruplanır:
  isabet       : dönemi bilinen ana set vakasına değiyor (modelin eğitim/ölçüm etiketi)
  spk_yakini   : ana set dışı ya da dönemi bilinmeyen bir SPK vakasının 12 aylık penceresine değiyor
  spk_hissesi  : hissenin başka bir zamanda SPK vakası var, bu döneme değmiyor
  yakin_donem  : hissenin SPK kaydı yok ve dönem 2025 veya sonrası (karar henüz çıkmamış olabilir)
  kayitsiz     : hissenin hiç SPK kaydı yok
Her grup için ilk alarm haftasındaki göstergeler ve sonraki fiyat yolu özetlenir:
  haber        : son 20 günde güçlü KAP haberi var mı
  sermaye      : son 60 günde sermaye işlemi bildirimi (bedelsiz, bölünme…) var mı
  sıçrama      : son 20 günde tek günde |getiri| > %25 (fiyat sınırını aşıyor: düzeltilmemiş fiyat / veri hatası şüphesi)
  pompa-boşalt : alarmdan önceki 60 günde ≥%50 yükseliş VE sonraki 180 günde zirveden ≥%40 düşüş
Ayrıca kayıtsız dönemlerden sabit tohumla rastgele bir örnek, tek tek incelenmek üzere
ayrıntılı dosyaya yazılır.

Çıktılar:
  docs/bos_alarmlar.md                     yalnızca toplu sayılar (şirket adı yok)
  data/interim/false_alarms_episodes.csv   ayrıntılı liste (gitignored, yayımlanmaz)
  data/interim/false_alarms_sample.txt     örnek dönemlerin özetleri (gitignored)
Kullanım: python scripts/false_alarms.py [--k 10]
"""

import argparse
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from evaluate_v2 import SCORES, load_cases  # noqa: E402

from bistmd.labels.windows import case_windows  # noqa: E402
from bistmd.paths import DB_PATH, INTERIM, ROOT  # noqa: E402

GAP_WEEKS = 4
# Somut şirket olayı sayılan KAP başlıkları (alarmdan önceki 60 gün): "Özel Durum Açıklaması (Genel)" içeriği
# belirsiz olduğu için sayılmaz; rutin bildirimler (genel kurul, finansal rapor, sermaye tavanı) da sayılmaz
CONCRETE = ["İhale", "Yeni İş İlişkisi", "Birleşme", "Bölünme", "Satış", "Satım", "Alım", "Geri Alın",
            "Halka Arz", "Sermaye Artırımı - Azaltımı", "Pay  Satış Bilgi Formu", "Pay Satış Bilgi Formu",
            "Haber ve Söylenti", "Yatırım", "Sözleşme İmzalan", "Ortaklık", "İştirak", "Pay Alım Teklifi",
            "Yönetim Kontrolü", "Önemli Nitelikte"]
SAMPLE_N = 30
RANDOM_N = 5000
JUMP = 0.25
GROUPS = ["isabet", "spk_yakini", "spk_hissesi", "yakin_donem", "kayitsiz"]
GROUP_TEXT = {
    "isabet": "İsabet (ana set SPK vakası)",
    "spk_yakini": "SPK yakını (ana set dışı / dönemi bilinmeyen vaka penceresi)",
    "spk_hissesi": "Hissenin başka zamanda SPK vakası var",
    "yakin_donem": "SPK kaydı yok, 2025 ve sonrası",
    "kayitsiz": "SPK kaydı yok, 2017–2024",
}


def episodes(top: pd.DataFrame) -> pd.DataFrame:
    top = top.sort_values(["ticker", "week_end"]).copy()
    gap = top.groupby("ticker")["week_end"].diff().dt.days.fillna(1e9)
    top["ep"] = (gap > 7 * GAP_WEEKS).cumsum()
    return top.groupby("ep").agg(ticker=("ticker", "first"), first=("week_end", "min"), last=("week_end", "max"),
                                 n_weeks=("week_end", "size"), best_rank=("rank", "min")).reset_index(drop=True)


def overlaps(ep: pd.DataFrame, win: pd.DataFrame) -> pd.Series:
    m = ep.reset_index().merge(win, on="ticker")
    hit = m[(m["first"] - pd.Timedelta(days=6) <= m["end"]) & (m["last"] >= m["start"])]
    return ep.index.isin(hit["index"])


def price_path(ep: pd.DataFrame, px: pd.DataFrame) -> pd.DataFrame:
    by = {t: g.set_index("date")["close"] for t, g in px.groupby("ticker")}
    rows = []
    for e in ep.itertuples():
        s = by.get(e.ticker)
        if s is None:
            rows.append((np.nan, np.nan, np.nan))
            continue
        before = s[(s.index > e.first - pd.Timedelta(days=60)) & (s.index <= e.first)]
        after = s[(s.index > e.first) & (s.index <= e.first + pd.Timedelta(days=180))]
        run = before.iloc[-1] / before.min() - 1 if len(before) else np.nan
        if len(after):
            path = pd.concat([before.iloc[-1:], after])
            dd = (path / path.cummax() - 1).min()
            fwd = after.iloc[-1] / before.iloc[-1] - 1 if len(before) else np.nan
        else:
            dd, fwd = np.nan, np.nan
        rows.append((run, dd, fwd))
    return pd.DataFrame(rows, columns=["runup_60", "dd_180", "ret_180"], index=ep.index)


def summarize(ep: pd.DataFrame, rnd: pd.DataFrame) -> pd.DataFrame:
    def stats(d: pd.DataFrame) -> dict:
        return {
            "dönem": len(d),
            "ort. süre (hafta)": round(d["n_weeks"].mean(), 1),
            "haber %": round(d["haber"].mean() * 100),
            "sermaye işlemi %": round(d["sermaye"].mean() * 100),
            "somut şirket olayı %": round(d["somut_haber"].mean() * 100),
            "Borsa açıklama istedi %": round(d["borsa_sordu"].mean() * 100),
            "sıçrama %": round(d["sicrama"].mean() * 100),
            "60g yükseliş (medyan) %": round(d["runup_60"].median() * 100),
            "180g en derin düşüş (medyan) %": round(d["dd_180"].median() * 100),
            "pompa-boşalt şekli %": round(d["pompa"].mean() * 100),
            "piyasa değeri / yıl medyanı (medyan)": round(d["rel_mcap"].median(), 2),
        }
    rows = {GROUP_TEXT[g]: stats(ep[ep["grup"] == g]) for g in GROUPS}
    rows["Boş alarmların tümü"] = stats(ep[ep["grup"] != "isabet"])
    rows["Rastgele hisse-hafta (karşılaştırma)"] = stats(rnd)
    return pd.DataFrame(rows).T


def annotate(ep: pd.DataFrame, ctx: dict) -> pd.DataFrame:
    """Gruplama + ilk alarm haftasındaki göstergeler + sonraki fiyat yolu."""
    ep = ep.copy()
    for c in ("first", "last"):
        ep[c] = ep[c].astype("datetime64[ns]")
    is_hit = overlaps(ep, ctx["exact"])
    near = overlaps(ep, ctx["any12"])
    ep["grup"] = np.select(
        [is_hit, near, ep["ticker"].isin(ctx["spk_tickers"]), ep["first"].dt.year >= 2025],
        ["isabet", "spk_yakini", "spk_hissesi", "yakin_donem"], "kayitsiz")
    # spk_hissesi: en yakın vaka penceresine uzaklık; vaka bu alarmdan sonra mı başlıyor?
    m = ep.reset_index().merge(ctx["any12"], on="ticker")
    m["dist"] = np.maximum((m["start"] - m["last"]).dt.days, (m["first"] - m["end"]).dt.days)
    m["later"] = m["start"] > m["last"]
    near_case = m.loc[m.groupby("index")["dist"].idxmin()].set_index("index")
    ep["case_dist"] = near_case["dist"]
    ep["case_later"] = near_case["later"]

    at = pd.merge_asof(ep.reset_index().sort_values("first"), ctx["f"], left_on="first", right_on="date",
                       by="ticker", direction="backward").set_index("index")
    ep["haber"] = at["n_strong_news_20"].fillna(0).gt(0)
    ep["sermaye"] = at["n_capital_action_60"].fillna(0).gt(0)
    ep["borsa_sordu"] = at["n_unusual_move_20"].fillna(0).gt(0)
    ep["sicrama"] = at["jump_20"].fillna(0).gt(0)
    mc = pd.merge_asof(ep.reset_index().sort_values("first"), ctx["mcap"], left_on="first", right_on="date",
                       by="ticker", direction="backward").set_index("index")
    ep["mcap"] = mc["mcap_try"]
    ep["rel_mcap"] = ep["mcap"] / ep["first"].dt.year.map(ctx["yr_med"])
    ep = ep.join(price_path(ep, ctx["px"]))
    ep["pompa"] = (ep["runup_60"] >= 0.5) & (ep["dd_180"] <= -0.4)
    kap = ctx["kap"]
    m = ep.reset_index()[["index", "ticker", "first"]].merge(kap, on="ticker")
    m = m[(m["d"] <= m["first"]) & (m["d"] > m["first"] - pd.Timedelta(days=60))]
    ep["somut_haber"] = ep.index.isin(m.loc[m["concrete"], "index"])
    return ep


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=10)
    k = ap.parse_args().k

    wk = pd.read_parquet(SCORES / "honest_none_4_kural_pu.parquet")
    wk = wk[wk["week_end"].dt.year >= 2017]
    top = wk[wk["rank"] <= k]

    con = duckdb.connect(str(DB_PATH), read_only=True)
    cases = con.execute("SELECT * FROM spk_cases").df()
    px = con.execute("SELECT ticker, date, close, mcap_try FROM prices WHERE close IS NOT NULL").df()
    con.close()
    px["date"] = px["date"].astype("datetime64[ns]")
    exact, _, _ = load_cases()
    f = pd.read_parquet(INTERIM / "features.parquet", columns=[
        "ticker", "date", "ret_1", "n_strong_news_20", "n_capital_action_60", "n_unusual_move_20"])
    f["date"] = f["date"].astype("datetime64[ns]")
    # Günlük fiyat sınırı ±%10 (2020 sonrası bazı paylarda ±%20); bunu aşan tek günlük hareket düzeltilmemiş
    # sermaye işlemi ya da veri hatası işaretidir
    f["jump"] = (f["ret_1"].abs() > JUMP).astype(int)
    f = f.sort_values(["ticker", "date"])
    f["jump_20"] = f.groupby("ticker")["jump"].transform(lambda s: s.rolling(20, min_periods=1).max())
    con = duckdb.connect(str(DB_PATH), read_only=True)
    kap = con.execute("SELECT ticker, CAST(published_at AS DATE) d, subject FROM kap_disclosures "
                      "WHERE ticker IS NOT NULL").df()
    con.close()
    kap["d"] = kap["d"].astype("datetime64[ns]")
    kap["concrete"] = kap["subject"].fillna("").str.contains("|".join(CONCRETE), regex=True)
    kap = kap[kap["concrete"]]
    ctx = {
        "kap": kap,
        "exact": exact[["ticker", "start", "end"]],
        "any12": case_windows(cases, 12)[["ticker", "start", "end"]],
        "spk_tickers": set(cases["ticker"]),
        "f": f.drop(columns=["ret_1", "jump"]).sort_values("date"),
        "mcap": px[["ticker", "date", "mcap_try"]].dropna().sort_values("date"),
        "px": px[["ticker", "date", "close"]],
        "yr_med": px.dropna(subset=["mcap_try"]).groupby(px["date"].dt.year)["mcap_try"].median(),
    }
    ep = annotate(episodes(top), ctx)
    # Karşılaştırma: aynı yıllardan rastgele hisse-haftalar (sıradan bağımsız), tek haftalık dönem gibi
    rnd = wk.sample(RANDOM_N, random_state=0)
    rnd = annotate(pd.DataFrame({"ticker": rnd["ticker"].to_numpy(), "first": rnd["week_end"].to_numpy(),
                                 "last": rnd["week_end"].to_numpy(), "n_weeks": 1, "best_rank": rnd["rank"].to_numpy()}),
                   ctx)

    ep.sort_values(["grup", "first"]).to_csv(INTERIM / "false_alarms_episodes.csv", index=False)

    # Ayrıntılı örnek: kayıtsız dönemlerden rastgele, tek tek inceleme için (yayımlanmaz)
    samp = ep[ep["grup"] == "kayitsiz"].sample(min(SAMPLE_N, (ep["grup"] == "kayitsiz").sum()), random_state=0)
    con = duckdb.connect(str(DB_PATH), read_only=True)
    lines = []
    for e in samp.sort_values("first").itertuples():
        kap = con.execute(
            "SELECT CAST(published_at AS DATE) d, subject FROM kap_disclosures WHERE ticker = ? "
            "AND published_at BETWEEN ? AND ? ORDER BY published_at",
            [e.ticker, e.first - pd.Timedelta(days=60), e.last + pd.Timedelta(days=30)]).fetchall()
        lines.append(f"## {e.ticker} {e.first.date()} – {e.last.date()} | {e.n_weeks} hafta, en iyi sıra {e.best_rank:.0f} | "
                     f"60g yükseliş {e.runup_60:+.0%}, 180g en derin düşüş {e.dd_180:+.0%}, 180g getiri {e.ret_180:+.0%} | "
                     f"pd {e.mcap / 1e6:,.0f} mn TL | haber={e.haber} sermaye={e.sermaye} borsa_sordu={e.borsa_sordu} somut={e.somut_haber} sıçrama={e.sicrama}")
        subj = pd.Series([s for _, s in kap]).value_counts()
        lines.append("   KAP: " + "; ".join(f"{s} ×{n}" for s, n in subj.head(12).items()) if len(subj) else "   KAP: yok")
    con.close()
    (INTERIM / "false_alarms_sample.txt").write_text("\n".join(lines), encoding="utf-8")

    t = summarize(ep, rnd)
    false = ep[ep["grup"] != "isabet"]
    share = ep["grup"].value_counts(normalize=True).reindex(GROUPS).fillna(0)
    rshare = rnd["grup"].value_counts(normalize=True).reindex(GROUPS).fillna(0)
    sh = ep[ep["grup"] == "spk_hissesi"]
    rsh = rnd[rnd["grup"] == "spk_hissesi"]
    text = [
        "# Boş alarm incelemesi", "",
        f"`scripts/false_alarms.py --k {k}` üretir; yorum `docs/yorum_v2.md`. Şirket adları bilerek verilmez: "
        "SPK kararı olmayan bir hisse için \"manipülasyon\" ya da \"temiz\" denemez.", "",
        f"Kural + PU, dürüst yıllık eğitim, 2017–2026 haftalık ilk {k}. Aynı hissenin en fazla {GAP_WEEKS} hafta "
        "arayla gelen alarm haftaları tek döneme birleştirildi. Göstergeler dönemin ilk alarm haftasına göre. "
        f"Karşılaştırma için aynı yıllardan sıradan bağımsız {RANDOM_N} rastgele hisse-hafta aynı şekilde ölçüldü.", "",
        f"Toplam {len(ep)} alarm dönemi ({ep['n_weeks'].sum()} hisse-hafta); "
        f"{len(false)} dönem ana set SPK vakasına değmiyor.", "",
        "## Alarmlar SPK kayıtlarına göre nereye düşüyor?", "",
        "| grup | alarm dönemleri | rastgele hisse-haftalar |", "|---|---|---|",
        *[f"| {GROUP_TEXT[g]} | %{share[g] * 100:.0f} | %{rshare[g] * 100:.0f} |" for g in GROUPS], "",
        f"\"Hissenin başka zamanda SPK vakası var\" grubunda vakanın alarmdan **sonra** başladığı dönemler: "
        f"%{sh['case_later'].mean() * 100:.0f} (rastgele: %{rsh['case_later'].mean() * 100:.0f}); "
        f"en yakın vaka penceresine medyan uzaklık {sh['case_dist'].median():.0f} gün "
        f"(rastgele: {rsh['case_dist'].median():.0f} gün).", "",
        "## Gruplara göre özellikler", "",
        t.to_markdown(), "",
        "Tanımlar: **haber** = son 20 günde güçlü KAP haberi; **sermaye işlemi** = son 60 günde sermaye artırımı/"
        "bölünme bildirimi; **somut şirket olayı** = önceki 60 günde ihale, yeni iş, birleşme, varlık alım-satımı, "
        "geri alım, halka arz, bedelli sermaye artırımı, pay alım teklifi gibi başlıklı bir KAP bildirimi "
        "(içeriği belirsiz \"özel durum açıklaması\" sayılmadı); **Borsa açıklama istedi** = son 20 günde \"olağan dışı fiyat ve miktar hareketi\" "
        f"bildirimi; **sıçrama** = son 20 günde tek günde |getiri| > %{JUMP * 100:.0f} (günlük fiyat sınırını aşıyor: "
        "düzeltilmemiş sermaye işlemi ya da veri hatası şüphesi); **pompa-boşalt şekli** = önceki 60 günde ≥ %50 "
        "yükseliş ve sonraki 180 günde zirveden ≥ %40 düşüş (geriye bakarak; model bunu alarm anında bilemez); "
        "**piyasa değeri** o yılın tüm hisse medyanına bölündü (enflasyon etkisini kaldırmak için).", "",
    ]
    out = ROOT / "docs" / "bos_alarmlar.md"
    out.write_text("\n".join(text), encoding="utf-8")
    print("\n".join(text))


if __name__ == "__main__":
    main()
