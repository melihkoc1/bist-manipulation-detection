"""KAP haberlerinin alarmlara göre zamanlaması (MEL-94; haber bağlamı 1. adım).

Model değişmez. Kural + PU haftalık ilk 20 alarmlarında şirkete ait güçlü KAP haberinin yükselişin
başlangıcına (t0) göre ne zaman geldiğine bakılır:
  A  haberle başlayan        : [t0 − PRE, t0] içinde güçlü haber
  B  yükseliş sırasında haber: A değil, (t0, hafta sonu] içinde güçlü haber
  C  habersiz                : [t0 − PRE, hafta sonu] içinde güçlü haber yok
t0 = hafta sonundan geriye 20 işlem günündeki en düşük kapanış günü. Haber günü = effective_date
(18:00 sonrası yayın ertesi işlem günü). Fiyatın sonucu olan bildirimler haber sayılmaz.
Tasarım Linear MEL-94'te sonuçtan önce kayıtlı.

Kullanım: python scripts/news_timing.py [--score scores_v2/honest_none_4_kural_pu]
"""

import argparse
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from evaluate_v2 import load_cases  # noqa: E402

from bistmd.eval import weekly as W  # noqa: E402
from bistmd.features.kap import categorize  # noqa: E402
from bistmd.paths import DB_PATH, INTERIM  # noqa: E402

K = 20
LOOK = 20          # t0 arama penceresi (işlem günü)
POST = 10          # hafta sonrası (yalnız geçmiş analiz)
N_BOOT = 2000
REACTIVE = ("price_reactive", "unusual_move", "circuit_breaker")
YEARS = (2017, 2026)


def load():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    px = con.execute("SELECT ticker, date, close FROM prices WHERE close IS NOT NULL ORDER BY ticker, date").df()
    kap = con.execute("SELECT ticker, effective_date, subject, summary FROM kap_disclosures "
                      "WHERE effective_date IS NOT NULL").df()
    kap_end = con.execute("SELECT max(effective_date) FROM kap_disclosures").fetchone()[0]
    kap["group"] = categorize(kap["subject"], kap["summary"]).to_numpy()
    return px, kap, pd.Timestamp(kap_end)


def positions(px: pd.DataFrame, rows: pd.DataFrame) -> pd.DataFrame:
    """Her satır (ticker, week_end) için hafta sonu işlem günü sırası (i_end) ve t0 sırası (i_t0)."""
    out = []
    for t, r in rows.groupby("ticker"):
        p = px[px["ticker"] == t]
        if p.empty:
            continue
        d = p["date"].to_numpy()
        c = p["close"].to_numpy()
        ie = np.searchsorted(d, r["week_end"].to_numpy().astype(d.dtype), side="right") - 1
        ok = ie >= LOOK
        i0 = np.full(len(r), -1)
        for j in np.where(ok)[0]:
            lo = ie[j] - LOOK + 1
            i0[j] = lo + int(np.argmin(c[lo:ie[j] + 1]))
        out.append(r.assign(i_end=ie, i_t0=i0, runup=np.where(ok, c[ie] / c[np.maximum(i0, 0)] - 1, np.nan)))
    return pd.concat(out, ignore_index=True)


def news_flags(px, kap, rows, groups, pre, post=POST):
    """rows: ticker, i_end, i_t0 → n_pre, n_during, n_post (verilen grup bildirimleri)."""
    res = {k: np.zeros(len(rows), dtype=int) for k in ("pre", "during", "post")}
    rows = rows.reset_index(drop=True)
    kg = kap[kap["group"].isin(groups)]
    for t, r in rows.groupby("ticker"):
        d = px.loc[px["ticker"] == t, "date"].to_numpy()
        e = kg.loc[kg["ticker"] == t, "effective_date"].to_numpy().astype(d.dtype)
        if len(e) == 0:
            continue
        ei = np.sort(np.searchsorted(d, e, side="left"))   # haber işlem günü sırası
        cnt = lambda a, b: np.searchsorted(ei, b, side="right") - np.searchsorted(ei, a, side="left")  # noqa: E731
        i0, ie = r["i_t0"].to_numpy(), r["i_end"].to_numpy()
        res["pre"][r.index] = cnt(i0 - pre, i0)
        res["during"][r.index] = cnt(i0 + 1, ie)
        res["post"][r.index] = cnt(ie + 1, ie + post)
    return pd.DataFrame(res)


