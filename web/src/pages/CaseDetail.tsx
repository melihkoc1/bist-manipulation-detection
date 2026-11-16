import { Link, Navigate, useParams } from "react-router-dom";
import { addDays, dayDiff, useIndex, useStock } from "../data";
import { useT } from "../i18n";
import { Page } from "../components/Layout";
import { Arrow, Back, Bulb, Check, Dash, Eye } from "../components/Icons";
import { ChartLegend, firedRules, Loading, RULE_TEXT } from "../components/ui";
import { StockChart } from "../components/charts";
import { CASE_TEXT } from "./caseText";

export default function CaseDetail() {
  const f = useT();
  const { id = "" } = useParams();
  const { data: idx, error } = useIndex();
  const c = idx?.cases.find((x) => x.id === id);
  const st = useStock(c?.ticker ?? null);
  if (!idx) return <Page width="narrow"><Loading error={error} /></Page>;
  if (!c) return <Navigate to="/vakalar" replace />;
  const tx = CASE_TEXT[c.id];
  const i = idx.cases.indexOf(c);
  const next = idx.cases[(i + 1) % idx.cases.length];
  const rise = c.peakPx / c.startPx - 1;
  const drop = c.minAfter != null ? 1 - c.minAfter / c.peakPx : null;
  const from = addDays(c.start, -120), to = addDays(c.firstSpk && c.firstSpk < addDays(c.end, 400) ? c.firstSpk : c.end, 150);

  type M = { label: string; date: string; color: string };
  const ms: M[] = [{ label: f.L("Manipülasyon başladı", "Manipulation began"), date: c.start, color: "#f4a261" }];
  if (c.firstAlert) ms.push({ label: f.L(`İlk alarm (${c.leadDays}. gün)`, `First alarm (day ${c.leadDays})`), date: c.firstAlert, color: "#e63946" });
  if (c.peak) ms.push({ label: f.L("Fiyat zirvesi", "Price peak"), date: c.peak, color: "var(--text)" });
  if (c.firstSpk) ms.push({ label: f.L("SPK'nın ilk kararı", "SPK's first decision"), date: c.firstSpk, color: "var(--muted)" });
  if (c.firstSanction && c.firstSanction !== c.firstSpk) ms.push({ label: f.L("SPK cezası", "SPK sanction"), date: c.firstSanction, color: "var(--muted)" });
  ms.sort((a, b) => (a.date < b.date ? -1 : 1));
  const gap = (a: string, b: string) => {
    const d = dayDiff(b, a);
    return d >= 60 ? f.L(`+${Math.round(d / 30.4)} ay`, `+${Math.round(d / 30.4)} mo`) : f.L(`+${d} gün`, `+${d} days`);
  };

  const alarmRow = st.data && c.firstAlert ? st.data.ranks.find((r) => r[0] === c.firstAlert) : undefined;
  const fired = alarmRow ? firedRules(alarmRow.slice(3) as (number | null)[], idx.rules) : [];
  const topWeeks = st.data ? st.data.ranks.filter((r) => r[0] >= c.start && addDays(r[0], -6) <= c.end && r[1] <= 20).length : 0;

  return (
    <Page width="narrow">
      <nav aria-label={f.L("Konum", "Breadcrumb")} style={{ fontSize: 13, display: "flex", gap: 8, alignItems: "center" }} className="muted">
        <Link to="/vakalar">{f.L("Vaka çalışmaları", "Case studies")}</Link><span aria-hidden="true">/</span><span aria-current="page">{c.ticker} {c.start.slice(0, 4)}</span>
      </nav>

      <section style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 820 }}>
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 12 }}>
          <h1 style={{ fontSize: "clamp(34px, 5vw, 44px)", fontWeight: 700, letterSpacing: "-.025em", lineHeight: 1.05 }}>{c.ticker} · {c.start.slice(0, 4)}</h1>
          {c.caught ? <span className="badge b-green" style={{ fontSize: 13, padding: "5px 11px" }}><Check size={13} />{f.L("Yakalandı", "Caught")}</span>
                    : <span className="badge b-gray" style={{ fontSize: 13, padding: "5px 11px" }}><Dash size={13} />{f.L("Kaçırıldı", "Missed")}</span>}
        </div>
        <p style={{ fontSize: 20, lineHeight: 1.45 }}>{f.L(...tx.title)}. {f.L(...tx.card)}</p>
        <p style={{ fontSize: 15, lineHeight: 1.6 }} className="muted">
          {idx.stocks.find((s) => s.t === c.ticker)?.name.replace(/\.$/, "")}. {f.L(`SPK'nın belirttiği manipülasyon dönemi ${f.date(c.start)} – ${f.date(c.end)}. Dönemde fiyat ${f.pct(rise)} arttı`, `Manipulation period stated by SPK: ${f.date(c.start)} – ${f.date(c.end)}. The price rose ${f.pct(rise)}`)}
          {drop != null && drop > 0.2 ? f.L(`; sonraki 6 ayda zirveden ${f.pct(drop)} düştü.`, `, then fell ${f.pct(drop)} from the peak within 6 months.`) : "."}{" "}
          {f.L(`Rastgele bir listenin bu vakayı yakalama olasılığı ${f.pct(c.pRandom)}. Aşağıdaki sıralar yalnızca o tarihte erişilebilen veriyle üretildi.`,
               `A random list would catch this case with probability ${f.pct(c.pRandom)}. The ranks below use only data available at the time.`)}
        </p>
      </section>

      <section className="card" aria-labelledby="ms-h" style={{ padding: "28px 24px 24px" }}>
        <h2 id="ms-h" className="eyebrow" style={{ marginBottom: 24 }}>{f.L("Olayların sırası", "Sequence of events")}</h2>
        <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "24px 0" }}>
          {ms.map((m, j) => (
            <li key={m.label} style={{ display: "flex", flexDirection: "column", gap: 10, paddingRight: 12 }}>
              <div style={{ display: "flex", alignItems: "center" }}>
                <span style={{ width: 18, height: 18, borderRadius: "50%", flex: "none", background: m.color, boxShadow: "0 0 0 4px var(--surface)" }} />
                <span style={{ flex: 1, height: 2, background: "var(--line-2)", marginLeft: 4 }} />
                {j < ms.length - 1 && <span style={{ fontSize: 12, fontWeight: 600, padding: "2px 8px", borderRadius: 999, background: "var(--surface-2)", whiteSpace: "nowrap", margin: "0 4px" }} className="muted">{gap(m.date, ms[j + 1].date)}</span>}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <strong style={{ fontSize: 15, fontWeight: 600 }}>{m.label}</strong>
                <span style={{ fontSize: 13 }} className="muted">{f.date(m.date)}{j > 0 ? f.L(` · gün ${dayDiff(m.date, c.start)}`, ` · day ${dayDiff(m.date, c.start)}`) : f.L(" · gün 0", " · day 0")}</span>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="card" aria-labelledby="ch-h" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
          <h2 id="ch-h" style={{ fontSize: 16, fontWeight: 600 }}>{f.L("Fiyat, hacim ve haftalık sıra", "Price, volume and weekly rank")} · {f.date(from)} – {f.date(to)}</h2>
          <ChartLegend threshold alarmLabel={f.L("İlk alarm", "First alarm")} />
        </div>
        {st.data ? (
          <StockChart data={st.data} from={from} to={to}
                      alarms={c.firstAlert ? [{ date: c.firstAlert, label: f.L(`İlk alarm · ${c.leadDays}. gün`, `First alarm · day ${c.leadDays}`) }] : []}
                      peak={c.peak ? { date: c.peak, label: f.L("Zirve", "Peak") } : undefined}
                      ariaLabel={f.L(`${c.ticker}: SPK dönemi turuncu bantla; fiyat dönemde ${f.pct(rise)} arttı.${c.firstAlert ? ` Sistem ${f.date(c.firstAlert)} haftasında ilk alarmı verdi.` : " Sistem alarm vermedi."}`,
                                     `${c.ticker}: SPK period as orange band; the price rose ${f.pct(rise)}.${c.firstAlert ? ` First alarm in the week of ${f.date(c.firstAlert)}.` : " No alarm."}`)} />
        ) : <Loading error={st.error} />}
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(400px, 100%), 1fr))", gap: 20 }}>
        <section className="card" aria-labelledby="saw-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ width: 36, height: 36, borderRadius: 9, background: "var(--teal-soft)", color: "var(--teal-ink)", display: "flex", alignItems: "center", justifyContent: "center" }}><Eye size={18} /></span>
            <h2 id="saw-h" style={{ fontSize: 18, fontWeight: 600 }}>{c.caught ? f.L("Sistem ne gördü?", "What did the system see?") : f.L("Neden kaçtı?", "Why was it missed?")}</h2>
          </div>
          <ul style={{ margin: 0, paddingLeft: 20, display: "flex", flexDirection: "column", gap: 10, fontSize: 15, lineHeight: 1.55 }}>
            {c.caught && alarmRow && <li>{f.L(`İlk alarm haftasında (${f.date(c.firstAlert)}) sıra ${alarmRow[1]} / ${alarmRow[2]}.`, `In the first-alarm week (${f.date(c.firstAlert)}) it ranked ${alarmRow[1]} of ${alarmRow[2]}.`)}</li>}
            {fired.map((x) => <li key={x.k}>{RULE_TEXT[x.k].sentence(x.v as number, f)}</li>)}
            {c.caught && <li>{f.L(`Dönem boyunca ${topWeeks} hafta ilk 20'de kaldı.`, `It stayed in the top 20 for ${topWeeks} weeks during the period.`)}</li>}
            {!c.caught && <li>{f.L(`En iyi haftalık sırası ${c.bestRank}; hiç ilk 20'ye girmedi.`, `Its best weekly rank was ${c.bestRank}; it never entered the top 20.`)}</li>}
            {tx.saw.map((s, j) => <li key={j}>{f.L(...s)}</li>)}
          </ul>
        </section>
        <section className="card" aria-labelledby="ders-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14, background: "var(--surface-2)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ width: 36, height: 36, borderRadius: 9, background: "var(--surface)", border: "1px solid var(--line)", display: "flex", alignItems: "center", justifyContent: "center" }}><Bulb size={18} /></span>
            <h2 id="ders-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("Ders", "Lesson")}</h2>
          </div>
          <p style={{ fontSize: 15, lineHeight: 1.6 }}>{f.L(...tx.lesson)}</p>
          {tx.caution && <p style={{ fontSize: 14, lineHeight: 1.55 }}><strong>{f.L("Dikkat: ", "Note: ")}</strong>{f.L(...tx.caution)}</p>}
          <p style={{ fontSize: 13 }} className="muted">{f.L("Alarm, SPK kararının yerine geçmez; yalnızca hangi hisseye önce bakılacağını önerir.", "An alarm does not replace SPK's decision; it only suggests which stock to look at first.")}</p>
        </section>
      </div>

      <nav aria-label={f.L("Diğer vakalar", "Other cases")} style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 12, paddingTop: 8, borderTop: "1px solid var(--line)" }}>
        <Link to="/vakalar" className="btn"><Back />{f.L("Tüm vakalar", "All cases")}</Link>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <Link to={`/hisse/${c.ticker}`} className="btn">{f.L("Hisse detayı", "Stock detail")}</Link>
          <Link to={`/vakalar/${next.id}`} className="btn">{f.L(`Sonraki vaka: ${next.ticker}`, `Next case: ${next.ticker}`)}<Arrow /></Link>
        </div>
      </nav>
    </Page>
  );
}
