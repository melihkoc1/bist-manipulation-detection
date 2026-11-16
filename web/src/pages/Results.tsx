import { useState } from "react";
import { getResult, useIndex, type Index } from "../data";
import { useT } from "../i18n";
import { Page } from "../components/Layout";
import { Check, Half, Star, X } from "../components/Icons";
import { KpiCards, Loading, MODEL_NAMES } from "../components/ui";
import { Histogram } from "../components/charts";

const PERIODS = [["2017–2026", "2017–2026 (ana)", "2017–2026 (main)"], ["2017–2021"], ["2022–2026"], ["2012–2016"], ["2012–2026"]];
const ORDER = ["random", "0a_kural", "1_iforest", "2_lightgbm", "3a_pu_agirlikli", "3b_pu_bagging", "4_kural_pu"];
const SHORT: Record<string, [string, string]> = {
  random: ["Rastgele", "Random"], "0a_kural": ["Kurallar", "Rules"], "1_iforest": ["Isolation F.", "Isolation F."],
  "2_lightgbm": ["LightGBM", "LightGBM"], "3a_pu_agirlikli": ["PU ağırlıklı", "PU weighted"], "3b_pu_bagging": ["PU bagging", "PU bagging"], "4_kural_pu": ["Kural + PU", "Rules + PU"],
};

/** Deneme günlüğü: docs/yorum_v2.md ve git geçmişi. Geri alınan denemeler (kod silindi) burada yer almaz. */
const LOG: { idea: [string, string]; ok: boolean; eff: [string, string]; date: string; tag?: [string, string] }[] = [
  { idea: ["İlk değerlendirme (\"vakaların %40–47'si yakalandı\")", "First evaluation (\"40–47% of cases caught\")"], ok: false, tag: ["Geri çekildi", "Retracted"], eff: ["Rastgele tabanla karşılaştırınca rastgeleden iyi değildi; geri çekildi, değerlendirme baştan kuruldu", "Not better than random once compared with a baseline; retracted, evaluation rebuilt"], date: "2026-10-20" },
  { idea: ["Şirket profili göstergeleri (büyüklük, halka açıklık)", "Company profile features (size, free float)"], ok: false, tag: ["Çıkarıldı", "Removed"], eff: ["Model, daha önce manipüle edilen hisseleri ezberledi; çıkarıldı", "The model memorised previously manipulated stocks; removed"], date: "2026-10-18" },
  { idea: ["KAP içerik sınıflandırması ve \"habersiz hareket\" göstergeleri", "KAP content classification and \"move without news\" features"], ok: false, eff: ["Anlamlı katkı yok; tümü eklenince hafif kötüleşme (tez sorusu 3)", "No significant gain; adding all slightly hurts (thesis question 3)"], date: "2026-10-19" },
  { idea: ["PU öğrenme (gözetimli öğrenme yerine)", "PU learning (instead of supervised)"], ok: true, eff: ["AUC +0,03, eşli bootstrap ile anlamlı", "AUC +0.03, significant (paired bootstrap)"], date: "2026-10-20" },
  { idea: ["Eski SPK bültenleri (2009–2015) eklendi", "Older SPK bulletins (2009–2015) added"], ok: true, eff: ["Vaka 335 → 413; LightGBM AUC +0,05, PU +0,02 (anlamlı)", "Cases 335 → 413; LightGBM AUC +0.05, PU +0.02 (significant)"], date: "2026-10-22" },
  { idea: ["Kapanış / VWAP (\"kapanış oyunu\") göstergeleri", "Close / VWAP (\"marking the close\") features"], ok: false, eff: ["Modellere anlamlı katkı yok", "No significant gain inside the models"], date: "2026-10-23" },
  { idea: ["Kural + PU birleşimi (eşit ağırlıklı sıra ortalaması)", "Rules + PU ensemble (equal-weight rank average)"], ok: true, eff: ["En iyi model; AUC hem kurallardan hem PU'dan anlamlı yüksek", "Best model; AUC significantly above both rules and PU"], date: "2026-10-23" },
  { idea: ["Dönemi bilinmeyen vakaları tahminle etiketleme", "Estimating periods for cases without a stated period"], ok: false, eff: ["6 aylık pencereye göre kazanç yok; yalnızca belgelendi", "No gain over the 6-month window; documented only"], date: "2026-10-24" },
];

