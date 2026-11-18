import { useT } from "../i18n";
import { GITHUB, Page } from "../components/Layout";
import { CalClock, Clock, Github } from "../components/Icons";
import { Fragment, useState } from "react";
import { Link } from "react-router-dom";
import { useIndex, useJson, type RuleVals, type Shap } from "../data";
import { ReasonChips, ShapPanel, WhyPanel } from "../components/ui";

/** İleriye dönük canlı test (Linear MEL-17). Veri: scripts/export_web.py → live.json.
 *  `lists` yalnız yerel dışa aktarımda dolar (hisse adları içerir; web/public/data depoya girmez,
 *  herkese açık bir kopya için `export_web.py --live --no-lists`). */
interface Live {
  frozen: string; dataEnd: string; labelCutoff: string; knownCases: number;
  modelSha: string; codeCommit: string; distinct: number;
  /** [hafta sonu, kayıt zamanı (UTC), gecikmeli, skorlanan hisse, ilk 20 sha256] */
  weeks: [string, string, number, number, string][];
  /** hafta sonu → [hisse, şirket, sıra, yüzdelik, kural göstergeleri, PU SHAP] */
  lists?: Record<string, [string, string, number, number, RuleVals, Shap][]>;
  feats?: string[];
}

function LiveLists({ data }: { data: Live }) {
  const f = useT();
  const { data: idx } = useIndex();
  const weeks = Object.keys(data.lists ?? {}).sort();
  const [week, setWeek] = useState(weeks[weeks.length - 1]);
  const [open, setOpen] = useState<string | null>(null);
  if (!weeks.length || !idx) return null;
  const rows = data.lists![week] ?? [];
  return (
    <section className="card" aria-labelledby="ll-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <span className="badge b-amber" style={{ alignSelf: "flex-start" }}>{f.L("Yalnız bu bilgisayarda", "Only on this computer")}</span>
        <h2 id="ll-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("Kaydedilen listeler", "Recorded lists")}</h2>
        <p style={{ fontSize: 13, lineHeight: 1.55 }} className="muted">{f.L(
          "Donmuş modelin o hafta en üste koyduğu 20 hisse. Bu bölüm yerel veriden oluşur, yayımlanmaz. Listedeki bir hisse manipülasyon kanıtı değildir; olağan dışı fiyat ve hacim hareketi gösterir. Sonuç Haziran 2027'de SPK kararlarıyla ölçülecek.",
          "The 20 stocks the frozen model ranked highest that week. This section is built from local data and is not published. A listed stock is not evidence of manipulation; it shows unusual price and volume behaviour. The outcome will be measured against SPK decisions in June 2027.")}</p>
      </div>
      <div className="seg" role="group" aria-label={f.L("Hafta seç", "Choose week")} style={{ alignSelf: "flex-start", flexWrap: "wrap" }}>
        {weeks.map((w) => <button key={w} type="button" className={w === week ? "on" : ""} aria-pressed={w === week} onClick={() => { setWeek(w); setOpen(null); }}>{w}</button>)}
      </div>
      <div className="tbl-wrap">
        <table className="t">
          <thead><tr><th className="num">{f.L("Sıra", "Rank")}</th><th>{f.L("Hisse", "Stock")}</th><th>{f.L("Öne çıkan", "Highlights")}</th></tr></thead>
          <tbody>
            {rows.map(([t, name, rank, , vals, shap]) => (
              <Fragment key={t}>
                <tr>
                  <td className="num">{rank}</td>
                  <td>
                    <button type="button" className="rowbtn" aria-expanded={open === t} onClick={() => setOpen(open === t ? null : t)}>
                      <strong>{t}</strong> <span className="muted" style={{ fontSize: 13 }}>{name}</span>
                    </button>
                  </td>
                  <td><div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}><ReasonChips vals={vals} thr={idx.rules} /></div></td>
                </tr>
                {open === t && (
                  <tr>
                    <td colSpan={3} style={{ background: "var(--surface-2)" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 20, padding: "8px 4px" }}>
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                          <strong style={{ fontSize: 14 }}>{f.L("Kural göstergeleri", "Rule indicators")}</strong>
                          <WhyPanel vals={vals} thr={idx.rules} compact />
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                          <ShapPanel shap={shap} feats={data.feats} compact />
                          <Link to={`/hisse/${t}`} className="btn sm" style={{ alignSelf: "flex-start" }}>{f.L("Geçmişini gör (16.10.2026'ya kadar)", "See its history (to 16 Oct 2026)")}</Link>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

const TARGET_END = "2027-05-28"; // Haziran 2027 değerlendirmesinden önceki son cuma

function fridaysBetween(a: string, b: string) {
  return Math.floor((Date.parse(b) - Date.parse(a)) / (7 * 864e5)) + 1;
}

export default function LiveTest() {
  const f = useT();
  const { data } = useJson<Live>("live.json");
  const rows = data?.weeks ?? [];
  const weeks = rows.length;
  const target = rows.length ? fridaysBetween(rows[0][0], TARGET_END) : 32;
  const started = !!data;
  const card = { padding: 22, display: "flex", flexDirection: "column", gap: 10 } as const;
  const big = { fontSize: 48, fontWeight: 600, letterSpacing: "-.02em", lineHeight: 1 } as const;
  const done = "3px solid var(--teal)", todo = "3px dashed var(--line-2)";
  return (
    <Page width="narrow">
      <section style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 800 }}>
        <span className={`badge ${started ? "b-teal" : "b-amber"}`} style={{ alignSelf: "flex-start" }}><Clock size={12} />
          {started ? f.L("Sürüyor · ileriye dönük test", "Running · prospective test") : f.L("Yakında · ileriye dönük test", "Coming soon · prospective test")}</span>
        <h1 className="h1">{f.L("Canlı test", "Live test")}</h1>
        <p style={{ fontSize: 18, lineHeight: 1.55 }}>{f.L("Model donduruldu. Her haftanın ilk 20 listesi kaydediliyor ve Haziran 2027'de o tarihe kadar açıklanan SPK kararlarıyla karşılaştırılacak.",
                                                           "The model is frozen. Every week's top-20 list is being recorded and will be compared in June 2027 with the SPK decisions announced by then.")}</p>
        <p style={{ fontSize: 15, lineHeight: 1.6 }} className="muted">{f.L("Geriye dönük testler ne kadar dikkatli kurulsa da geleceği görmüş olma riski taşır. Burada sonuç henüz kimse tarafından bilinmiyor: her liste kaydedildiği an parmak iziyle (sha256) sabitleniyor; liste sonradan değişirse parmak izi tutmaz. Neyin nasıl ölçüleceği, ilk listeden önce protokolde yazıldı.",
                                                                              "However carefully a backtest is built, it risks having seen the future. Here nobody knows the outcome yet: each list is fixed by its fingerprint (sha256) when recorded; if the list changed later the fingerprint would not match. What will be measured, and how, was written in the protocol before the first list.")}</p>
        <p style={{ fontSize: 13 }} className="faint">{f.L("Listelerin kendisi yayımlanmaz; burada yalnızca kayıt zamanları ve parmak izleri görünür.", "The lists themselves are not published; only record times and fingerprints are shown here.")}</p>
      </section>

      <section className="card" aria-labelledby="tl-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 18 }}>
        <h2 id="tl-h" className="eyebrow">{f.L("Takvim", "Timeline")}</h2>
        <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
          {[
            [f.L("Model donduruldu", "Model frozen"),
             data ? f.L(`${data.frozen} · veri sonu ${data.dataEnd} · ${data.knownCases} bilinen vaka`, `${data.frozen} · data to ${data.dataEnd}, ${data.knownCases} known cases`)
                  : f.L("Kasım 2026 · kod ve ayarlar sabitlenir", "Nov 2026 · code and settings fixed"), data ? done : todo],
            [f.L("Haftalık kayıt", "Weekly record"), f.L("Her hafta sonu · ilk 20 liste zaman ve parmak iziyle kaydedilir", "Every weekend · the top-20 list is saved with a timestamp and fingerprint"), weeks ? done : todo],
            [f.L("SPK karşılaştırması", "SPK comparison"), f.L("Haziran 2027 · listeler yeni SPK kararlarıyla eşleştirilir", "June 2027 · lists matched with new SPK decisions"), todo],
          ].map(([h, s, b]) => (
            <li key={h} style={{ display: "flex", flexDirection: "column", gap: 6, paddingTop: 14, borderTop: b }}>
              <strong style={{ fontSize: 15 }}>{h}</strong><span style={{ fontSize: 13 }} className="muted">{s}</span>
            </li>
          ))}
        </ol>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }} className="muted"><span>{f.L("İlerleme", "Progress")}</span><span>{weeks} / {target} {f.L("hafta", "weeks")}</span></div>
          <div role="progressbar" aria-label={f.L("Kaydedilen hafta", "Weeks recorded")} aria-valuemin={0} aria-valuemax={target} aria-valuenow={weeks} className="bar">
            <span style={{ width: `${Math.min(1, weeks / target) * 100}%` }} />
          </div>
        </div>
      </section>

      <section aria-label={f.L("Sayaçlar", "Counters")} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
        <div className="card" style={card}><p style={{ fontSize: 14, fontWeight: 500 }} className="muted">{f.L("Kaydedilen hafta", "Weeks recorded")}</p><strong style={big}>{weeks}</strong><p style={{ fontSize: 13 }} className="faint">{f.L(`hedef: Haziran 2027'ye kadar ${target} hafta`, `target: ${target} weeks by June 2027`)}</p></div>
        <div className="card" style={card}><p style={{ fontSize: 14, fontWeight: 500 }} className="muted">{f.L("Listeye giren farklı hisse", "Distinct stocks listed")}</p><strong style={big}>{data?.distinct ?? 0}</strong><p style={{ fontSize: 13 }} className="faint">{f.L("her hafta ilk 20", "top 20 each week")}</p></div>
        <div className="card" style={card}><p style={{ fontSize: 14, fontWeight: 500 }} className="muted">{f.L("Sonradan SPK kararı gelen", "Later got an SPK decision")}</p><strong style={{ ...big, color: "var(--faint)" }}>—</strong><p style={{ fontSize: 13 }} className="faint">{f.L("Haziran 2027'de hesaplanacak · rastgele beklenti de o zaman", "computed in June 2027, with the random expectation")}</p></div>
      </section>

      {data?.lists && <LiveLists data={data} />}

      <section className="card" aria-labelledby="log-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <h2 id="log-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("Haftalık kayıt", "Weekly log")}</h2>
          <span style={{ fontSize: 13 }} className="muted">{f.L("Kural + PU · ilk 20", "Rules + PU · top 20")}</span>
        </div>
        {rows.length ? (
          <>
            <div className="tbl-wrap">
              <table className="t">
                <thead><tr><th>{f.L("Hafta (cuma)", "Week (Friday)")}</th><th>{f.L("Kayıt (UTC)", "Recorded (UTC)")}</th><th className="num">{f.L("Hisse", "Stocks")}</th><th>{f.L("Parmak izi (ilk 20)", "Fingerprint (top 20)")}</th></tr></thead>
                <tbody>
                  {[...rows].reverse().map(([w, rec, late, n, sha]) => (
                    <tr key={w}>
                      <td>{w}{late ? <span className="badge b-amber" style={{ marginLeft: 8 }} title={f.L("Hafta kapandıktan 3 günden sonra kaydedildi", "Recorded more than 3 days after the week closed")}>{f.L("gecikmeli", "late")}</span> : null}</td>
                      <td className="muted">{rec.replace("T", " ").slice(0, 16)}</td>
                      <td className="num">{n}</td>
                      <td><code title={sha} style={{ fontSize: 12 }}>{sha.slice(0, 16)}…</code></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p style={{ fontSize: 13, lineHeight: 1.55 }} className="faint">{f.L(
              `"Gecikmeli" haftalar: araştırma verisinin bittiği ${data?.dataEnd} ile modelin dondurulduğu ${data?.frozen} arasındaki haftalar aynı gün geriye doğru kaydedildi. Model ve liste kuralı sabit olduğu için seçim yapılamaz; yine de sonuçlar bu haftalar çıkarılarak da raporlanacak. Model parmak izi: ${data?.modelSha.slice(0, 16)}…`,
              `"Late" weeks: the weeks between the end of the research data (${data?.dataEnd}) and the freeze (${data?.frozen}) were recorded retroactively on the same day. The model and list rule are fixed, so nothing could be selected; results will also be reported without these weeks. Model fingerprint: ${data?.modelSha.slice(0, 16)}…`)}</p>
          </>
        ) : (
          <div style={{ padding: "56px 24px", border: "1px dashed var(--line-2)", borderRadius: 12, display: "flex", flexDirection: "column", alignItems: "center", gap: 14, textAlign: "center" }}>
            <span style={{ width: 56, height: 56, borderRadius: 14, background: "var(--surface-2)", color: "var(--muted)", display: "flex", alignItems: "center", justifyContent: "center" }}><CalClock size={26} /></span>
            <h3 style={{ fontSize: 18, fontWeight: 600 }}>{f.L("İlk hafta kaydı bekleniyor", "Waiting for the first weekly record")}</h3>
            <p style={{ fontSize: 14, lineHeight: 1.55, maxWidth: 460 }} className="muted">{f.L("Model dondurulup ilk liste kaydedildiğinde kayıtlar burada en yenisi üstte görünecek.",
                                                                                                    "Once the model is frozen and the first list recorded, entries will appear here, newest first.")}</p>
            <a href={GITHUB} target="_blank" rel="noreferrer" className="btn sm"><Github />{f.L("Kodu incele", "View the code")}</a>
          </div>
        )}
      </section>
    </Page>
  );
}
