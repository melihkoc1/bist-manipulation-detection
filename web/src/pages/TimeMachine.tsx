import { useMemo, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { addDays, EXAMPLES, isNewIpo, useIndex, useIpo, useJson, useStock, weekMonday, type Index, type ListRow, type WeekEntry } from "../data";
import { useT } from "../i18n";
import { Page } from "../components/Layout";
import { Arrow, Cal, ChevL, ChevR, Clock, Warn } from "../components/Icons";
import { Loading, MODEL_NAMES, Note, ReasonChips, ShapPanel, SpkBadge, SpkLegend, WhyPanel } from "../components/ui";
import { MiniPrice } from "../components/charts";

const LENS = [10, 20, 50];

function weekNo(end: string) {
  const d = new Date(end + "T00:00:00Z");
  const jan1 = Date.UTC(d.getUTCFullYear(), 0, 1);
  return Math.ceil(((d.getTime() - jan1) / 864e5 + 1) / 7);
}

export default function TimeMachine() {
  const { data: idx, error } = useIndex();
  if (!idx) return <Page><Loading error={error} /></Page>;
  return <TM idx={idx} />;
}

function TM({ idx }: { idx: Index }) {
  const f = useT();
  const [sp, setSp] = useSearchParams();
  const dateRef = useRef<HTMLInputElement>(null);
  const weeks = idx.weeks;
  const week = sp.get("hafta") && weeks.some((w) => w.end === sp.get("hafta")) ? sp.get("hafta")! : EXAMPLES[0].week;
  const model = idx.models.includes(sp.get("model") ?? "") ? sp.get("model")! : idx.models[0];
  const k = LENS.includes(Number(sp.get("k"))) ? Number(sp.get("k")) : 20;
  const wi = weeks.findIndex((w) => w.end === week);
  const year = week.slice(0, 4);
  const yf = useJson<{ weeks: WeekEntry[] }>(`weeks/${year}.json`);
  const entry = yf.data?.weeks.find((w) => w.end === week);
  const rows: ListRow[] = entry?.lists[model]?.slice(0, k) ?? [];
  const selT = sp.get("sec") && rows.some((r) => r[0] === sp.get("sec")) ? sp.get("sec")! : (rows.find((r) => r[4] === "in") ?? rows[0])?.[0];
  const sel = rows.find((r) => r[0] === selT);
  const names = useMemo(() => new Map(idx.stocks.map((s) => [s.t, s.name])), [idx]);
  const ipo = useIpo().data;

  const set = (p: Record<string, string | null>) => {
    const n = new URLSearchParams(sp);
    for (const [a, b] of Object.entries(p)) if (b == null) n.delete(a); else n.set(a, b);
    setSp(n, { replace: true });
  };
  const goWeek = (end: string, sec: string | null = null) => set({ hafta: end, sec });
  const pickDate = (d: string) => {
    const w = weeks.find((x) => x.end >= d) ?? weeks[weeks.length - 1];
    goWeek(w.end);
  };
  const onYear = (y: number) => {
    const target = `${y}${week.slice(4)}`;
    pickDate(target);
  };

  const hits = rows.filter((r) => r[4] === "in").length;
  const randExp = entry ? (k * entry.inPeriod) / entry.n : 0;
  const modelName = (m: string) => (m === "4_kural_pu" ? f.L("Kural + PU (önerilen)", "Rules + PU (recommended)") : m === "3b_pu_bagging" ? f.L("PU öğrenme", "PU learning") : f.L(...MODEL_NAMES[m]));
  const wkLabel = f.L(`Hafta ${weekNo(week)} · ${year}`, `Week ${weekNo(week)} · ${year}`);

  return (
    <Page gap={20}>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <h1 style={{ fontSize: 30, fontWeight: 700, letterSpacing: "-.02em" }}>{f.L("Zaman makinesi", "Time machine")}</h1>
        <p className="muted" style={{ fontSize: 15, maxWidth: 720 }}>
          {f.L("Geçmiş bir hafta seçin: sistemin o hafta ne listelediğini ve SPK'nın sonradan ne yaptığını yan yana görün.",
               "Pick a past week: see what the system listed that week next to what SPK did later.")}
        </p>
      </div>

      <section className="card" aria-label={f.L("Hafta ve model seçimi", "Week and model")} style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "16px 24px", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, flex: "1 1 auto", maxWidth: 360 }}>
            <button type="button" className="icon-btn" aria-label={f.L("Önceki hafta", "Previous week")} disabled={wi <= 0} onClick={() => goWeek(weeks[wi - 1].end)}><ChevL size={18} /></button>
            <button type="button" aria-label={f.L("Takvimden hafta seç", "Pick a week from the calendar")}
                    onClick={() => { const el = dateRef.current; if (el) { try { el.showPicker(); } catch { el.focus(); } } }}
                    style={{ position: "relative", flex: 1, minHeight: 44, padding: "0 14px", display: "inline-flex", alignItems: "center", gap: 10, border: "1px solid var(--line-2)", borderRadius: 10, background: "var(--surface)", color: "var(--text)", fontFamily: "inherit", cursor: "pointer" }}>
              <Cal size={18} />
              <span style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", lineHeight: 1.2 }}>
                <span style={{ fontSize: 11 }} className="faint">{wkLabel}</span>
                <strong style={{ fontSize: 15, fontWeight: 600 }}>{f.range(weekMonday(week), week)}</strong>
              </span>
              <input ref={dateRef} type="date" tabIndex={-1} aria-hidden="true" min={weeks[0].start} max={weeks[weeks.length - 1].end} value={week}
                     onChange={(e) => e.target.value && pickDate(e.target.value)}
                     style={{ position: "absolute", left: 0, bottom: 0, width: 1, height: 1, opacity: 0, pointerEvents: "none" }} />
            </button>
            <button type="button" className="icon-btn" aria-label={f.L("Sonraki hafta", "Next week")} disabled={wi >= weeks.length - 1} onClick={() => goWeek(weeks[wi + 1].end)}><ChevR size={18} /></button>
          </div>
          <div style={{ flex: "1 1 420px", display: "flex", flexDirection: "column", gap: 4, minWidth: 220 }}>
            <label htmlFor="yr" className="sr">{f.L("Zaman çizelgesi, yıl", "Timeline, year")}</label>
            <input id="yr" type="range" min={Number(weeks[0].end.slice(0, 4))} max={Number(weeks[weeks.length - 1].end.slice(0, 4))} step={1}
                   value={Number(year)} onChange={(e) => onYear(Number(e.target.value))} aria-valuetext={year} />
            <div aria-hidden="true" style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }} className="faint">
              {[2012, 2014, 2016, 2018, 2020, 2022, 2024, 2026].map((y) => <span key={y}>{y}</span>)}
            </div>
          </div>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "12px 24px", alignItems: "center", paddingTop: 14, borderTop: "1px solid var(--line)" }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
            <span style={{ fontSize: 13 }} className="muted">{f.L("Örnekler", "Examples")}</span>
            {EXAMPLES.map((e) => (
              <button key={e.t} type="button" className={`ex${week === e.week ? " on" : ""}`} aria-pressed={week === e.week} onClick={() => goWeek(e.week, e.t)}>
                <Clock size={12} />{e.t} · {f.month(e.week)}
              </button>
            ))}
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "12px 20px", alignItems: "center", marginLeft: "auto" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              <span id="mlab" style={{ fontSize: 13 }} className="muted">Model</span>
              <div className="seg" role="group" aria-labelledby="mlab">
                {idx.models.map((m) => <button key={m} type="button" className={m === model ? "on" : ""} aria-pressed={m === model} onClick={() => set({ model: m, sec: null })}>{modelName(m)}</button>)}
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span id="llab" style={{ fontSize: 13 }} className="muted">{f.L("Liste", "List")}</span>
              <div className="seg" role="group" aria-labelledby="llab">
                {LENS.map((n) => <button key={n} type="button" className={n === k ? "on" : ""} aria-pressed={n === k} onClick={() => set({ k: String(n) })}>{n}</button>)}
              </div>
            </div>
          </div>
        </div>
      </section>

      {!entry ? <Loading error={yf.error} /> : (
        <>
          <section aria-label={f.L("Hafta özeti", "Week summary")} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(240px, 45%), 1fr))", gap: 16 }}>
            <div className="card" style={{ padding: "18px 20px", display: "flex", flexDirection: "column", gap: 8 }}>
              <p style={{ fontSize: 13, fontWeight: 500 }} className="muted">{f.L("SPK manipülasyon dönemindeki hisse", "Stocks inside an SPK manipulation period")}</p>
              <p style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
                <strong style={{ fontSize: 40, fontWeight: 600, letterSpacing: "-.02em", lineHeight: 1, color: hits ? "var(--green-ink)" : "var(--text)" }}>{hits}</strong>
                <span style={{ fontSize: 20 }} className="muted">/ {k}</span>
              </p>
              <p style={{ fontSize: 13 }} className="faint">{f.L(`rastgele beklenti ${f.num(randExp, 2)} · o hafta ${entry.inPeriod} hisse dönemde`, `random expectation ${f.num(randExp, 2)} · ${entry.inPeriod} stocks in a period that week`)}</p>
            </div>
            <div className="card" style={{ padding: "18px 20px", display: "flex", flexDirection: "column", gap: 8 }}>
              <p style={{ fontSize: 13, fontWeight: 500 }} className="muted">{f.L("O hafta puanlanan hisse", "Stocks scored that week")}</p>
              <strong style={{ fontSize: 40, fontWeight: 600, letterSpacing: "-.02em", lineHeight: 1 }}>{entry.n}</strong>
              <p style={{ fontSize: 13 }} className="faint">{f.L(`ilk ${k} = en şüpheli ${f.pct(k / entry.n, 1)}`, `top ${k} = most suspicious ${f.pct(k / entry.n, 1)}`)}</p>
            </div>
            <div className="card" style={{ padding: "18px 20px", display: "flex", flexDirection: "column", gap: 8 }}>
              <p style={{ fontSize: 13, fontWeight: 500 }} className="muted">{f.L("Seçili hafta", "Selected week")}</p>
              <strong style={{ fontSize: 30, fontWeight: 600, letterSpacing: "-.02em", lineHeight: 1.15 }}>{f.range(weekMonday(week), week)}</strong>
              <p style={{ fontSize: 13 }} className="faint">{modelName(model)} · {f.L("yalnızca o güne kadarki veri", "data up to that day only")}</p>
            </div>
          </section>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 20, alignItems: "flex-start" }}>
            <section className="card tm-table" aria-labelledby="tbl-h" style={{ flex: "999 1 640px", minWidth: 0, overflow: "hidden" }}>
              <div style={{ padding: "14px 16px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                <h2 id="tbl-h" style={{ fontSize: 16, fontWeight: 600 }}>{f.L(`Haftalık şüphe listesi · ilk ${k}`, `Weekly suspicion list · top ${k}`)}</h2>
                <SpkLegend />
              </div>
              <div style={{ overflowX: "auto" }}>
                <table className="t">
                  <caption className="sr">{f.L("Seçili haftada şüphe skoruna göre sıralanmış hisseler", "Stocks ranked by suspicion in the selected week")}</caption>
                  <thead><tr>
                    <th scope="col" style={{ width: 56 }}>{f.L("Sıra", "Rank")}</th>
                    <th scope="col">{f.L("Hisse · Şirket", "Stock · Company")}</th>
                    <th scope="col" style={{ width: 170 }} title={f.L("Haftanın hisselerinin yüzde kaçından daha şüpheli", "Share of that week's stocks it outranks")}>{f.L("Şüphe yüzdeliği", "Suspicion percentile")}</th>
                    <th scope="col">{f.L("Nedenler", "Reasons")}</th>
                    <th scope="col">{f.L("Sonradan SPK", "SPK later")}</th>
                  </tr></thead>
                  <tbody>
                    {rows.map((r) => (
                      <Row key={r[0]} r={r} name={names.get(r[0]) ?? ""} on={r[0] === selT} cut={k === 50 && r[1] === 21}
                           thr={idx.rules} pick={() => set({ sec: r[0] })} ipo={isNewIpo(ipo, r[0], week)} />
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {sel && <Preview idx={idx} row={sel} name={names.get(sel[0]) ?? ""} week={week} n={entry.n} />}

            <section className="tm-cards" aria-labelledby="ls-h" style={{ flexDirection: "column", gap: 8, width: "100%" }}>
              <h2 id="ls-h" style={{ fontSize: 16, fontWeight: 600 }}>{f.L(`Şüphe listesi · ilk ${k}`, `Suspicion list · top ${k}`)}</h2>
              <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 8 }}>
                {rows.map((r) => (
                  <MobileCard key={r[0]} r={r} name={names.get(r[0]) ?? ""} open={r[0] === sp.get("sec")} idx={idx} week={week} ipo={isNewIpo(ipo, r[0], week)}
                              toggle={() => set({ sec: r[0] === sp.get("sec") ? "" : r[0] })} />
                ))}
              </ol>
            </section>
          </div>
        </>
      )}

      <Note>{f.L("SPK bağlantısı olmayan hisse masum ya da suçlu anlamına gelmez. Liste yalnızca o haftaya kadar bilinen veriyle, o yıl öncesinde eğitilmiş modelle üretildi.",
                  "A stock without an SPK link is neither innocent nor guilty. Each list uses only data known up to that week and a model trained on earlier years.")}</Note>
    </Page>
  );
}

