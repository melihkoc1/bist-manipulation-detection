import { useT } from "../i18n";
import { GITHUB, Page } from "../components/Layout";
import { CalClock, Clock, Github } from "../components/Icons";

/** İleriye dönük canlı test henüz başlamadı (Linear MEL-17). Kayıt dosyası gelince bu sayfa doldurulacak. */
export default function LiveTest() {
  const f = useT();
  const weeks = 0, target = 30;
  const card = { padding: 22, display: "flex", flexDirection: "column", gap: 10 } as const;
  const big = { fontSize: 48, fontWeight: 600, letterSpacing: "-.02em", lineHeight: 1 } as const;
  return (
    <Page width="narrow">
      <section style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 800 }}>
        <span className="badge b-amber" style={{ alignSelf: "flex-start" }}><Clock size={12} />{f.L("Yakında · ileriye dönük test", "Coming soon · prospective test")}</span>
        <h1 className="h1">{f.L("Canlı test", "Live test")}</h1>
        <p style={{ fontSize: 18, lineHeight: 1.55 }}>{f.L("Plan: model dondurulacak, her haftanın listesi kaydedilecek ve Haziran 2027'de o tarihe kadar açıklanan SPK kararlarıyla karşılaştırılacak.",
                                                           "Plan: freeze the model, record every week's list, and compare them in June 2027 with the SPK decisions announced by then.")}</p>
        <p style={{ fontSize: 15, lineHeight: 1.6 }} className="muted">{f.L("Geriye dönük testler ne kadar dikkatli kurulsa da geleceği görmüş olma riski taşır. Burada sonuç henüz kimse tarafından bilinmeyecek: listeler kaydedildiği an zaman damgasıyla sabitlenecek ve sonradan değiştirilemeyecek.",
                                                                              "However carefully a backtest is built, it risks having seen the future. Here nobody will know the outcome yet: each list will be fixed with a timestamp when recorded and cannot be changed later.")}</p>
      </section>

      <section className="card" aria-labelledby="tl-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 18 }}>
        <h2 id="tl-h" className="eyebrow">{f.L("Takvim", "Timeline")}</h2>
        <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
          {[
            [f.L("Model dondurulur", "Model frozen"), f.L("Kasım 2026 · kod ve ayarlar sabitlenir", "Nov 2026 · code and settings fixed"), "3px dashed var(--line-2)"],
            [f.L("Haftalık kayıt", "Weekly record"), f.L("Her hafta sonu · ilk 20 liste zaman damgası ve özetiyle (hash) kaydedilir", "Every weekend · the top-20 list is saved with a timestamp and hash"), "3px dashed var(--line-2)"],
            [f.L("SPK karşılaştırması", "SPK comparison"), f.L("Haziran 2027 · listeler yeni SPK kararlarıyla eşleştirilir", "June 2027 · lists matched with new SPK decisions"), "3px dashed var(--line-2)"],
          ].map(([h, s, b]) => (
            <li key={h} style={{ display: "flex", flexDirection: "column", gap: 6, paddingTop: 14, borderTop: b }}>
              <strong style={{ fontSize: 15 }}>{h}</strong><span style={{ fontSize: 13 }} className="muted">{s}</span>
            </li>
          ))}
        </ol>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }} className="muted"><span>{f.L("İlerleme", "Progress")}</span><span>{weeks} / {target} {f.L("hafta", "weeks")}</span></div>
          <div role="progressbar" aria-label={f.L("Kaydedilen hafta", "Weeks recorded")} aria-valuemin={0} aria-valuemax={target} aria-valuenow={weeks} className="bar">
            <span style={{ width: `${(weeks / target) * 100}%` }} />
          </div>
        </div>
      </section>

      <section aria-label={f.L("Sayaçlar", "Counters")} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
        <div className="card" style={card}><p style={{ fontSize: 14, fontWeight: 500 }} className="muted">{f.L("Kaydedilen hafta", "Weeks recorded")}</p><strong style={big}>{weeks}</strong><p style={{ fontSize: 13 }} className="faint">{f.L("hedef: Haziran 2027'ye kadar ~30 hafta", "target: ~30 weeks by June 2027")}</p></div>
        <div className="card" style={card}><p style={{ fontSize: 14, fontWeight: 500 }} className="muted">{f.L("Listeye giren farklı hisse", "Distinct stocks listed")}</p><strong style={big}>0</strong><p style={{ fontSize: 13 }} className="faint">{f.L("her hafta ilk 20", "top 20 each week")}</p></div>
        <div className="card" style={card}><p style={{ fontSize: 14, fontWeight: 500 }} className="muted">{f.L("Sonradan SPK kararı gelen", "Later got an SPK decision")}</p><strong style={{ ...big, color: "var(--faint)" }}>—</strong><p style={{ fontSize: 13 }} className="faint">{f.L("Haziran 2027'de hesaplanacak · rastgele beklenti de o zaman", "computed in June 2027, with the random expectation")}</p></div>
      </section>

      <section className="card" aria-labelledby="log-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <h2 id="log-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("Haftalık kayıt", "Weekly log")}</h2>
          <span style={{ fontSize: 13 }} className="muted">{f.L("Kural + PU · ilk 20", "Rules + PU · top 20")}</span>
        </div>
        <div style={{ padding: "56px 24px", border: "1px dashed var(--line-2)", borderRadius: 12, display: "flex", flexDirection: "column", alignItems: "center", gap: 14, textAlign: "center" }}>
          <span style={{ width: 56, height: 56, borderRadius: 14, background: "var(--surface-2)", color: "var(--muted)", display: "flex", alignItems: "center", justifyContent: "center" }}><CalClock size={26} /></span>
          <h3 style={{ fontSize: 18, fontWeight: 600 }}>{f.L("İlk hafta kaydı bekleniyor", "Waiting for the first weekly record")}</h3>
          <p style={{ fontSize: 14, lineHeight: 1.55, maxWidth: 460 }} className="muted">{f.L("Canlı test henüz başlamadı. Model dondurulup ilk liste kaydedildiğinde kayıtlar burada en yenisi üstte görünecek.",
                                                                                                  "The live test has not started yet. Once the model is frozen and the first list recorded, entries will appear here, newest first.")}</p>
          <a href={GITHUB} target="_blank" rel="noreferrer" className="btn sm"><Github />{f.L("Kodu incele", "View the code")}</a>
        </div>
      </section>
    </Page>
  );
}
