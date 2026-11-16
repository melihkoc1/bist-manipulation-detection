import { useT } from "../i18n";
import { GITHUB, Page } from "../components/Layout";
import { Doc, Github, Person } from "../components/Icons";

export default function About() {
  const f = useT();
  return (
    <Page width="narrower">
      <section style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 760 }}>
        <h1 className="h1">{f.L("Hakkında", "About")}</h1>
        <p style={{ fontSize: 17, lineHeight: 1.6 }}>{f.L("Bu proje, Borsa İstanbul'da \"pompala ve boşalt\" tipi piyasa dolandırıcılığının SPK kararından önce, yalnızca kamuya açık veriyle fark edilip edilemeyeceğini sınayan bir yazılım mühendisliği bitirme projesidir.",
                                                           "This software engineering graduation project tests whether pump-and-dump manipulation on Borsa Istanbul can be spotted before the regulator acts, using public data only.")}</p>
        <p style={{ fontSize: 15, lineHeight: 1.6 }} className="muted">{f.L("Amaç bir ön eleme aracı kurmak: uzmanın her hafta yüzlerce hisse yerine en şüpheli 20'sine bakmasını sağlamak ve bunun rastgeleden ne kadar iyi olduğunu dürüstçe ölçmek.",
                                                                              "The goal is a triage tool: let an analyst look at the 20 most suspicious stocks each week instead of hundreds, and measure honestly how much better than random that is.")}</p>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(320px, 100%), 1fr))", gap: 20 }}>
        <section className="card" aria-labelledby="au-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 18 }}>
          <h2 id="au-h" className="eyebrow">{f.L("Ekip", "Team")}</h2>
          <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
            <span aria-hidden="true" style={{ width: 56, height: 56, borderRadius: "50%", background: "var(--teal-soft)", color: "var(--teal-ink)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, fontWeight: 700 }}>MK</span>
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}><strong style={{ fontSize: 17 }}>Melih Erdem Koçoğlu</strong><span style={{ fontSize: 14 }} className="muted">{f.L("Yazar · Yazılım Mühendisliği", "Author · Software Engineering")}</span></div>
          </div>
          <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
            <span aria-hidden="true" style={{ width: 56, height: 56, borderRadius: "50%", background: "var(--surface-2)", border: "1px dashed var(--line-2)", color: "var(--faint)", display: "flex", alignItems: "center", justifyContent: "center" }}><Person size={22} /></span>
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}><strong style={{ fontSize: 17 }} className="muted">{f.L("Danışman (eklenecek)", "Advisor (to be added)")}</strong><span style={{ fontSize: 14 }} className="muted">{f.L("Tez danışmanı", "Thesis advisor")}</span></div>
          </div>
        </section>
        <section className="card" aria-labelledby="pr-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 18 }}>
          <h2 id="pr-h" className="eyebrow">{f.L("Proje", "Project")}</h2>
          <dl className="kv">
            <dt>{f.L("Program", "Programme")}</dt><dd>{f.L("Yazılım Mühendisliği Bitirme Projesi", "Software Engineering Graduation Project")}</dd>
            <dt>{f.L("Dönem", "Term")}</dt><dd>2026–2027</dd>
            <dt>{f.L("Değerlendirme", "Evaluation")}</dt><dd>{f.L("2012–2026 SPK vakaları", "2012–2026 SPK cases")}</dd>
            <dt>{f.L("Canlı test", "Live test")}</dt><dd>{f.L("Planlandı · Haziran 2027", "Planned · June 2027")}</dd>
            <dt>{f.L("Lisans", "License")}</dt><dd>MIT</dd>
          </dl>
        </section>
      </div>

      <section className="card" aria-labelledby="ln-h" style={{ padding: 24, display: "flex", flexWrap: "wrap", gap: 20, alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, maxWidth: 560 }}>
          <h2 id="ln-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("Kod ve tez", "Code and thesis")}</h2>
          <p style={{ fontSize: 14, lineHeight: 1.55 }} className="muted">{f.L("Veri hazırlama, modeller ve değerlendirme kodu açık. Tez metni tüm deneyleri, başarısız olanlar dahil, ayrıntılı anlatacak.",
                                                                                 "Data preparation, models and evaluation code are open. The thesis will describe every experiment in detail, including the failed ones.")}</p>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
          <a href={GITHUB} target="_blank" rel="noreferrer" className="btn primary"><Github size={18} />{f.L("GitHub deposu", "GitHub repository")}</a>
          <button type="button" className="btn" disabled title={f.L("Tez tamamlanınca eklenecek", "Added when the thesis is done")}><Doc size={18} />{f.L("Tez PDF (yakında)", "Thesis PDF (soon)")}</button>
        </div>
      </section>

      <section aria-labelledby="st-h" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <h2 id="st-h" className="eyebrow">{f.L("Kullanılan teknolojiler", "Technologies")}</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {["Python", "pandas", "DuckDB", "scikit-learn", "LightGBM", f.L("PU öğrenme", "PU learning"), "pytest", "React", "TypeScript", "Vite"].map((t) => <span key={t} className="pill">{t}</span>)}
        </div>
      </section>
    </Page>
  );
}