def classify(f: pd.DataFrame) -> pd.Series:
    return pd.Series(np.where(f["pre"] > 0, "A", np.where(f["during"] > 0, "B", "C")), index=f.index)


def boot_diff(df, col, val, rng):
    """isabet − boş alarm oranı farkı, hisse düzeyinde küme bootstrap."""
    x = (df[col] == val).astype(float)
    g = pd.DataFrame({"t": df["ticker"], "h": df["hit"], "x": x})
    agg = g.groupby(["t", "h"])["x"].agg(["sum", "size"]).unstack(fill_value=0)
    s1, n1 = agg[("sum", 1)].to_numpy(), agg[("size", 1)].to_numpy()
    s0, n0 = agg[("sum", 0)].to_numpy(), agg[("size", 0)].to_numpy()
    pt = s1.sum() / n1.sum() - s0.sum() / n0.sum()
    idx = rng.integers(0, len(agg), (N_BOOT, len(agg)))
    bs = s1[idx].sum(1) / np.maximum(n1[idx].sum(1), 1) - s0[idx].sum(1) / np.maximum(n0[idx].sum(1), 1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return pt, lo, hi


def report(al, rnd, label, rng):
    lab = al[al["y"].notna()].assign(hit=lambda d: (d["y"] == 1).astype(int))
    print(f"\n-- {label}: {len(lab):,} alarm ({lab['hit'].sum()} isabet, {(1 - lab['hit']).sum():,} boş), "
          f"rastgele taban {len(rnd):,}")
    print(f"   {'sınıf':28s} {'isabet':>7s} {'boş':>7s} {'rastgele':>8s}  fark isabet−boş [%95 GA]   sınıf içi isabet")
    names = {"A": "A haberle başlayan", "B": "B yükseliş sırasında", "C": "C habersiz"}
    for c in "ABC":
        pt, lo, hi = boot_diff(lab, "cls", c, rng)
        sig = "anlamlı" if lo > 0 or hi < 0 else "anlamsız"
        prec = lab.loc[lab["cls"] == c, "hit"].mean()
        print(f"   {names[c]:28s} {(lab.loc[lab.hit == 1, 'cls'] == c).mean():7.3f} "
              f"{(lab.loc[lab.hit == 0, 'cls'] == c).mean():7.3f} {(rnd['cls'] == c).mean():8.3f}  "
              f"{pt:+.3f} [{lo:+.3f}, {hi:+.3f}] {sig:8s}  {prec:.3f}")
    return lab


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", default="scores_v2/honest_none_4_kural_pu")
    args = ap.parse_args()
    rng = np.random.default_rng(0)

    exact, core6, any12 = load_cases()
    px, kap, kap_end = load()
    wk = pd.read_parquet(INTERIM / f"{args.score}.parquet")
    wk["week"] = pd.PeriodIndex(wk["week"], freq="W-FRI")
    wk = wk[wk["week_end"].dt.year.between(*YEARS) & (wk["week_end"] <= kap_end)]
    lab = W.week_labels(wk, core6, any12)
    al = lab[lab["rank"] <= K].copy()
    pool = lab[lab["rank"] > K]
    rnd = pool.sample(n=min(5 * len(al), len(pool)), random_state=0).copy()
    print(f"KAP verisi sonu {kap_end:%Y-%m-%d}; dönem {YEARS[0]}–{YEARS[1]}; alarm {len(al):,}, rastgele {len(rnd):,}")

    al = positions(px, al)
    rnd = positions(px, rnd)
    al, rnd = al[al["i_t0"] >= 0].reset_index(drop=True), rnd[rnd["i_t0"] >= 0].reset_index(drop=True)
    strong = ("strong_news",)
    for d in (al, rnd):
        f = news_flags(px, kap, d, strong, 10)
        d[["pre", "during", "post"]] = f.to_numpy()
        d["cls"] = classify(f).to_numpy()
        d["t0_lag"] = d["i_end"] - d["i_t0"]

    print("\n== Ana sonuç (güçlü haber, önce 10 işlem günü) ==")
    lab_al = report(al, rnd, "2017–2026", rng)
    print(f"   yükseliş (t0 → hafta sonu) medyanı: isabet {lab_al.loc[lab_al.hit == 1, 'runup'].median():.3f}, "
          f"boş {lab_al.loc[lab_al.hit == 0, 'runup'].median():.3f}, rastgele {rnd['runup'].median():.3f}; "
          f"t0'dan hafta sonuna gün medyanı: isabet {lab_al.loc[lab_al.hit == 1, 't0_lag'].median():.0f}, "
          f"boş {lab_al.loc[lab_al.hit == 0, 't0_lag'].median():.0f}")
    pend = kap_end - pd.Timedelta(days=21)
    s = lab_al[lab_al["week_end"] <= pend]
    print(f"   sonraki {POST} işlem gününde güçlü haber (hafta sonu ≤ {pend:%Y-%m-%d}): "
          f"isabet {(s.loc[s.hit == 1, 'post'] > 0).mean():.3f}, boş {(s.loc[s.hit == 0, 'post'] > 0).mean():.3f}, "
          f"rastgele {(rnd.loc[rnd['week_end'] <= pend, 'post'] > 0).mean():.3f}")
    tmp = s.assign(cls=np.where(s["post"] > 0, "P", "-"))
    pt, lo, hi = boot_diff(tmp, "cls", "P", rng)
    print(f"   fark isabet−boş {pt:+.3f} [{lo:+.3f}, {hi:+.3f}]")

    # fiyatın sonucu olan bildirimler ve söylenti açıklamaları (ayrı rapor)
    print("\n== Diğer bildirimler: [t0−10, hafta sonu] içinde en az bir tane ==")
    for grp in (REACTIVE, ("rumor",), ("weak_news",), ("financial_report",)):
        fa = news_flags(px, kap, al, grp, 10)
        fr = news_flags(px, kap, rnd, grp, 10)
        x = ((fa["pre"] + fa["during"]) > 0).to_numpy()
        h = al["y"].to_numpy()
        print(f"   {'+'.join(grp):45s} isabet {x[h == 1].mean():.3f}  boş {x[h == 0].mean():.3f}  "
              f"rastgele {((fr['pre'] + fr['during']) > 0).mean():.3f}")

    print("\n== Dönemler ==")
    for y0, y1 in ((2017, 2021), (2022, 2026)):
        m = al["week_end"].dt.year.between(y0, y1)
        report(al[m], rnd[rnd["week_end"].dt.year.between(y0, y1)], f"{y0}–{y1}", rng)

    print("\n== Duyarlılık ==")
    for name, grp, pre in (("önce 5 gün", strong, 5), ("önce 20 gün", strong, 20),
                           ("güçlü + zayıf haber", ("strong_news", "weak_news"), 10)):
        a2, r2 = al.copy(), rnd.copy()
        for d in (a2, r2):
            d["cls"] = classify(news_flags(px, kap, d, grp, pre)).to_numpy()
        report(a2, r2, name, rng)
    for post in (5, 20):
        f = news_flags(px, kap, s.reset_index(drop=True), strong, 10, post)
        x, h = (f["post"] > 0).to_numpy(), s["hit"].to_numpy()
        print(f"   sonraki {post} gün güçlü haber: isabet {x[h == 1].mean():.3f}, boş {x[h == 0].mean():.3f}")

    # ikincil: ilk 20 içinde A sınıfını sona itmek ilk 10 isabetini artırıyor mu?
    print("\n== İkincil: A sınıfı sona itilince ilk 10 isabeti (hafta başına) ==")
    a = al.assign(h=(al["y"] == 1).astype(float))
    a["rank2"] = a["rank"] + np.where(a["cls"] == "A", 100, 0)
    a["r2"] = a.groupby("week")["rank2"].rank(method="first")
    base = a[a["rank"] <= 10].groupby("week")["h"].sum() / 10
    new = a[a["r2"] <= 10].groupby("week")["h"].sum().reindex(base.index, fill_value=0) / 10
    d = (new - base).to_numpy()
    bs = d[rng.integers(0, len(d), (N_BOOT, len(d)))].mean(1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    print(f"   ilk 10 isabeti {base.mean():.4f} → {new.mean():.4f}; fark {d.mean():+.4f} [{lo:+.4f}, {hi:+.4f}] "
          f"({len(d)} hafta)")

    out = INTERIM / "results"
    al.to_parquet(out / "news_timing_alarms.parquet", index=False)


if __name__ == "__main__":
    main()