export default function Results() {
  const { data: idx, error } = useIndex();
  if (!idx) return <Page><Loading error={error} /></Page>;
  return <Body idx={idx} />;
}

function Body({ idx }: { idx: Index }) {
  const f = useT();
  const [period, setPeriod] = useState("2017–2026");
  const rows = ORDER.map((m) => ({ m, r: getResult(idx.results, m, period)! })).filter((x) => x.r);
  const best = "4_kural_pu";
  const main = getResult(idx.results, best)!;
  const rules = getResult(idx.results, "0a_kural")!;
  const pu = getResult(idx.results, "3b_pu_bagging")!;
  const lgb = getResult(idx.results, "2_lightgbm")!;
  const rnd = rows[0]?.r;

  // gruplu çubuk grafik
  const Yb = (v: number) => 300 - v * 3.6;
  const step = 1180 / rows.length;
  const tm = idx.timing;
  const binsOf = (xs: number[], edges: number[]) => edges.slice(0, -1).map((lo, i) => xs.filter((x) => x > lo && x <= edges[i + 1]).length);
  const firstEdges = [-1e9, 0, 7, 30, 91, 182, 365, 1e9];
  const sancEdges = [-1e9, 0, 91, 182, 365, 548, 730, 1e9];
  const medIdx = (med: number, edges: number[]) => Math.max(0, edges.findIndex((e, i) => i > 0 && med <= e) - 1);

  return (
    <Page>
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "flex-end", gap: 20 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 720 }}>
          <h1 className="h1">{f.L("Sonuçlar", "Results")}</h1>
          <p className="lead">{f.L("Her yıl, yalnızca o yıldan önceki veri ve SPK kararlarıyla eğitilen modelle puanlandı. Her sayı aynı uzunlukta rastgele bir listeyle karşılaştırılıyor.",
                                   "Each year is scored by a model trained only on data and SPK decisions from before that year. Every number is compared with a random list of the same length.")}</p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, alignItems: "flex-start" }}>
          <span id="plab" style={{ fontSize: 12, fontWeight: 600 }} className="muted">{f.L("Test dönemi", "Test period")}</span>
          <div className="seg" role="group" aria-labelledby="plab">
            {PERIODS.map(([p, tr, en]) => <button key={p} type="button" className={p === period ? "on" : ""} aria-pressed={p === period} onClick={() => setPeriod(p)}>{tr ? f.L(tr, en) : p}</button>)}
          </div>
        </div>
      </div>

      <section aria-label={f.L("Ana sonuçlar", "Key results")}><KpiCards idx={idx} period={period} /></section>

      <section className="card" aria-labelledby="bar-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
          <h2 id="bar-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L(`İlk 20'de yakalanan SPK vakası, modele göre · ${rows[0]?.r.nCases ?? ""} vaka`, `SPK cases caught in the top 20, by model · ${rows[0]?.r.nCases ?? ""} cases`)}</h2>
          <div className="legend" style={{ fontSize: 13 }}>
            <span><span style={{ width: 12, height: 12, borderRadius: 3, background: "var(--teal)" }} />{f.L("Yakalama", "Caught")}</span>
            <span><span style={{ width: 12, height: 12, borderRadius: 3, background: "var(--rand)" }} />{f.L("Rastgele beklenti", "Random expectation")}</span>
          </div>
        </div>
        <div style={{ overflowX: "auto" }}>
          <svg viewBox="0 0 1240 340" style={{ width: "100%", minWidth: 640, height: "auto", display: "block" }} role="img"
               aria-label={rows.map((x) => `${f.L(...SHORT[x.m])} ${f.pct(x.r.rec)}`).join(", ") + f.L(`; rastgele beklenti ${f.pct(rnd?.rnd)}`, `; random expectation ${f.pct(rnd?.rnd)}`)}>
            {[0, 20, 40, 60, 80].map((v) => (
              <g key={v}><line x1="50" x2="1230" y1={Yb(v)} y2={Yb(v)} stroke="var(--grid)" /><text x="42" y={Yb(v) + 4} fontSize="12" textAnchor="end" fill="var(--faint)">{f.pct(v / 100)}</text></g>
            ))}
            {rows.map((x, i) => {
              const cx = 50 + step / 2 + i * step, v = x.r.rec * 100, b = x.r.rnd * 100;
              return (
                <g key={x.m}>
                  {x.m === best && <rect x={cx - 70} y="14" width="140" height="286" rx="8" fill="var(--teal-soft)" />}
                  <rect x={cx - 46} y={Yb(v)} width="44" height={v * 3.6} rx="3" fill={x.m === "random" ? "var(--rand)" : "var(--teal)"} />
                  <rect x={cx + 2} y={Yb(b)} width="44" height={b * 3.6} rx="3" fill="var(--rand)" opacity={x.m === "random" ? 0.5 : 1} />
                  <text x={cx - 24} y={Yb(v) - 8} fontSize="13" fontWeight="600" textAnchor="middle" fill="var(--text)">{f.pct(x.r.rec)}</text>
                  <text x={cx + 24} y={Yb(b) - 8} fontSize="12" textAnchor="middle" fill="var(--muted)">{f.pct(x.r.rnd)}</text>
                  <text x={cx} y="322" fontSize="13" fontWeight={x.m === best ? 700 : 500} textAnchor="middle" fill="var(--text)">{f.L(...SHORT[x.m])}</text>
                </g>
              );
            })}
          </svg>
        </div>
        <div className="tbl-wrap">
          <table className="t num">
            <caption className="sr">{f.L(`Model karşılaştırması, ${period}`, `Model comparison, ${period}`)}</caption>
            <thead><tr>
              <th scope="col">Model</th><th scope="col">AUC [%95 {f.L("GA", "CI")}]</th><th scope="col">{f.L("İlk 20'de yakalama", "Caught in top 20")}</th>
              <th scope="col">{f.L("Rastgele", "Random")}</th><th scope="col">× {f.L("rastgele", "random")}</th><th scope="col">{f.L("Zirveden önce", "Before peak")}</th>
              <th scope="col">{f.L("İlk 10 isabeti", "Top-10 precision")}</th><th scope="col">{f.L("Medyan öncü gün", "Median lead (days)")}</th>
            </tr></thead>
            <tbody>
              {rows.map(({ m, r }) => (
                <tr key={m} className={m === best ? "best" : m === "random" ? "rand" : ""}>
                  <td><span style={{ display: "inline-flex", alignItems: "center", gap: 8, fontWeight: 600 }}>{f.L(...MODEL_NAMES[m])}
                    {m === best && <span className="badge b-teal"><Star size={11} />{f.L("En iyi", "Best")}</span>}</span></td>
                  <td>{f.num(r.auc, 2)} [{f.num(r.aucLo, 2)}–{f.num(r.aucHi, 2)}]</td>
                  <td>{f.pct(r.rec)}</td><td>{f.pct(r.rnd)}</td><td>{f.times(r.rec / r.rnd)}</td>
                  <td>{f.pct(r.prePeak)}</td><td>{f.pct(r.prec10, 1)}</td><td>{f.num(r.lead, 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: 12 }} className="faint">
          {f.L(`İlk 10 isabeti: listenin ilk 10'undaki hisselerden SPK vakası olanların oranı (rastgele ~${f.pct(rnd?.base10, 1)}). GA: vaka bazında bootstrap güven aralığı. Öncü gün: manipülasyon başlangıcından ilk alarma.`,
               `Top-10 precision: share of top-10 stocks that are SPK cases (random ~${f.pct(rnd?.base10, 1)}). CI: case-level bootstrap. Lead: days from manipulation start to first alarm.`)}
        </p>
      </section>

      <section className="card" aria-labelledby="hist-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <h2 id="hist-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("SPK'ya göre zaman", "Timing relative to SPK")}</h2>
          <p style={{ fontSize: 14 }} className="muted">
            {f.L(`Kural + PU'nun 2017–2026'da yakaladığı ${tm.nCaught} vakada (${tm.nCases} vakadan), ilk alarmdan SPK'nın ilk kararına ve ilk cezasına kadar geçen süre. Alarm, vakaların ${f.pct(tm.pctBefore)}'ünde SPK'nın ilk kararından önce geldi.`,
                 `For the ${tm.nCaught} cases (of ${tm.nCases}) caught by Rules + PU in 2017–2026: time from the first alarm to SPK's first decision and first sanction. In ${f.pct(tm.pctBefore)} of cases the alarm came before SPK's first decision.`)}
          </p>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(440px, 100%), 1fr))", gap: 28 }}>
          {[
            { t: f.L("İlk alarm → SPK'nın ilk kararı (tedbir dahil)", "First alarm → SPK's first decision (incl. measures)"), xs: tm.first, med: tm.medFirst, edges: firstEdges,
              labels: [f.L("sonra", "after"), f.L("0–7 g", "0–7 d"), f.L("1–4 hf", "1–4 wk"), f.L("1–3 ay", "1–3 mo"), f.L("3–6 ay", "3–6 mo"), f.L("6–12 ay", "6–12 mo"), "12+"],
              medTxt: f.L(`medyan ${Math.round(tm.medFirst)} gün`, `median ${Math.round(tm.medFirst)} days`) },
            { t: f.L("İlk alarm → SPK'nın ilk cezası / suç duyurusu", "First alarm → SPK's first sanction / complaint"), xs: tm.sanction, med: tm.medSanction, edges: sancEdges,
              labels: [f.L("sonra", "after"), f.L("0–3 ay", "0–3 mo"), "3–6", "6–12", "12–18", "18–24", "24+"],
              medTxt: f.L(`medyan ${Math.round(tm.medSanction / 30.4)} ay`, `median ${Math.round(tm.medSanction / 30.4)} months`) },
          ].map((h) => {
            const bins = binsOf(h.xs, h.edges);
            return (
              <figure key={h.t} style={{ margin: 0, display: "flex", flexDirection: "column", gap: 10 }}>
                <figcaption style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
                  <strong style={{ fontSize: 15, fontWeight: 600 }}>{h.t}</strong><span className="badge b-teal">{h.medTxt}</span>
                </figcaption>
                <Histogram bins={bins} labels={h.labels} medianIdx={medIdx(h.med, h.edges)} missIdx={0}
                           aria={`${h.t}: ${bins.map((n, i) => `${h.labels[i]} ${n}`).join(", ")}`} />
              </figure>
            );
          })}
        </div>
        <p style={{ fontSize: 12 }} className="faint">
          {f.L("Gri sütun: alarm SPK'nın kararından sonra geldi. Dürüst okuma: SPK pek çok vakada dönem bitiminden kısa süre sonra tedbir alıyor; asıl zaman kazancı ceza aşamasına göre.",
               "Gray bar: the alarm came after SPK's decision. Honest reading: SPK often acts with a measure soon after the period ends; the real time gain is relative to the sanction stage.")}
          {period !== "2017–2026" && f.L(" (Bu bölüm her zaman 2017–2026 ana dönemini gösterir.)", " (This section always shows the main 2017–2026 period.)")}
        </p>
      </section>

      <section aria-labelledby="q-h" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <h2 id="q-h" style={{ fontSize: 22, fontWeight: 600, letterSpacing: "-.01em" }}>{f.L("Tezin üç sorusu", "The thesis's three questions")}</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16 }}>
          {[
            { b: <span className="badge b-green" style={{ fontSize: 13 }}><Check size={13} />{f.L("Evet", "Yes")}</span>, q: f.L("Erken tespit mümkün mü?", "Is early detection possible?"),
              a: f.L(`Vakaların ${f.pct(main.rec)}'si ilk 20'de yakalandı (rastgele ${f.pct(main.rnd)}); ${f.pct(main.prePeak)}'sı fiyat zirvesinden önce. İlk alarm medyan ${main.lead} gün sonra.`,
                     `${f.pct(main.rec)} of cases were caught in the top 20 (random ${f.pct(main.rnd)}); ${f.pct(main.prePeak)} before the price peak. Median first alarm after ${main.lead} days.`) },
            { b: <span className="badge b-amber" style={{ fontSize: 13 }}><Half size={13} />{f.L("Kısmen", "Partly")}</span>, q: f.L("PU öğrenme daha iyi mi?", "Is PU learning better?"),
              a: f.L(`Gözetimli öğrenmeden anlamlı olarak iyi (AUC ${f.num(pu.auc, 2)} – ${f.num(lgb.auc, 2)}); tek başına kurallarla (${f.num(rules.auc, 2)}) istatistiksel olarak berabere. En iyi sonuç ikisinin birleşimiyle (${f.num(main.auc, 2)}).`,
                     `Significantly better than supervised learning (AUC ${f.num(pu.auc, 2)} vs ${f.num(lgb.auc, 2)}); statistically tied with rules alone (${f.num(rules.auc, 2)}). Best when combined (${f.num(main.auc, 2)}).`) },
            { b: <span className="badge b-gray" style={{ fontSize: 13 }}><X size={13} />{f.L("Hayır", "No")}</span>, q: f.L("Habersiz hareket işe yarıyor mu?", "Do \"moves without news\" help?"),
              a: f.L("KAP haberi olmadan gelen fiyat hareketi göstergeleri anlamlı katkı yapmadı; tüm KAP göstergeleri eklenince sonuç hafifçe kötüleşti.",
                     "Indicators of price moves without KAP news gave no significant gain; adding all KAP features slightly hurt.") },
          ].map((x) => (
            <div key={x.q} className="card" style={{ padding: 22, display: "flex", flexDirection: "column", gap: 12 }}>
              <span style={{ alignSelf: "flex-start" }}>{x.b}</span>
              <h3 style={{ fontSize: 18, fontWeight: 600 }}>{x.q}</h3>
              <p style={{ fontSize: 14, lineHeight: 1.55 }} className="muted">{x.a}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="card" aria-labelledby="log-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <h2 id="log-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("Deneme günlüğü", "Experiment log")}</h2>
          <p style={{ fontSize: 14 }} className="muted">{f.L("Denenen her fikir, işe yarasın ya da yaramasın, burada kayıtlı. Ayrıntılar: docs/yorum_v2.md.", "Every idea tried, whether it worked or not. Details: docs/yorum_v2.md.")}</p>
        </div>
        <div className="tbl-wrap">
          <table className="t">
            <thead><tr><th scope="col">{f.L("Fikir", "Idea")}</th><th scope="col">{f.L("Sonuç", "Outcome")}</th><th scope="col">{f.L("Etki", "Effect")}</th><th scope="col">{f.L("Tarih", "Date")}</th></tr></thead>
            <tbody>
              {LOG.map((l) => (
                <tr key={l.date + l.idea[0]}>
                  <td style={{ fontWeight: 500, padding: "11px 12px" }}>{f.L(...l.idea)}</td>
                  <td style={{ padding: "11px 12px" }}>{l.ok ? <span className="badge b-green"><Check size={12} />{f.L("İşe yaradı", "Worked")}</span>
                                                            : <span className="badge b-gray"><X size={12} />{l.tag ? f.L(...l.tag) : f.L("Katkı yok", "No gain")}</span>}</td>
                  <td className="muted" style={{ padding: "11px 12px" }}>{f.L(...l.eff)}</td>
                  <td className="muted" style={{ whiteSpace: "nowrap", padding: "11px 12px" }}>{f.date(l.date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </Page>
  );
}