function Row({ r, name, on, cut, thr, pick, ipo }: { r: ListRow; name: string; on: boolean; cut: boolean; thr: Record<string, number>; pick: () => void; ipo: boolean }) {
  const f = useT();
  return (
    <>
      {cut && (
        <tr><td colSpan={5} style={{ padding: 0, borderBottom: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 12px", color: "var(--red-ink)", fontSize: 12, fontWeight: 600 }}>
            <Warn size={14} />{f.L("İlk 20 eşiği", "Top-20 threshold")}<span style={{ flex: 1, borderTop: "2px dashed var(--red)" }} />
          </div>
        </td></tr>
      )}
      <tr className={on ? "sel" : ""}>
        <td style={{ fontWeight: 600 }} className="muted">{r[1]}</td>
        <td><button type="button" className="rowbtn" onClick={pick} aria-pressed={on} aria-label={f.L(`${r[0]} önizlemesini aç, sıra ${r[1]}`, `Open ${r[0]} preview, rank ${r[1]}`)}>
          <strong style={{ fontSize: 14, fontWeight: 700 }}>{r[0]}</strong><span style={{ fontSize: 12 }} className="muted">{name}</span>
          {ipo && <IpoBadge />}
        </button></td>
        <td><div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span className="bar" style={{ flex: 1 }}><span style={{ width: `${r[2] * 100}%` }} /></span>
          <span style={{ width: 34, textAlign: "right", fontWeight: 600 }}>{f.num(r[2] * 100, 1)}</span>
        </div></td>
        <td><div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}><ReasonChips vals={r[3]} thr={thr} /></div></td>
        <td><SpkBadge link={r[4]} days={r[5]} /></td>
      </tr>
    </>
  );
}

function Preview({ idx, row, name, week, n }: { idx: Index; row: ListRow; name: string; week: string; n: number }) {
  const f = useT();
  const st = useStock(row[0]);
  return (
    <aside className="card tm-preview" aria-labelledby="pv-h" style={{ flex: "1 1 380px", minWidth: 300, padding: 20, display: "flex", flexDirection: "column", gap: 18 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <p className="eyebrow">{f.L("Önizleme", "Preview")}</p>
          <h2 id="pv-h" style={{ fontSize: 24, fontWeight: 700, letterSpacing: "-.01em" }}>{row[0]}</h2>
          <p style={{ fontSize: 13 }} className="muted">{name}</p>
        </div>
        <span className="badge b-teal">{f.L("Sıra", "Rank")} {row[1]} / {n}</span>
      </div>
      {row[4] && <SpkBadge link={row[4]} days={row[5]} />}
      <figure style={{ margin: 0, display: "flex", flexDirection: "column", gap: 8 }}>
        <figcaption style={{ fontSize: 12 }} className="muted">{f.L("Fiyat · seçili haftanın 5 ay öncesi ve 6 hafta sonrası", "Price · 5 months before and 6 weeks after the selected week")}</figcaption>
        {st.data ? (
          <MiniPrice data={st.data} from={addDays(week, -150)} to={addDays(week, 42)} mark={week} markLabel={f.L("Seçili hafta", "Selected week")}
                     ariaLabel={f.L(`${row[0]} fiyat grafiği, seçili hafta kırmızı çizgiyle`, `${row[0]} price chart, selected week marked in red`)} />
        ) : <Loading error={st.error} />}
        <div className="legend" style={{ fontSize: 11 }}>
          <span><span className="sw-band" />{f.L("SPK'nın belirttiği dönem", "SPK-stated period")}</span>
          <span><span className="sw-line" />{f.L("Seçili hafta", "Selected week")}</span>
        </div>
      </figure>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <h3 style={{ fontSize: 15, fontWeight: 600 }}>{f.L("Neden şüpheli?", "Why suspicious?")}</h3>
        <WhyPanel vals={row[3]} thr={idx.rules} compact />
        <ShapPanel shap={row[6]} feats={idx.shapFeats} compact />
      </div>
      <Link to={`/hisse/${row[0]}?hafta=${week}`} className="btn primary" style={{ alignSelf: "stretch" }}>{f.L("Hisse detayına git", "Open stock detail")}<Arrow /></Link>
    </aside>
  );
}

/** Halka arzın ilk 60 işlem günü: PU modeli bu dönemde boş alarm eğiliminde (MEL-92). */
function IpoBadge() {
  const f = useT();
  return (
    <span className="badge b-gray" style={{ alignSelf: "flex-start" }}
          title={f.L("Halka arzın ilk 60 işlem günü. Bu dönemde fiyat ve hacim doğal olarak oynak; listeye giren yeni halka arzlar geçmişte çoğunlukla boş alarm oldu.",
                     "First 60 trading days after the IPO. Price and volume are naturally volatile; new IPOs on the list were mostly false alarms in the past.")}>
      {f.L("Yeni halka arz", "New IPO")}
    </span>
  );
}

function MobileCard({ r, name, open, idx, week, toggle, ipo }: { r: ListRow; name: string; open: boolean; idx: Index; week: string; toggle: () => void; ipo: boolean }) {
  const f = useT();
  const st = useStock(open ? r[0] : null);
  return (
    <li className={`card${open ? " sel-card" : ""}`}>
      <button type="button" className="rowcard" onClick={toggle} aria-expanded={open}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, width: "100%" }}>
          <span style={{ width: 22, fontSize: 14, fontWeight: 600 }} className="muted">{r[1]}</span>
          <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
            <strong style={{ fontSize: 15 }}>{r[0]}{ipo && <> <IpoBadge /></>}</strong>
            <span style={{ fontSize: 12, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }} className="muted">{name}</span>
          </div>
          <SpkBadge link={r[4]} days={r[5]} short />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, width: "100%", paddingLeft: 32 }}>
          <span className="bar" style={{ flex: 1, height: 6 }}><span style={{ width: `${r[2] * 100}%` }} /></span>
          <span style={{ fontSize: 13, fontWeight: 600, width: 34, textAlign: "right" }}>{f.num(r[2] * 100, 1)}</span>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4, paddingLeft: 32 }}><ReasonChips vals={r[3]} thr={idx.rules} max={2} /></div>
      </button>
      {open && (
        <div style={{ padding: "0 14px 14px", display: "flex", flexDirection: "column", gap: 12, borderTop: "1px solid var(--line)" }}>
          {r[4] && <div style={{ paddingTop: 12 }}><SpkBadge link={r[4]} days={r[5]} /></div>}
          {st.data ? <MiniPrice data={st.data} from={addDays(week, -150)} to={addDays(week, 42)} mark={week} w={340} h={120}
                                ariaLabel={f.L(`${r[0]} fiyat grafiği`, `${r[0]} price chart`)} /> : <Loading error={st.error} />}
          <h3 style={{ fontSize: 14, fontWeight: 600 }}>{f.L("Neden şüpheli?", "Why suspicious?")}</h3>
          <WhyPanel vals={r[3]} thr={idx.rules} compact />
          <ShapPanel shap={r[6]} feats={idx.shapFeats} compact />
          <Link to={`/hisse/${r[0]}?hafta=${week}`} className="btn primary">{f.L("Hisse detayına git", "Open stock detail")}</Link>
        </div>
      )}
    </li>
  );
}
