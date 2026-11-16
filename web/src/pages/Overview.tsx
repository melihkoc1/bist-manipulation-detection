import { Link } from "react-router-dom";
import { addDays, EXAMPLES, getResult, useIndex, useJson, useStock, weekMonday, type WeekEntry } from "../data";
import { useT } from "../i18n";
import { Page } from "../components/Layout";
import { Arrow, Check, Doc, Layers, List, Pulse, Shield, Warn } from "../components/Icons";
import { ChartLegend, KpiCards, Loading, SpkBadge, Waffle } from "../components/ui";
import { MiniPrice } from "../components/charts";

const SAMPLE = EXAMPLES[0];

export default function Overview() {
  const f = useT();
  const { data: idx, error } = useIndex();
  const year = SAMPLE.week.slice(0, 4);
  const weeks = useJson<{ weeks: WeekEntry[] }>(`weeks/${year}.json`);
  const izfas = useStock("IZFAS");
  if (!idx) return <Page><Loading error={error} /></Page>;
  const r = getResult(idx.results, "4_kural_pu")!;
  const rnd = getResult(idx.results, "random")!;
  const wk = weeks.data?.weeks.find((w) => w.end === SAMPLE.week);
  const cs = idx.cases.find((c) => c.id === "IZFAS-0")!;
  const drop = cs.minAfter ? 1 - cs.minAfter / cs.peakPx : null;
  const lift = r.rec / r.rnd;
  const c = idx.counts;

  return (
    <Page gap={40}>
      <section style={{ display: "flex", flexWrap: "wrap", gap: 40, alignItems: "center", paddingTop: 8 }}>
        <div style={{ flex: "1 1 560px", minWidth: 0, display: "flex", flexDirection: "column", gap: 20 }}>
          <span className="badge b-teal" style={{ alignSelf: "flex-start" }}><Shield size={14} />
            {f.L("Bitirme projesi · 2012–2026 SPK vakalarıyla değerlendirildi", "Graduation project · evaluated on 2012–2026 SPK cases")}</span>
          <h1 style={{ fontSize: "clamp(32px, 4vw, 48px)", lineHeight: 1.12, fontWeight: 700, letterSpacing: "-.025em", maxWidth: 720 }}>
            {f.L("Borsa İstanbul'da manipülasyonu SPK'dan önce fark eden erken uyarı sistemi", "An early-warning system that spots manipulation on Borsa Istanbul before the regulator")}
          </h1>
          <p style={{ fontSize: 18, lineHeight: 1.55, color: "var(--muted)", maxWidth: 640 }}>
            {f.L("Günlük işlem verisi, KAP bildirimleri ve SPK kararlarıyla her hafta tüm hisseleri şüphe skoruna göre sıralar.",
                 "Using daily trading data, company disclosures (KAP) and regulator (SPK) decisions, it ranks every stock by suspicion each week.")}
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12, paddingTop: 4 }}>
            <Link to="/zaman-makinesi" className="btn primary">{f.L("Zaman makinesini dene", "Try the time machine")}<Arrow /></Link>
            <Link to="/yontem" className="btn">{f.L("Nasıl çalışıyor?", "How does it work?")}</Link>
          </div>
        </div>
        <div className="card" style={{ flex: "1 1 420px", minWidth: 0, padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
            <p className="eyebrow">{f.L("Örnek hafta", "Sample week")} · {f.range(weekMonday(SAMPLE.week), SAMPLE.week)}</p>
            {wk && <p style={{ fontSize: 12 }} className="faint">{f.L(`${wk.n} hisse puanlandı`, `${wk.n} stocks scored`)}</p>}
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            {(wk?.lists["4_kural_pu"] ?? []).slice(0, 4).map((row, i) => (
              <div key={row[0]} style={{ display: "grid", gridTemplateColumns: "28px 64px 1fr 120px", gap: 12, alignItems: "center", padding: "10px 0", borderBottom: i < 3 ? "1px solid var(--line)" : 0, fontSize: 14 }}>
                <span className="faint">{row[1]}</span>
                {row[4] ? <strong>{row[0]}</strong> : <strong className="faint" aria-label={f.L("gizlendi", "hidden")}>•••••</strong>}
                <span className="bar"><span style={{ width: `${row[2] * 100}%` }} /></span>
                <span style={{ justifySelf: "end" }}><SpkBadge link={row[4]} days={row[5]} short /></span>
              </div>
            ))}
            {!wk && <Loading />}
          </div>
          <p style={{ fontSize: 12 }} className="faint">
            {f.L("Her hafta tüm hisseler sıralanır; SPK etiketi yalnızca sonradan bakıldığında görünür. SPK kararı olmayan hisseler bu kartta gizlendi.",
                 "All stocks are ranked every week; the SPK label is only visible in hindsight. Stocks without an SPK decision are hidden on this card.")}
          </p>
        </div>
      </section>

      <section aria-labelledby="kpi-h" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <h2 id="kpi-h" className="eyebrow">{f.L(`Ana sonuçlar · 2017–2026 test dönemi · ${r.nCases} SPK vakası`, `Key results · 2017–2026 test period · ${r.nCases} SPK cases`)}</h2>
        <KpiCards idx={idx} />
      </section>

      <section className="card" aria-labelledby="waffle-h" style={{ padding: "clamp(20px, 3vw, 32px)", display: "flex", flexDirection: "column", gap: 28 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 760 }}>
          <h2 id="waffle-h" style={{ fontSize: 26, fontWeight: 600, letterSpacing: "-.015em" }}>{f.L(`Rastgeleden ${f.num(lift, 0)} kat iyi ne demek?`, `What does "${f.num(lift, 0)}× better than random" mean?`)}</h2>
          <p className="lead">{f.L("Her kare bir vakayı ya da bir alarmı temsil eder. Aynı uzunlukta, rastgele seçilmiş bir listeyle karşılaştırıyoruz.",
                                   "Each square is one case or one alarm. We compare with a random list of the same length.")}</p>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(420px, 100%), 1fr))", gap: 32 }}>
          {[
            { h: f.L("100 SPK vakasından kaçı ilk 20'de yakalandı?", "Of 100 SPK cases, how many were caught in the top 20?"), a: r.rec * 100, b: r.rnd * 100, approx: false },
            { h: f.L("Sistem 100 hisseye \"şüpheli\" derse, kaçında gerçekten SPK'nın tespit ettiği bir manipülasyon var?", "If the system flags 100 stocks, how many turn out to be manipulation confirmed by SPK?"), a: r.prec10 * 100, b: rnd.prec10 * 100, approx: true },
          ].map((g) => (
            <div key={g.h} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <h3 style={{ fontSize: 16, fontWeight: 600 }}>{g.h}</h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 32 }}>
                {[{ n: g.a, cls: "t1" as const, who: f.L("sistem", "system"), col: "var(--teal-ink)" },
                  { n: g.b, cls: "g1" as const, who: f.L("rastgele", "random"), col: "var(--gray-ink)" }].map((x) => (
                  <figure key={x.who} style={{ margin: 0, display: "flex", flexDirection: "column", gap: 10 }}>
                    <Waffle n={x.n} cls={x.cls} label={`${x.who}: ${Math.round(x.n)} / 100`} />
                    <figcaption style={{ fontSize: 14 }}><strong style={{ fontSize: 22, fontWeight: 600, color: x.col }}>{g.approx ? "~" : ""}{Math.round(x.n)}</strong> <span className="muted">{x.who}</span></figcaption>
                  </figure>
                ))}
              </div>
            </div>
          ))}
        </div>
        <p style={{ fontSize: 14, lineHeight: 1.55, paddingTop: 16, borderTop: "1px solid var(--line)" }} className="muted">
          {f.L(`Kısacası: sistemin şüpheli bulduğu her 10 hisseden 1'i gerçek bir SPK manipülasyon vakası; rastgele seçimde bu oran 33'te 1. Geri kalanlar "temiz" demek değil, SPK'nın kararı olmayan hisselerdir (SPK her vakayı yakalamıyor). Sistem bir hüküm vermez; havalimanındaki güvenlik kapısı gibi önce nereye bakılacağını gösterir ve uzmanın listesini rastgeleye göre yaklaşık ${f.num(r.plift10, 0)} kat isabetli hâle getirir. (Ölçüm: her haftanın en şüpheli 10 hissesi, 2017–2026.)`,
               `In short: 1 in every 10 stocks the system flags is a real SPK manipulation case; with random picks it is 1 in 33. The rest are not "clean": they are stocks without an SPK decision (SPK does not catch every case). The system does not deliver a verdict; like an airport security gate it shows where to look first, making an analyst's list about ${f.num(r.plift10, 0)}× more accurate than random. (Measured on each week's 10 most suspicious stocks, 2017–2026.)`)}
        </p>
      </section>

      <section aria-labelledby="how-h" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: 12 }}>
          <h2 id="how-h" style={{ fontSize: 26, fontWeight: 600, letterSpacing: "-.015em" }}>{f.L("Nasıl çalışıyor", "How it works")}</h2>
          <Link to="/yontem" style={{ fontSize: 14, fontWeight: 600 }}>{f.L("Yöntemin tamamı", "Full method")}</Link>
        </div>
        <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
          {[
            [<Doc size={22} />, f.L("SPK kararları", "SPK decisions"), f.L(`${c.bulletinYears[1] - c.bulletinYears[0] + 1} yıllık bültenlerden manipülasyon kararları ve SPK'nın belirttiği dönemler çıkarılır.`, `Manipulation decisions and the periods SPK states are extracted from ${c.bulletinYears[1] - c.bulletinYears[0] + 1} years of bulletins.`)],
            [<Pulse size={22} />, f.L("Göstergeler", "Indicators"), f.L("Hacim patlaması, kesintisiz yükseliş, tavan serisi gibi göstergeler yalnızca geçmiş veriyle hesaplanır.", "Indicators such as volume surges, steady rises and limit-up streaks are computed from past data only.")],
            [<Layers size={22} />, f.L("Modeller", "Models"), f.L("Uzman kuralları ve PU öğrenme birleştirilerek her hisseye bir şüphe skoru verilir.", "Expert rules and PU learning are combined into one suspicion score per stock.")],
            [<List size={22} />, f.L("Haftalık liste", "Weekly list"), f.L(`Her hafta ${c.minWeek}–${c.maxWeek} hisse sıralanır; ilk 20 uzman incelemesi için önerilir.`, `Every week ${c.minWeek}–${c.maxWeek} stocks are ranked; the top 20 are suggested for review.`)],
          ].map(([icon, h, p], i) => (
            <li key={i} className="card" style={{ padding: 22, display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ width: 44, height: 44, borderRadius: 10, background: "var(--teal-soft)", color: "var(--teal-ink)", display: "flex", alignItems: "center", justifyContent: "center" }}>{icon}</span>
                <span style={{ fontSize: 13 }} className="faint">{f.L("Adım", "Step")} {i + 1}</span>
              </div>
              <h3 style={{ fontSize: 17, fontWeight: 600 }}>{h}</h3>
              <p style={{ fontSize: 14, lineHeight: 1.5 }} className="muted">{p}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="card" aria-labelledby="case-h" style={{ padding: 28, display: "flex", flexWrap: "wrap", gap: 32, alignItems: "center" }}>
        <div style={{ flex: "1 1 340px", display: "flex", flexDirection: "column", gap: 14 }}>
          <p className="eyebrow">{f.L("Öne çıkan vaka", "Featured case")}</p>
          <h2 id="case-h" style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-.015em" }}>IZFAS · 2018</h2>
          <p style={{ fontSize: 17, lineHeight: 1.5 }}>
            {f.L(`${cs.leadDays}. günde alarm; SPK işlem yasağından sonra fiyat ${f.pct(drop)} düştü.`, `Alarm on day ${cs.leadDays}; after SPK's trading ban the price fell ${f.pct(drop)}.`)}
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            <span className="badge b-green"><Check size={12} />{f.L("Yakalandı", "Caught")}</span>
            <span className="badge b-red"><Warn size={12} />{f.L(`İlk alarm ${cs.leadDays}. gün`, `First alarm day ${cs.leadDays}`)}</span>
          </div>
          <Link to="/vakalar/IZFAS-0" className="btn" style={{ alignSelf: "flex-start", marginTop: 4 }}>{f.L("Vakayı incele", "Open the case")}</Link>
        </div>
        <figure style={{ flex: "2 1 520px", margin: 0, display: "flex", flexDirection: "column", gap: 10, minWidth: 0 }}>
          {izfas.data ? (
            <MiniPrice data={izfas.data} from={addDays(cs.start, -60)} to={addDays(cs.end, 150)} mark={cs.firstAlert ?? undefined}
                       markLabel={f.L(`İlk alarm · ${cs.leadDays}. gün`, `First alarm · day ${cs.leadDays}`)} w={640} h={220}
                       ariaLabel={f.L(`IZFAS fiyat grafiği: SPK döneminde fiyat yükseliyor, ${cs.leadDays}. günde alarm, sonra ${f.pct(drop)} düşüş`, `IZFAS price: rises during the SPK period, alarm on day ${cs.leadDays}, then a ${f.pct(drop)} fall`)} />
          ) : <Loading error={izfas.error} />}
          <figcaption><ChartLegend decision={false} /></figcaption>
        </figure>
      </section>

      <section aria-label={f.L("Veri kapsamı", "Data coverage")} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)" }}>
        {[
          [f.L(`${c.bulletinYears[1] - c.bulletinYears[0] + 1} yıl`, `${c.bulletinYears[1] - c.bulletinYears[0] + 1} years`), f.L("SPK bülteni", "of SPK bulletins")],
          [String(c.cases), f.L("SPK vakası", "SPK cases")],
          [f.L(`${Math.round(c.kap / 1000)} bin`, `${Math.round(c.kap / 1000)}k`), f.L("KAP bildirimi", "KAP disclosures")],
          [`${c.minWeek}–${c.maxWeek}`, f.L("hisse, her hafta", "stocks, every week")],
        ].map(([a, b]) => (
          <div key={b} style={{ padding: "24px 8px", display: "flex", flexDirection: "column", gap: 4 }}>
            <strong style={{ fontSize: 28, fontWeight: 600 }}>{a}</strong><span style={{ fontSize: 14 }} className="muted">{b}</span>
          </div>
        ))}
      </section>
    </Page>
  );
}
