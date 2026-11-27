import { useSearchParams } from "react-router-dom";
import { useT } from "../i18n";
import { Page } from "../components/Layout";
import { Check, Dash, Half, Warn, X } from "../components/Icons";
import { EXPS, GROUPS, type Exp, type Group, type Verdict } from "./experimentData";

const VERDICTS: { id: Verdict; name: [string, string]; cls: string; icon: React.ReactNode }[] = [
  { id: "ok", name: ["İşe yaradı", "Worked"], cls: "b-green", icon: <Check size={12} /> },
  { id: "part", name: ["Kısmen", "Partly"], cls: "b-amber", icon: <Half size={12} /> },
  { id: "no", name: ["Katkı yok", "No gain"], cls: "b-gray", icon: <X size={12} /> },
  { id: "harm", name: ["Zararlı", "Harmful"], cls: "b-red", icon: <Warn size={12} /> },
  { id: "diag", name: ["Tanı / taban", "Diagnostic / baseline"], cls: "b-teal", icon: <Dash size={12} /> },
];
const V = Object.fromEntries(VERDICTS.map((v) => [v.id, v]));

export default function Experiments() {
  const f = useT();
  const [sp, setSp] = useSearchParams();
  const g = (sp.get("konu") ?? "") as Group | "";
  const v = (sp.get("sonuc") ?? "") as Verdict | "";
  const set = (k: string, val: string) => {
    const n = new URLSearchParams(sp);
    if (val) n.set(k, val); else n.delete(k);
    setSp(n, { replace: true });
  };
  const shown = EXPS.filter((e) => (!g || e.group === g) && (!v || e.verdict === v));
  const count = (id: Verdict) => EXPS.filter((e) => e.verdict === id).length;

  return (
    <Page width="narrow" gap={28}>
      <section style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 760 }}>
        <h1 className="h1">{f.L("Denemeler", "Experiments")}</h1>
        <p style={{ fontSize: 16, lineHeight: 1.6 }} className="muted">
          {f.L(`Projede denenen ${EXPS.length} fikrin tamamı, işe yarasın ya da yaramasın. Her kartta: neden denendi, nasıl ölçüldü, ne çıktı ve ne karar verildi. İşe yaramayan denemelerin kodu depoya alınmadı; sayılar belgelerde kayıtlı.`,
               `All ${EXPS.length} ideas tried in the project, whether they worked or not. Each card shows why it was tried, how it was measured, what came out and what was decided. Code for failed experiments was not kept; the numbers are recorded in the documents.`)}
        </p>
      </section>

      <section className="card" aria-labelledby="how-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14 }}>
        <h2 id="how-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("Her deneme nasıl ölçüldü?", "How was each experiment measured?")}</h2>
        <ul style={{ margin: 0, paddingLeft: 20, display: "flex", flexDirection: "column", gap: 8, fontSize: 14, lineHeight: 1.55 }} className="muted">
          <li>{f.L("Karşılaştırma hep ana modelle: Kural + PU (AUC 0,849; vakaların %67,2'si haftalık ilk 20'de en az bir kez, rastgele liste %23,2).",
                   "Always compared with the main model: Rules + PU (AUC 0.849; 67.2% of cases appear in a weekly top 20 at least once, random list 23.2%).")}</li>
          <li>{f.L("Dürüst protokol: her yıl, yalnız o yıldan önceki veriyle ve o güne kadar açıklanmış SPK kararlarıyla eğitilen modelle puanlanır. Gelecek bilgisi kullanılmaz.",
                   "Honest protocol: each year is scored by a model trained only on earlier data and SPK decisions announced by then. No future information.")}</li>
          <li>{f.L("Aynı 123 vaka (2017–2026) üzerinde eşli bootstrap; fark yalnız %95 güven aralığı sıfırı içermiyorsa \"anlamlı\".",
                   "Paired bootstrap on the same 123 cases (2017–2026); a difference is \"significant\" only if its 95% interval excludes zero.")}</li>
          <li>{f.L("Her tasarım ve karar kuralı, sonuç görülmeden önce görev kaydına yazıldı. Kural: yalnız ana modelde anlamlı kazanç varsa eklenir; sınırdaki durumlar birlikte karar verildi.",
                   "Each design and decision rule was written down before seeing results. Rule: adopt only on a significant gain for the main model; borderline cases were decided together.")}</li>
        </ul>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {VERDICTS.map((x) => (
            <span key={x.id} className={`badge ${x.cls}`}>{x.icon}{f.L(...x.name)}: {count(x.id)}</span>
          ))}
        </div>
      </section>

      <section aria-label={f.L("Filtreler", "Filters")} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <div className="seg" role="group" aria-label={f.L("Konu", "Topic")}>
          <button type="button" className={!g ? "on" : ""} aria-pressed={!g} onClick={() => set("konu", "")}>{f.L("Tüm konular", "All topics")}</button>
          {GROUPS.map((x) => (
            <button key={x.id} type="button" className={g === x.id ? "on" : ""} aria-pressed={g === x.id} onClick={() => set("konu", x.id)}>{f.L(...x.name)}</button>
          ))}
        </div>
        <div className="seg" role="group" aria-label={f.L("Sonuç", "Outcome")}>
          <button type="button" className={!v ? "on" : ""} aria-pressed={!v} onClick={() => set("sonuc", "")}>{f.L("Tüm sonuçlar", "All outcomes")}</button>
          {VERDICTS.map((x) => (
            <button key={x.id} type="button" className={v === x.id ? "on" : ""} aria-pressed={v === x.id} onClick={() => set("sonuc", x.id)}>{f.L(...x.name)}</button>
          ))}
        </div>
        <p style={{ fontSize: 13 }} className="faint" aria-live="polite">{f.L(`${shown.length} deneme gösteriliyor`, `Showing ${shown.length} experiments`)}</p>
      </section>

      {GROUPS.filter((x) => shown.some((e) => e.group === x.id)).map((grp) => (
        <section key={grp.id} aria-labelledby={`g-${grp.id}`} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <h2 id={`g-${grp.id}`} style={{ fontSize: 22, fontWeight: 600, letterSpacing: "-.01em" }}>{f.L(...grp.name)}</h2>
            <p style={{ fontSize: 14 }} className="muted">{f.L(...grp.desc)}</p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {shown.filter((e) => e.group === grp.id).sort((a, b) => (a.date < b.date ? -1 : 1)).map((e) => <Card key={e.id} e={e} />)}
          </div>
        </section>
      ))}
    </Page>
  );
}

function Card({ e }: { e: Exp }) {
  const f = useT();
  const vd = V[e.verdict];
  const row = (h: string, t: string) => (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr)", gap: 2 }}>
      <dt style={{ fontSize: 12, fontWeight: 600 }} className="faint">{h}</dt>
      <dd style={{ margin: 0, fontSize: 14, lineHeight: 1.55 }}>{t}</dd>
    </div>
  );
  return (
    <details className="card exp">
      <summary>
        <span className={`badge ${vd.cls}`}>{vd.icon}{f.L(...vd.name)}</span>
        <span className="exp-title">{f.L(...e.title)}</span>
        <span style={{ fontSize: 12, whiteSpace: "nowrap" }} className="faint">{f.date(e.date)}</span>
      </summary>
      <dl style={{ margin: 0, padding: "0 18px 18px", display: "flex", flexDirection: "column", gap: 12 }}>
        {row(f.L("Neden denendi?", "Why?"), f.L(...e.why))}
        {row(f.L("Nasıl ölçüldü?", "How?"), f.L(...e.how))}
        {row(f.L("Sonuç", "Result"), f.L(...e.result))}
        {row(f.L("Karar", "Decision"), f.L(...e.decision))}
      </dl>
    </details>
  );
}
