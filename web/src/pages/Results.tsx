import { useState } from "react";
import { getResult, useIndex, useJson, type Index } from "../data";
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
  { idea: ["Birleşim ağırlıklarını geçmiş yıllardan öğrenmek", "Learning ensemble weights from past years"], ok: false, eff: ["Eşit ağırlıkla aynı (AUC +0,000, anlamsız); eşit ağırlık korundu", "Same as equal weights (AUC +0.000, n.s.); equal weights kept"], date: "2026-11-17" },
  { idea: ["Hissenin SPK geçmişi (önceki vaka sayısı)", "Stock's SPK history (number of prior cases)"], ok: false, eff: ["Anlamlı kötüleşme (PU AUC −0,04); model \"sicili olan\" hisseleri öne çekti", "Significantly worse (PU AUC −0.04); the model favoured stocks with a record"], date: "2026-11-17" },
  { idea: ["Birlikte sıçrayan hisseler ağı", "Network of stocks surging together"], ok: false, eff: ["SPK vakaları benzer yükselişlerden daha yalnız hareket ediyor; Kural + PU değişmedi", "SPK cases move more alone than similar rallies; Rules + PU unchanged"], date: "2026-11-25" },
  { idea: ["Kendi pompala-boşalt örüntü etiketlerimiz (eğitimde zayıf pozitif)", "Our own pump-and-dump pattern labels (weak positives in training)"], ok: false, eff: ["612 / 214 ek etiket; PU'nun AUC'si hafif arttı ama Kural + PU değişmedi", "612 / 214 extra labels; PU AUC rose slightly but Rules + PU did not change"], date: "2026-11-25" },
  { idea: ["\"Ne zaman çöker?\" modeli (SPK etiketi yerine fiyattan büyük düşüş)", "\"When will it crash?\" model (large price drop instead of SPK labels)"], ok: false, eff: ["SPK etiketi görmeden vakaları PU'ya yakın sıralıyor (AUC 0,808); birleşime katkı anlamsız", "Ranks SPK cases almost as well as PU without seeing SPK labels (AUC 0.808); no significant gain in the ensemble"], date: "2026-11-25" },
  { idea: ["Otomatik kodlayıcı ile anomali (etiketsiz)", "Autoencoder anomaly detection (unsupervised)"], ok: false, eff: ["Isolation Forest'tan anlamlı zayıf (AUC −0,042); birleşime katkı yok", "Significantly weaker than Isolation Forest (AUC −0.042); no gain in the ensemble"], date: "2026-11-25" },
  { idea: ["Derin öğrenme (ham seriden 1B CNN)", "Deep learning (1D CNN on raw series)"], ok: false, eff: ["Tek başına PU'nun anlamlı gerisinde; birleşime katkı yok (az etiketle elle yazılmış göstergeler daha verimli)", "Alone significantly behind PU; no gain in the ensemble (with few labels hand-crafted features work better)"], date: "2026-11-25" },
  { idea: ["SPK vakalarına grafik şekli benzerliği (DTW)", "Chart-shape similarity to SPK cases (DTW)"], ok: false, eff: ["Tek başına rastgelenin 2 katı yakalıyor ama PU'nun gerisinde; birleşime katkı yok", "Alone it catches twice as many as random but trails PU; no gain in the ensemble"], date: "2026-11-25" },
  { idea: ["Üçlü birleşim: Kural + PU-LightGBM + PU-Random Forest", "Three-way ensemble: rules + PU-LightGBM + PU-Random Forest"], ok: false, tag: ["Sınırda", "Borderline"], eff: ["AUC 0,849 → 0,856 (anlamlı) ama ilk 20'de yakalama artmadı; ana model değişmedi", "AUC 0.849 → 0.856 (significant) but top-20 recall did not improve; main model unchanged"], date: "2026-11-25" },
  { idea: ["PU içinde Random Forest / Extra Trees", "Random Forest / Extra Trees inside PU"], ok: false, tag: ["Kısmi", "Partial"], eff: ["PU tek başına AUC +0,02 (anlamlı), ama listenin üstü ve kurallarla birleşim değişmedi", "PU alone AUC +0.02 (significant), but the top of the list and the ensemble with rules did not change"], date: "2026-11-25" },
  { idea: ["Farklı PU yöntemleri (Elkan–Noto, nnPU)", "Other PU methods (Elkan–Noto, nnPU)"], ok: false, eff: ["Elkan–Noto bagging ile aynı; nnPU daha kötü (AUC −0,015, anlamlı). PU'nun türü ikincil", "Elkan–Noto equals bagging; nnPU is worse (AUC −0.015, significant). The PU variant matters little"], date: "2026-11-25" },
  { idea: ["Lojistik regresyon (basit, açıklanabilir taban)", "Logistic regression (simple, explainable baseline)"], ok: false, tag: ["Taban", "Baseline"], eff: ["AUC ağaç modellerine çok yakın; ilk 20'de 3–7 puan geride (anlamsız). Sinyalin çoğu doğrusal", "AUC very close to the tree models; 3–7 points behind in the top 20 (not significant). Most of the signal is linear"], date: "2026-11-24" },
  { idea: ["Fiyat ile temel değerin kopması (PD/DD, kâr verimi)", "Price vs fundamentals (price-to-book, earnings yield)"], ok: false, tag: ["Zararlı", "Harmful"], eff: ["Kural + PU yakalama −5,7 puan (anlamlı); model şirket türünü ezberliyor", "Rules + PU recall −5.7 points (significant); the model memorises company types"], date: "2026-11-19" },
  { idea: ["Borsa İstanbul VBTS tedbirleri (açığa satış yasağı, brüt takas, tek fiyat)", "Borsa Istanbul volatility measures (VBTS: short-sale ban, gross settlement, single price)"], ok: false, eff: ["Kazanç yok (AUC −0,001); tedbir, modelin zaten gördüğü fiyat oynaklığını özetliyor", "No gain (AUC −0.001); the measures summarise price volatility the model already sees"], date: "2026-11-19" },
  { idea: ["Ana set dışı vakaları zayıf etiket olarak eklemek", "Adding non-core cases as weak labels"], ok: false, eff: ["AUC çok az arttı (+0,003, sınırda anlamlı) ama yakalama ve isabet artmadı; ana model değişmedi", "AUC rose slightly (+0.003, borderline significant) but recall and precision did not; main model unchanged"], date: "2026-11-18" },
  { idea: ["Yükseliş sırasında içeriden satış (KAP bildirimleri)", "Insider selling during the run-up (KAP filings)"], ok: false, eff: ["Kazanç yok; SPK vakalarında satış bildirimi rastgele günlerden bile az (%1,1 / %1,7): satanlar bildirim yükümlüsü değil", "No gain; SPK cases have even fewer sell filings than random days (1.1% / 1.7%): the sellers are not obliged to file"], date: "2026-11-17" },
  { idea: ["Yükselişi bütün olarak izleyen göstergeler", "Indicators tracking the whole run-up"], ok: false, eff: ["Kazanç yok (Kural + PU AUC −0,005, yakalama −2,4 puan, anlamsız); mevcut \"dipten yükseliş\" göstergesi aynı bilgiyi taşıyor", "No gain (Rules + PU AUC −0.005, recall −2.4 points, n.s.); the existing \"rise from the low\" indicator carries the same information"], date: "2026-11-17" },
  { idea: ["Yeni yıllara daha çok ağırlık", "More weight on recent years"], ok: false, eff: ["Kazanç yok (Kural + PU AUC −0,005, anlamsız); eski vakalar da bilgi taşıyor", "No gain (Rules + PU AUC −0.005, n.s.); older cases carry information too"], date: "2026-11-17" },
  { idea: ["Doğrudan sıralama için eğitim (lambdarank)", "Training directly for ranking (lambdarank)"], ok: false, eff: ["Anlamlı kötüleşme (yakalama −5,7 puan)", "Significantly worse (recall −5.7 points)"], date: "2026-11-17" },
  { idea: ["Ayarları yalnız geçmiş yıllarla seçmek", "Tuning settings on past years only"], ok: false, eff: ["PU tek başına biraz iyi (AUC +0,005), Kural + PU'da fark yok; ayarlar korundu", "PU alone slightly better (AUC +0.005), no change for Rules + PU; settings kept"], date: "2026-11-17" },
  { idea: ["PU modelinin açıklamaları (SHAP)", "Explaining the PU model (SHAP)"], ok: true, eff: ["Model en çok halka açık devir hızına ve dipten yükselişe bakıyor; kurallardan farklı bilgi kullanıyor. \"Neden şüpheli?\" paneline eklendi", "The model relies most on free-float turnover and the rise from the low; it uses different information than the rules. Added to the \"Why suspicious?\" panel"], date: "2026-11-17" },
  { idea: ["Boş alarmların incelenmesi (SPK kararı olmayan ilk 10 hisseleri)", "Reviewing false alarms (top-10 stocks without an SPK decision)"], ok: true, eff: ["Veri hatası yok; boş alarmlar da olağan dışı hareketler (üçte biri yükseliş + çöküş, rastgelede %5). İsabet oranı alt sınır", "No data errors; false alarms are unusual moves too (a third rise then crash, 5% at random). Precision is a lower bound"], date: "2026-11-17" },
  { idea: ["Dönemi bilinmeyen vakaları tahminle etiketleme", "Estimating periods for cases without a stated period"], ok: false, eff: ["6 aylık pencereye göre kazanç yok; yalnızca belgelendi", "No gain over the 6-month window; documented only"], date: "2026-10-24" },
];

