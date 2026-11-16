import { useState } from "react";
import { Link } from "react-router-dom";
import { addDays, getResult, useIndex, useStock, type CaseStudy } from "../data";
import { useT } from "../i18n";
import { Page } from "../components/Layout";
import { Arrow, Check, Dash } from "../components/Icons";
import { ChartLegend, Loading } from "../components/ui";
import { MiniPrice } from "../components/charts";
import { CASE_TEXT } from "./caseText";

export default function Cases() {
  const f = useT();
  const { data: idx, error } = useIndex();
  const [flt, setFlt] = useState<"all" | "c" | "m">("all");
  if (!idx) return <Page><Loading error={error} /></Page>;
  const r = getResult(idx.results, "4_kural_pu")!;
  const nC = idx.cases.filter((c) => c.caught).length, nM = idx.cases.length - nC;
  const shown = idx.cases.filter((c) => flt === "all" || (flt === "c" ? c.caught : !c.caught));
  return (
    <Page>
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "flex-end", gap: 20 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 760 }}>
          <h1 className="h1">{f.L("Vaka çalışmaları", "Case studies")}</h1>
          <p className="lead">{f.L("SPK'nın karara bağladığı vakalardan seçilmiş örnekler. Sistemin neyi yakaladığını ve neyi kaçırdığını aynı açıklıkla gösteriyoruz.",
                                   "Selected cases that SPK ruled on. We show what the system caught and what it missed with the same openness.")}</p>
        </div>
        <div className="seg" role="group" aria-label={f.L("Vaka filtresi", "Case filter")}>
          {([["all", f.L(`Tümü · ${idx.cases.length}`, `All · ${idx.cases.length}`)], ["c", f.L(`Yakalanan · ${nC}`, `Caught · ${nC}`)], ["m", f.L(`Kaçırılan · ${nM}`, `Missed · ${nM}`)]] as const).map(([k, l]) => (
            <button key={k} type="button" className={flt === k ? "on" : ""} aria-pressed={flt === k} onClick={() => setFlt(k)} style={{ padding: "0 14px" }}>{l}</button>
          ))}
        </div>
      </div>
      <p className="notice">
        {f.L("Tüm test vakalarında yakalama oranı ", "Across all test cases the catch rate is ")}<strong style={{ color: "var(--text)" }}>{f.pct(r.rec)}</strong>{" "}
        <span className="faint">({f.L("rastgele", "random")} {f.pct(r.rnd)})</span>.{" "}
        {f.L(`Buradaki ${idx.cases.length} vaka, iki sonucu da göstermek için seçildi; oranı temsil etmez. Seçim kuralı: kısa süren (rastgele yakalanması zor) vakalar.`,
             `These ${idx.cases.length} cases were picked to show both outcomes; they do not represent the rate. Selection rule: short cases that are hard to hit by chance.`)}
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(min(380px, 100%), 1fr))", gap: 20 }}>
        {shown.map((c) => <CaseCard key={c.id} c={c} />)}
      </div>
      <ChartLegend decision={false} />
    </Page>
  );
}

function CaseCard({ c }: { c: CaseStudy }) {
  const f = useT();
  const st = useStock(c.ticker);
  const tx = CASE_TEXT[c.id];
  return (
    <Link to={`/vakalar/${c.id}`} className="card casecard" aria-label={`${c.ticker}: ${c.caught ? f.L("yakalandı", "caught") : f.L("kaçırıldı", "missed")}. ${f.L(...tx.card)}`}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <h2 style={{ fontSize: 24, fontWeight: 700, letterSpacing: "-.01em" }}>{c.ticker}</h2>
          <p style={{ fontSize: 13 }} className="muted">{f.date(c.start)} – {f.date(c.end)} · {f.L(...tx.title)}</p>
        </div>
        {c.caught ? <span className="badge b-green"><Check size={12} />{f.L("Yakalandı", "Caught")}</span>
                  : <span className="badge b-gray"><Dash size={12} />{f.L("Kaçırıldı", "Missed")}</span>}
      </div>
      {st.data ? <MiniPrice data={st.data} from={addDays(c.start, -90)} to={addDays(c.end, 120)} mark={c.firstAlert ?? undefined} w={340} h={96}
                            ariaLabel={f.L(`${c.ticker} fiyat grafiği; turuncu bant SPK dönemi${c.caught ? ", kırmızı çizgi ilk alarm" : ", alarm yok"}`, `${c.ticker} price; orange band = SPK period${c.caught ? ", red line = first alarm" : ", no alarm"}`)} />
               : <div style={{ height: 96 }} />}
      <p style={{ fontSize: 14, lineHeight: 1.5 }}>{f.L(...tx.card)}</p>
      <span style={{ fontSize: 13, fontWeight: 600, color: "var(--teal-ink)", display: "inline-flex", alignItems: "center", gap: 6 }}>{f.L("Vakayı aç", "Open case")}<Arrow size={14} /></span>
    </Link>
  );
}
