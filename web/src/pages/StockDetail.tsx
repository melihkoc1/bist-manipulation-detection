import { useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { addDays, dayDiff, firstAlert, useIndex, useStock, weekMonday, type Index, type StockData } from "../data";
import { useT } from "../i18n";
import { Page } from "../components/Layout";
import { Search, Tri } from "../components/Icons";
import { ChartLegend, DECISION_TYPES, Loading, ShapPanel, WhyPanel } from "../components/ui";
import { StockChart } from "../components/charts";

const RANGES = [["6A", "6M", 183], ["1Y", "1Y", 365], ["2Y", "2Y", 730], ["Tümü", "All", 0]] as const;

export default function StockDetail() {
  const { data: idx, error } = useIndex();
  const { ticker = "IZFAS" } = useParams();
  if (!idx) return <Page><Loading error={error} /></Page>;
  return <Detail key={ticker} idx={idx} ticker={ticker.toUpperCase()} />;
}

export function StockSearch({ idx }: { idx: Index }) {
  const f = useT();
  const nav = useNavigate();
  const [q, setQ] = useState("");
  const hits = useMemo(() => {
    const s = q.trim().toLocaleUpperCase("tr");
    if (!s) return [];
    return idx.stocks.filter((x) => x.t.startsWith(s) || x.name.toLocaleUpperCase("tr").includes(s)).slice(0, 8);
  }, [q, idx]);
  const go = (t: string) => { setQ(""); nav(`/hisse/${t}`); };
  return (
    <div style={{ flex: "0 1 360px", position: "relative" }}>
      <label htmlFor="q" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 6 }} className="muted">{f.L("Hisse ara", "Search stock")}</label>
      <span style={{ position: "absolute", left: 12, top: 38, color: "var(--faint)" }}><Search size={18} /></span>
      <input id="q" className="field" type="search" autoComplete="off" placeholder={f.L("Kod veya şirket adı, ör. SANEL", "Ticker or company, e.g. SANEL")}
             value={q} onChange={(e) => setQ(e.target.value)}
             onKeyDown={(e) => { if (e.key === "Enter" && hits[0]) go(hits[0].t); }}
             role="combobox" aria-expanded={hits.length > 0} aria-controls="q-list" aria-autocomplete="list" />
      {hits.length > 0 && (
        <ul id="q-list" role="listbox" className="card" style={{ position: "absolute", zIndex: 5, top: "100%", left: 0, right: 0, marginTop: 4, listStyle: "none", padding: 4 }}>
          {hits.map((h) => (
            <li key={h.t} role="option" aria-selected="false">
              <button type="button" onClick={() => go(h.t)} style={{ width: "100%", textAlign: "left", display: "flex", gap: 10, alignItems: "baseline", padding: "8px 10px", border: 0, background: "transparent", borderRadius: 8, cursor: "pointer", fontFamily: "inherit", color: "var(--text)" }}>
                <strong style={{ minWidth: 56 }}>{h.t}</strong>
                <span style={{ fontSize: 12, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} className="muted">{h.name}</span>
                {h.nDec > 0 && <span className="badge b-orange" style={{ marginLeft: "auto" }}><Tri size={9} />{h.nDec}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Detail({ idx, ticker }: { idx: Index; ticker: string }) {
  const f = useT();
  const st = useStock(ticker);
  const meta = idx.stocks.find((s) => s.t === ticker);
  return (
    <Page gap={20}>
      <section style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "flex-end", gap: 20 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <p className="eyebrow">{f.L("Hisse detayı", "Stock detail")}</p>
          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 14 }}>
            <h1 style={{ fontSize: "clamp(40px, 6vw, 56px)", lineHeight: 1, fontWeight: 700, letterSpacing: "-.03em" }}>{ticker}</h1>
            {meta && meta.nDec > 0 && <span className="badge b-orange" style={{ fontSize: 13, padding: "5px 11px" }}><Tri size={12} />{f.L(`${meta.nDec} SPK kararı`, `${meta.nDec} SPK decision${meta.nDec > 1 ? "s" : ""}`)}</span>}
          </div>
          <p style={{ fontSize: 16 }} className="muted">{meta?.name || "—"} · BIST</p>
        </div>
        <StockSearch idx={idx} />
      </section>
      {!meta ? (
        <div className="card" style={{ padding: 24 }}><p>{f.L("Bu kodla puanlanmış bir hisse bulunamadı.", "No scored stock with this ticker.")}</p></div>
      ) : !st.data ? <Loading error={st.error} /> : <Body idx={idx} d={st.data} />}
    </Page>
  );
}

function Body({ idx, d }: { idx: Index; d: StockData }) {
  const f = useT();
  const [sp, setSp] = useSearchParams();
  const known = d.cases.filter((c) => c.known && c.core);
  const alarms = known.map((c) => ({ c, a: firstAlert(d.ranks, c.start, c.end) })).filter((x) => x.a);
  const best = d.ranks.reduce<typeof d.ranks[number] | undefined>((b, r) => (!b || r[1] < b[1] ? r : b), undefined);
  const hafta = sp.get("hafta");
  const selected = d.ranks.find((r) => r[0] === hafta) ?? alarms[0]?.a ?? best;
  const lastDate = d.prices.d[d.prices.d.length - 1] ?? selected?.[0] ?? "2026-01-01";
  const firstDate = d.prices.d[0] ?? "2010-01-01";
  const [range, setRange] = useState<number>(known.length || hafta ? 2 : 3);
  const days = RANGES[range][2];
  const [anchor] = useState(selected?.[0] ?? lastDate); // grafik penceresi tıklamayla kaymasın
  let from = days ? addDays(anchor, -Math.round(days * 0.45)) : firstDate;
  let to = days ? addDays(from, days) : lastDate;
  if (days && to > lastDate) { to = lastDate; from = addDays(to, -days); }
  if (from < firstDate) from = firstDate;

  const inRange = d.ranks.filter((r) => r[0] >= from && r[0] <= to);
  const top20 = inRange.filter((r) => r[1] <= 20).length;
  const expTop20 = inRange.reduce((s, r) => s + Math.min(1, 20 / r[2]), 0);
  const firstDec = d.decisions[0];
  const decYears = d.decisions.length ? `${d.decisions[0].date.slice(0, 4)}–${d.decisions[d.decisions.length - 1].date.slice(0, 4)}` : "";
  const leadOverSpk = alarms.length ? (() => {
    const x = alarms[0];
    const dec = d.decisions.find((q) => q.date >= x.c.start);
    return dec ? dayDiff(dec.date, x.a![0]) : null;
  })() : null;
  const pick = (w: string) => { const n = new URLSearchParams(sp); n.set("hafta", w); setSp(n, { replace: true }); };

  const card = { padding: "18px 20px", display: "flex", flexDirection: "column", gap: 8 } as const;
  const big = { fontSize: 44, fontWeight: 600, letterSpacing: "-.02em", lineHeight: 1 } as const;
  return (
    <>
      <section aria-label={f.L("Özet göstergeler", "Summary")} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
        <div className="card" style={card}>
          <p style={{ fontSize: 13, fontWeight: 500 }} className="muted">{f.L("En iyi haftalık sıra", "Best weekly rank")}</p>
          {best ? <>
            <p style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}><strong style={big}>{best[1]}</strong>
              <span style={{ fontSize: 14 }} className="muted">/ {best[2]} · {f.L(`${f.date(best[0])} haftası`, `week of ${f.date(best[0])}`)}</span></p>
            <p style={{ fontSize: 13 }} className="faint">{f.L(`rastgele beklenen medyan sıra ~${Math.round(best[2] / 2)}`, `random median rank ~${Math.round(best[2] / 2)}`)}</p>
          </> : <p className="muted">—</p>}
        </div>
        <div className="card" style={card}>
          <p style={{ fontSize: 13, fontWeight: 500 }} className="muted">{f.L("İlk 20'de geçen hafta (grafik aralığı)", "Weeks in the top 20 (chart range)")}</p>
          <p style={{ display: "flex", alignItems: "baseline", gap: 10 }}><strong style={big}>{top20}</strong><span style={{ fontSize: 14 }} className="muted">{f.L("hafta", "weeks")} / {inRange.length}</span></p>
          <p style={{ fontSize: 13 }} className="faint">{f.L(`rastgele beklenti ${f.num(expTop20, 1)} hafta`, `random expectation ${f.num(expTop20, 1)} weeks`)}</p>
        </div>
        <div className="card" style={card}>
          <p style={{ fontSize: 13, fontWeight: 500 }} className="muted">{f.L("SPK kararı", "SPK decisions")}</p>
          <p style={{ display: "flex", alignItems: "baseline", gap: 10 }}><strong style={big}>{d.decisions.length}</strong>
            <span style={{ fontSize: 14 }} className="muted">{d.decisions.length ? f.L(`karar · ${decYears}`, `decisions · ${decYears}`) : ""}</span></p>
          <p style={{ fontSize: 13 }} className="faint">
            {leadOverSpk != null ? (leadOverSpk > 0
              ? f.L(`ilk alarm, SPK'nın ilk kararından ${leadOverSpk} gün önce`, `first alarm ${leadOverSpk} days before SPK's first decision`)
              : f.L(`ilk alarm, SPK'nın ilk kararından ${-leadOverSpk} gün sonra`, `first alarm ${-leadOverSpk} days after SPK's first decision`))
              : firstDec ? f.L("dönemi yazan vakada alarm yok", "no alarm in a case with a stated period") : f.L("bu hisse için SPK kararı yok", "no SPK decision for this stock")}
          </p>
        </div>
      </section>

      <section className="card" aria-labelledby="ch-h" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
          <h2 id="ch-h" style={{ fontSize: 16, fontWeight: 600 }}>{f.L("Fiyat, hacim ve haftalık sıra", "Price, volume and weekly rank")}</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center" }}>
            <div className="seg" role="group" aria-label={f.L("Tarih aralığı", "Date range")}>
              {RANGES.map((r, i) => <button key={r[0]} type="button" className={i === range ? "on" : ""} aria-pressed={i === range} onClick={() => setRange(i)}>{f.L(r[0], r[1])}</button>)}
            </div>
            <span className="muted" style={{ fontSize: 13 }}>{f.date(from)} – {f.date(to)}</span>
          </div>
        </div>
        <ChartLegend threshold alarmLabel={f.L("İlk alarm (ilk 20)", "First alarm (top 20)")} />
        <StockChart data={d} from={from} to={to} selected={selected?.[0]} onPick={pick}
                    alarms={alarms.map((x) => ({ date: x.a![0], label: f.L(`İlk alarm · ${dayDiff(x.a![0], x.c.start)}. gün`, `First alarm · day ${dayDiff(x.a![0], x.c.start)}`) }))}
                    ariaLabel={f.L(`${d.ticker} fiyat, hacim ve haftalık sıra grafiği, ${f.date(from)}–${f.date(to)}. ${known.length} SPK dönemi turuncu bantla, ${d.decisions.length} SPK kararı üçgenle gösterildi.`,
                                   `${d.ticker} price, volume and weekly rank, ${f.date(from)}–${f.date(to)}. ${known.length} SPK periods as orange bands, ${d.decisions.length} SPK decisions as triangles.`)} />
        <p style={{ fontSize: 12 }} className="faint">{f.L("Grafiğe tıklayarak bir hafta seçin; \"Neden şüpheli?\" paneli o haftayı gösterir.", "Click the chart to pick a week; the \"Why suspicious?\" panel follows it.")}</p>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(440px, 100%), 1fr))", gap: 20 }}>
        <section className="card" aria-labelledby="why-h" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
            <h2 id="why-h" style={{ fontSize: 16, fontWeight: 600 }}>{f.L("Neden şüpheli?", "Why suspicious?")}</h2>
            {selected && <span style={{ fontSize: 13 }} className="muted">{f.range(weekMonday(selected[0]), selected[0])} · {f.L("sıra", "rank")} {selected[1]} / {selected[2]}</span>}
          </div>
          {selected ? <WhyPanel vals={selected.slice(3, 9) as (number | null)[]} thr={idx.rules} /> : <p className="muted">—</p>}
          {selected && <ShapPanel shap={d.shap?.[selected[0]]} feats={idx.shapFeats} />}
        </section>

        <section className="card" aria-labelledby="spk-h" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
          <h2 id="spk-h" style={{ fontSize: 16, fontWeight: 600 }}>{f.L("SPK kararları", "SPK decisions")}</h2>
          {d.decisions.length === 0 ? <p className="muted" style={{ fontSize: 14 }}>{f.L("Bu hisse için SPK bülteninde manipülasyon kararı bulunmadı. Bu, hissenin \"temiz\" olduğu anlamına gelmez.", "No manipulation decision for this stock in SPK bulletins. That does not mean the stock is \"clean\".")}</p> : (
            <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column" }}>
              {d.decisions.map((e, i) => {
                const al = alarms.find((x) => e.date >= x.c.start)?.a;
                return (
                  <li key={i} style={{ display: "grid", gridTemplateColumns: "20px 1fr", gap: 14 }}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                      <span style={{ width: 12, height: 12, marginTop: 5, borderRadius: "50%", background: "var(--text)", border: "2px solid var(--surface)", boxShadow: "0 0 0 1px var(--text)" }} />
                      {i < d.decisions.length - 1 && <span style={{ flex: 1, width: 2, background: "var(--line)" }} />}
                    </div>
                    <div style={{ paddingBottom: 18, display: "flex", flexDirection: "column", gap: 4 }}>
                      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8 }}>
                        <strong style={{ fontSize: 14 }}>{f.date(e.date)}</strong>
                        <span className="badge b-gray">{f.L(...(DECISION_TYPES[e.type] ?? [e.type, e.type]))}</span>
                      </div>
                      {e.pStart && <p style={{ fontSize: 13 }} className="muted">{f.L("SPK'nın belirttiği dönem", "Period stated by SPK")}: {f.date(e.pStart)} – {f.date(e.pEnd)}</p>}
                      <p style={{ fontSize: 12 }} className="faint">
                        {e.ref ? f.L(`SPK Bülteni ${e.ref}`, `SPK Bulletin ${e.ref}`) : f.L("SPK yaptırım kaydı", "SPK sanctions record")}
                        {al && dayDiff(e.date, al[0]) > 0 && dayDiff(e.date, al[0]) <= 1100 ? f.L(` · ilk alarmdan ${dayDiff(e.date, al[0])} gün sonra`, ` · ${dayDiff(e.date, al[0])} days after the first alarm`) : ""}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
          )}
        </section>
      </div>

      <KapList d={d} from={from} to={to} />
    </>
  );
}

const KAP_CATS = [["all", "Tümü", "All"], ["news", "Gerçek haber", "Real news"], ["price", "Fiyat hareketi açıklaması", "Price-move statement"], ["rumor", "Söylenti", "Rumor"], ["other", "Diğer", "Other"]] as const;
const KAP_CLS: Record<string, string> = { news: "tag b-teal", price: "tag b-gray", rumor: "tag b-amber", other: "tag b-gray" };

function KapList({ d, from, to }: { d: StockData; from: string; to: string }) {
  const f = useT();
  const [cat, setCat] = useState("all");
  const [q, setQ] = useState("");
  const [n, setN] = useState(15);
  const [inRange, setInRange] = useState(true);
  const list = useMemo(() => {
    const s = q.trim().toLocaleLowerCase("tr");
    return d.kap.filter((k) => (cat === "all" || k[2] === cat) && (!s || `${k[1]} ${k[4] ?? ""}`.toLocaleLowerCase("tr").includes(s))
      && (!inRange || (k[0] >= from && k[0] <= to)));
  }, [d, cat, q, inRange, from, to]);
  return (
    <section className="card" aria-labelledby="kap-h" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        <h2 id="kap-h" style={{ fontSize: 16, fontWeight: 600 }}>{f.L("KAP bildirimleri", "KAP disclosures")} <span style={{ fontWeight: 500 }} className="muted">· {list.length}</span></h2>
        <div style={{ position: "relative", flex: "0 1 320px" }}>
          <label htmlFor="kq" className="sr">{f.L("Bildirimlerde ara", "Search disclosures")}</label>
          <span style={{ position: "absolute", left: 13, top: 14, color: "var(--faint)" }}><Search size={16} /></span>
          <input id="kq" className="field" type="search" placeholder={f.L("Bildirimlerde ara", "Search disclosures")} value={q} onChange={(e) => { setQ(e.target.value); setN(15); }} />
        </div>
      </div>
      <div role="group" aria-label={f.L("Kategori filtresi", "Category filter")} style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {KAP_CATS.map(([k, tr, en]) => <button key={k} type="button" className={`fchip${cat === k ? " on" : ""}`} aria-pressed={cat === k} onClick={() => { setCat(k); setN(15); }}>{f.L(tr, en)}</button>)}
        <label style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 13, marginLeft: "auto", cursor: "pointer" }} className="muted">
          <input type="checkbox" checked={inRange} onChange={(e) => { setInRange(e.target.checked); setN(15); }} style={{ width: 18, height: 18, accentColor: "#2a9d8f" }} />
          {f.L(`Yalnızca grafik aralığı (${f.date(from)} – ${f.date(to)})`, `Chart range only (${f.date(from)} – ${f.date(to)})`)}
        </label>
      </div>
      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column" }}>
        {list.slice(0, n).map((k) => (
          <li key={k[3]} style={{ display: "grid", gridTemplateColumns: "100px 1fr auto", gap: 16, alignItems: "center", padding: "12px 4px", borderTop: "1px solid var(--line)", fontSize: 14 }}>
            <span className="muted">{f.date(k[0])}</span>
            <a href={`https://www.kap.org.tr/tr/Bildirim/${k[3]}`} target="_blank" rel="noreferrer" style={{ color: "var(--text)", textDecoration: "none", fontWeight: 500, minWidth: 0, overflowWrap: "anywhere", display: "flex", flexDirection: "column", gap: 2 }}>
              <span>{k[4] || k[1] || "—"}</span>{k[4] && k[1] && <span style={{ fontSize: 12, fontWeight: 400 }} className="faint">{k[1]}</span>}</a>
            <span className={KAP_CLS[k[2]]}>{f.L(...(KAP_CATS.find((c) => c[0] === k[2])!.slice(1) as [string, string]))}</span>
          </li>
        ))}
        {list.length === 0 && <li className="muted" style={{ padding: "12px 4px", borderTop: "1px solid var(--line)", fontSize: 14 }}>{f.L("Bildirim yok.", "No disclosures.")}</li>}
      </ul>
      {list.length > n && <button type="button" className="btn sm" style={{ alignSelf: "flex-start" }} onClick={() => setN(n + 30)}>{f.L(`${Math.min(30, list.length - n)} bildirim daha göster`, `Show ${Math.min(30, list.length - n)} more`)}</button>}
      <p style={{ fontSize: 12 }} className="faint">{f.L("Kategoriler otomatik sınıflandırmadır (elle kontrol edilen örnekte %93 doğru).", "Categories come from an automatic classifier (93% accurate on a hand-checked sample).")}</p>
    </section>
  );
}