/** Denenen diğer modeller (MEL-81…87, MEL-32): scripts/alt_models.py → export_web.py --alt → alt_models.json. */
interface AltRow {
  key: string; tr: string; en: string; group: "tek" | "birlesim"; issue: string; ref: string;
  auc: number; rec: number; rnd: number; prec10: number;
  dAuc: number; dAucLo: number; dAucHi: number; dAucSig: boolean; dRec: number; dRecLo: number; dRecHi: number; dRecSig: boolean;
}
const REF_NAMES: Record<string, [string, string]> = {
  "3b_pu_bagging": ["PU bagging", "PU bagging"], "4_kural_pu": ["ana model", "main model"],
  "2_lightgbm": ["LightGBM", "LightGBM"], "1_iforest": ["Isolation Forest", "Isolation Forest"],
};

function AltModels() {
  const f = useT();
  const { data } = useJson<AltRow[]>("alt_models.json");
  if (!data?.length) return null;
  const diff = (d: number, lo: number, hi: number, sig: boolean, digits: number, pct: boolean) => {
    const v = pct ? `${d >= 0 ? "+" : "−"}${f.num(Math.abs(d) * 100, 1)}` : `${d >= 0 ? "+" : "−"}${f.num(Math.abs(d), digits)}`;
    const ci = pct ? `[${f.num(lo * 100, 1)}, ${f.num(hi * 100, 1)}]` : `[${f.num(lo, digits)}, ${f.num(hi, digits)}]`;
    return <span title={ci} style={{ fontWeight: sig ? 700 : 400, color: sig ? (d > 0 ? "var(--teal)" : "var(--red, #c0392b)") : undefined }}>{v}{sig ? " *" : ""}</span>;
  };
  const table = (grp: AltRow["group"], cap: string) => (
    <div className="tbl-wrap">
      <table className="t num">
        <caption className="sr">{cap}</caption>
        <thead><tr>
          <th scope="col">Model</th><th scope="col">AUC</th><th scope="col">{f.L("İlk 20'de yakalama", "Caught in top 20")}</th>
          <th scope="col">{f.L("Rastgele", "Random")}</th><th scope="col">{f.L("İlk 10 isabeti", "Top-10 precision")}</th>
          <th scope="col">{f.L("Karşılaştırılan", "Compared with")}</th><th scope="col">{f.L("AUC farkı", "AUC diff.")}</th><th scope="col">{f.L("Yakalama farkı (puan)", "Recall diff. (pts)")}</th>
        </tr></thead>
        <tbody>
          {data.filter((x) => x.group === grp).map((x) => (
            <tr key={x.key}>
              <td style={{ fontWeight: 600 }}>{f.L(x.tr, x.en)} <span className="faint" style={{ fontSize: 11, fontWeight: 400 }}>{x.issue}</span></td>
              <td>{f.num(x.auc, 3)}</td><td>{f.pct(x.rec)}</td><td>{f.pct(x.rnd)}</td><td>{f.pct(x.prec10, 1)}</td>
              <td className="muted">{f.L(...(REF_NAMES[x.ref] ?? [x.ref, x.ref]))}</td>
              <td>{diff(x.dAuc, x.dAucLo, x.dAucHi, x.dAucSig, 3, false)}</td>
              <td>{diff(x.dRec, x.dRecLo, x.dRecHi, x.dRecSig, 1, true)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
  return (
    <section className="card" aria-labelledby="alt-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <h2 id="alt-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("Denenen diğer modeller · 2017–2026", "Other models tried · 2017–2026")}</h2>
        <p style={{ fontSize: 14, lineHeight: 1.55 }} className="muted">{f.L(
          "Hepsi aynı dürüst testle: her yıl yalnız geçmiş verilerle eğitildi, ayarlar sonuçlara bakılmadan sabitlendi. Hiçbiri ana modelin (Kural + PU) ilk 20 yakalamasını anlamlı biçimde geçmedi; birkaçı AUC'de küçük artış gösterdi ama listenin üstü iyileşmediği için ana model korundu.",
          "All with the same honest test: each year trained on past data only, settings fixed before seeing results. None significantly beat the main model's (Rules + PU) top-20 recall; a few gave small AUC gains, but the main model was kept because the top of the list did not improve.")}</p>
      </div>
      <h3 style={{ fontSize: 15, fontWeight: 600 }}>{f.L("Tek başına", "On their own")}</h3>
      {table("tek", f.L("Denenen modeller, tek başına", "Models tried, on their own"))}
      <h3 style={{ fontSize: 15, fontWeight: 600 }}>{f.L("Kurallarla birleşince (ana modelle karşılaştırma)", "Combined with the rules (vs the main model)")}</h3>
      {table("birlesim", f.L("Kurallarla birleşimler", "Ensembles with the rules"))}
      <p style={{ fontSize: 12, lineHeight: 1.55 }} className="faint">{f.L(
        "Fark: modelin değeri − karşılaştırılan modelin değeri, aynı vakalarda. * ve kalın: %95 eşli bootstrap güven aralığı 0'ı içermiyor (anlamlı); aralık için üzerine gelin. Aralığı 0'a çok yakın (sınırda) sonuçlar bootstrap tekrarına göre anlamlı / anlamsız arasında değişebilir. Ayrıntılar ve tasarımlar: docs/yorum_v2.md ve deneme günlüğü.",
        "Difference: model − comparison model, on the same cases. * and bold: the 95% paired-bootstrap interval excludes 0 (significant); hover for the interval. Borderline results (interval touching 0) can flip between significant and not across bootstrap runs. Details and designs: docs/yorum_v2.md and the experiment log.")}</p>
    </section>
  );
}

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

      <AltModels />

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

      {/* Sayılar: scripts/false_alarms.py → docs/bos_alarmlar.md, elle örnek → docs/yorum_v2.md (MEL-16) */}
      <section className="card" aria-labelledby="fa-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <h2 id="fa-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("SPK kararı olmayan alarmlar: olağan dışı hareket", "Alarms without an SPK decision: unusual moves")}</h2>
          <p style={{ fontSize: 14, lineHeight: 1.55 }} className="muted">
            {f.L("Haftalık ilk 10'daki hisselerin çoğu için SPK kararı yok. Bunlar boş mu? Hayır: fiyat davranışı SPK vakalarına çok benziyor, rastgele hisselerden ise çok farklı. Bu hisseler SPK kararı olmasa da \"olağan dışı hareket\" olarak etiketlenebilir; ancak manipülasyon olduklarını yalnızca SPK kararı gösterebilir.",
                 "Most stocks in the weekly top 10 have no SPK decision. Are they empty alarms? No: their price behaviour closely resembles SPK cases and differs sharply from random stocks. They can be labelled \"unusual moves\" even without an SPK decision; only an SPK decision can show they were manipulation.")}
          </p>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(380px, 100%), 1fr))", gap: 28 }}>
          <div className="tbl-wrap">
            <table className="t num">
              <thead><tr><th scope="col"></th><th scope="col">{f.L("SPK vakası", "SPK case")}</th><th scope="col">{f.L("SPK kararı yok", "No SPK decision")}</th><th scope="col">{f.L("Rastgele hisse", "Random stock")}</th></tr></thead>
              <tbody>
                {[
                  [f.L("Son 2 ayda yükseliş (medyan)", "Rise over the past 2 months (median)"), "%62", "%60", "%12"],
                  [f.L("Borsa şirketten açıklama istedi", "Exchange asked the company to explain"), "%43", "%32", "%5"],
                  [f.L("Sonra: yükseliş + çöküş", "Afterwards: rise then crash"), "%40", "%33", "%5"],
                  [f.L("Veri hatası", "Data error"), "%0", "%0", "%0"],
                ].map((r) => (
                  <tr key={r[0]}><th scope="row" style={{ fontWeight: 500 }}>{r[0]}</th>{r.slice(1).map((v, i) => <td key={i}>{f.lang === "en" ? v.replace("%", "") + "%" : v}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <strong style={{ fontSize: 15, fontWeight: 600 }}>{f.L("Tek tek incelenen 30 örnek (hiç SPK kaydı olmayan hisseler)", "30 examples reviewed one by one (stocks with no SPK record)")}</strong>
            {[
              [14, f.L("Haber yokken sert yükseliş, ardından çöküş", "Sharp rise without news, then a crash")],
              [9, f.L("Somut şirket haberiyle açıklanabilir", "Explained by concrete company news")],
              [3, f.L("Yeni halka arz", "Recent IPO")],
              [3, f.L("Kalıcı yükseliş", "Lasting rise")],
              [1, f.L("Çok az hissesi işlem gören büyük şirket", "Large company with a tiny free float")],
            ].map(([n, t]) => (
              <div key={t as string} style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 120px 24px", gap: 10, alignItems: "center", fontSize: 14 }}>
                <span>{t}</span>
                <span style={{ height: 10, borderRadius: 5, background: "var(--line)", overflow: "hidden" }}>
                  <span style={{ display: "block", height: "100%", width: `${((n as number) / 14) * 100}%`, background: "var(--teal)" }} />
                </span>
                <span style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>{n}</span>
              </div>
            ))}
          </div>
        </div>
        <p style={{ fontSize: 12 }} className="faint">
          {f.L("Kural + PU, her haftanın en şüpheli 10 hissesi, 2017–2026; aynı hissenin art arda alarmları tek dönem sayıldı (2.393 dönem). \"Sonra\" satırı geriye bakarak ölçülür, sistem bunu alarm anında bilemez. Şirket adları bilerek verilmez.",
               "Rules + PU, each week's 10 most suspicious stocks, 2017–2026; consecutive alarms on the same stock counted as one episode (2,393 episodes). The \"afterwards\" row is measured in hindsight; the system cannot know it at alarm time. Company names are deliberately withheld.")}
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
              {[...LOG].sort((a, b) => (a.date < b.date ? -1 : 1)).map((l) => (
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
