import { getResult, useIndex } from "../data";
import { useT } from "../i18n";
import { Page } from "../components/Layout";
import { Dash, Shield, Warn } from "../components/Icons";
import { Loading } from "../components/ui";

const ArrowR = () => (
  <div aria-hidden="true" style={{ display: "flex", alignItems: "center", justifyContent: "center", color: "var(--faint)", flex: "none", width: 36 }}>
    <svg width="28" height="16" viewBox="0 0 28 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M2 8h22M18 2l6 6-6 6" /></svg>
  </div>
);

export default function Method() {
  const f = useT();
  const { data: idx, error } = useIndex();
  if (!idx) return <Page width="narrow"><Loading error={error} /></Page>;
  const c = idx.counts;
  const all = getResult(idx.results, "4_kural_pu", "2012–2026")!;
  const kap = f.L(`${Math.round(c.kap / 1000)} bin bildirim`, `${Math.round(c.kap / 1000)}k disclosures`);
  const col = (h: string, flex: string, nodes: React.ReactNode) => (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, flex }}><p style={{ fontSize: 11, fontWeight: 600 }} className="faint">{h}</p>{nodes}</div>
  );
  return (
    <Page width="narrow" gap={32}>
      <section style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 760 }}>
        <h1 className="h1">{f.L("Yöntem", "Method")}</h1>
        <p style={{ fontSize: 16, lineHeight: 1.6 }} className="muted">{f.L("Sistem, SPK'nın geçmişte karara bağladığı vakalardan öğrenir ve her hafta, yalnızca o güne kadar bilinen veriyle tüm hisseleri sıralar.",
                                                                                "The system learns from cases SPK has ruled on and, every week, ranks all stocks using only data known up to that day.")}</p>
      </section>

      <section className="card" aria-labelledby="flow-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 18 }}>
        <h2 id="flow-h" className="eyebrow">{f.L("Veri akışı", "Data flow")}</h2>
        <div role="img" aria-label={f.L("Akış: SPK bültenleri, KAP bildirimleri ve günlük piyasa verisi; etiketler ve göstergelere dönüşür; modeller şüphe skoru üretir; haftalık sıralama yapılır; sonuçlar SPK vakalarıyla değerlendirilir.",
                                         "Flow: SPK bulletins, KAP disclosures and daily market data become labels and indicators; models produce a suspicion score; stocks are ranked weekly; results are evaluated against SPK cases.")}
             style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "12px 0" }}>
          {col(f.L("VERİ KAYNAKLARI", "DATA SOURCES"), "1 1 190px", <>
            <div className="node" style={{ borderColor: "#f4a261" }}>{f.L("SPK bültenleri", "SPK bulletins")}<span>{c.bulletinYears.join("–")} · {c.cases} {f.L("vaka", "cases")}</span></div>
            <div className="node">{f.L("KAP bildirimleri", "KAP disclosures")}<span>{kap}</span></div>
            <div className="node">{f.L("Günlük piyasa verisi", "Daily market data")}<span>{f.L("fiyat, hacim, halka açıklık", "price, volume, free float")}</span></div>
          </>)}
          <ArrowR />
          {col(f.L("HAZIRLIK", "PREPARATION"), "1 1 170px", <>
            <div className="node">{f.L("Etiketler", "Labels")}<span>{f.L("SPK'nın belirttiği dönemler", "periods stated by SPK")}</span></div>
            <div className="node">{f.L("Göstergeler", "Indicators")}<span>{f.L("~60 gösterge, hisse × gün", "~60 features per stock-day")}</span></div>
          </>)}
          <ArrowR />
          {col(f.L("MODELLER", "MODELS"), "1 1 150px", <div className="node" style={{ background: "var(--teal-soft)", borderColor: "var(--teal)" }}>{f.L("Kural + PU", "Rules + PU")}<span>{f.L("şüphe skoru", "suspicion score")}</span></div>)}
          <ArrowR />
          {col(f.L("ÇIKTI", "OUTPUT"), "1 1 150px", <div className="node" style={{ borderColor: "#e63946" }}>{f.L("Haftalık sıralama", "Weekly ranking")}<span>{c.minWeek}–{c.maxWeek} {f.L("hisse · ilk 20", "stocks · top 20")}</span></div>)}
          <ArrowR />
          {col(f.L("KONTROL", "CHECK"), "1 1 150px", <div className="node">{f.L("Değerlendirme", "Evaluation")}<span>{f.L("SPK vakaları vs rastgele", "SPK cases vs random")}</span></div>)}
        </div>
      </section>

      <section aria-labelledby="steps-h" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <h2 id="steps-h" style={{ fontSize: 22, fontWeight: 600, letterSpacing: "-.01em" }}>{f.L("Dört adım", "Four steps")}</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
          {[
            [f.L("Etiketler", "Labels"), f.L("~1.000 SPK bülteni iki formatta ayrıştırılır (eski bültenlerde şirket unvanı hisse koduna çevrilir). Bir hisse-hafta yalnızca SPK'nın açıkça belirttiği dönemdeyse \"pozitif\" sayılır; geri kalan her şey \"bilinmiyor\"dur, temiz değil. Elle kontrolde etiket doğruluğu %94.",
                                             "~1,000 SPK bulletins are parsed in two formats (old ones name companies, which are matched to tickers). A stock-week is \"positive\" only inside a period SPK explicitly states; everything else is \"unknown\", not clean. Label precision on a manual check: 94%.")],
            [f.L("Göstergeler", "Indicators"), f.L("Endeks üstü getiri, hacim ve halka açık devir oranları, tavan serileri, yükseliş günleri, kapanış konumu ve KAP haber sayıları. Her gösterge yalnızca o güne kadarki veriyle hesaplanır; bu, birim testleriyle denetlenir.",
                                                   "Excess return, volume and free-float turnover ratios, limit-up streaks, up days, close location and KAP news counts. Every feature uses data up to that day only, checked by unit tests.")],
            [f.L("Modeller", "Models"), f.L("Uzman kuralları, Isolation Forest, LightGBM ve PU öğrenme (yalnızca pozitif + etiketsiz veriyle öğrenme) karşılaştırılır. En iyi sonuç, kural ve PU sıralarının eşit ağırlıklı ortalaması.",
                                            "Expert rules, Isolation Forest, LightGBM and PU learning (learning from positive + unlabeled data) are compared. Best: the equal-weight average of the rule and PU ranks.")],
            [f.L("Dürüst değerlendirme", "Honest evaluation"), f.L("Her yıl, yalnızca o yıldan önce bilinen veri ve SPK kararlarıyla eğitilen modelle puanlanır. Vaka bazında bootstrap güven aralıkları, eşli testler ve her metrik için rastgele taban.",
                                                                   "Each year is scored by a model trained only on data and SPK decisions known before it. Case-level bootstrap intervals, paired tests and a random baseline for every metric.")],
          ].map(([h, p], i) => (
            <div key={h} className="card" style={{ padding: 22, display: "flex", flexDirection: "column", gap: 10 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--teal-ink)" }}>0{i + 1}</span>
              <h3 style={{ fontSize: 17, fontWeight: 600 }}>{h}</h3>
              <p style={{ fontSize: 14, lineHeight: 1.55 }} className="muted">{p}</p>
            </div>
          ))}
        </div>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(420px, 100%), 1fr))", gap: 20 }}>
        <section className="card" aria-labelledby="rb-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14 }}>
          <h2 id="rb-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("Rastgele taban nedir?", "What is the random baseline?")}</h2>
          <p style={{ fontSize: 14, lineHeight: 1.55 }} className="muted">{f.L("Her hafta 20 hisseyi rastgele seçseydik, bir vakayı en az bir kez yakalama olasılığımız:", "If we picked 20 stocks at random every week, the chance of catching a case at least once is:")}</p>
          <p style={{ padding: 18, borderRadius: 10, background: "var(--surface-2)", fontSize: 26, fontWeight: 500, textAlign: "center" }}
             aria-label={f.L("1 eksi, t üzerinden çarpım, 1 eksi k bölü N t", "1 minus the product over t of 1 minus k over N t")}>
            1 − ∏<sub style={{ fontSize: 14 }}>t</sub> (1 − k / N<sub style={{ fontSize: 14 }}>t</sub>)
          </p>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, lineHeight: 1.6 }} className="muted">
            <li><strong style={{ color: "var(--text)" }}>k</strong> = {f.L("liste uzunluğu (20)", "list length (20)")}</li>
            <li><strong style={{ color: "var(--text)" }}>Nₜ</strong> = {f.L("t haftasında puanlanan hisse sayısı", "stocks scored in week t")}</li>
            <li><strong style={{ color: "var(--text)" }}>t</strong> = {f.L("SPK'nın belirttiği dönemdeki haftalar", "weeks inside the SPK-stated period")}</li>
          </ul>
          <p style={{ fontSize: 14, lineHeight: 1.55, paddingTop: 12, borderTop: "1px solid var(--line)" }}>
            <strong>{f.L("Örnek:", "Example:")}</strong>{f.L(" 4 hafta süren bir vaka, her hafta ~400 hisse: 1 − (1 − 20/400)⁴ ≈ ", " a 4-week case, ~400 stocks each week: 1 − (1 − 20/400)⁴ ≈ ")}<strong>{f.pct(0.185, 1)}</strong>.
            {f.L(" Uzun süren vakaları rastgele yakalamak da kolaylaşır; bu yüzden her sonucu bu tabanla karşılaştırıyoruz.", " Long cases are easy to hit by chance too, so every result is compared with this baseline.")}
          </p>
        </section>

        <section aria-labelledby="err-h" style={{ padding: 24, borderRadius: 12, border: "1px solid #f4a261", background: "var(--orange-soft)", display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, color: "var(--orange-ink)" }}><Warn size={22} /><h2 id="err-h" style={{ fontSize: 18, fontWeight: 600, color: "var(--text)" }}>{f.L("İlk hatamız", "Our first mistake")}</h2></div>
          <p style={{ fontSize: 15, lineHeight: 1.6 }}>{f.L("İlk sonucumuz etkileyiciydi (\"vakaların %40–47'si yakalandı\"), ama rastgeleden daha iyi değildi. Uzun süren vakaların rastgele bir listeye de kolayca girdiğini hesaba katmamıştık.",
                                                            "Our first result looked impressive (\"40–47% of cases caught\"), but it was no better than random. We had not accounted for long cases easily landing in a random list too.")}</p>
          <p style={{ fontSize: 15, lineHeight: 1.6 }}>{f.L("Sonucu geri çektik ve değerlendirmeyi baştan kurduk: her metrik artık aynı uzunlukta rastgele bir listeyle, vaka süresi dikkate alınarak karşılaştırılıyor. Bu sitedeki tüm sayılar yeni değerlendirmeden.",
                                                            "We retracted it and rebuilt the evaluation: every metric is now compared with a random list of the same length, accounting for case duration. All numbers on this site come from the new evaluation.")}</p>
          <p style={{ fontSize: 13, color: "var(--orange-ink)", fontWeight: 600 }}>{f.L("Ders: Taban olmadan verilen bir başarı oranı hiçbir şey söylemez.", "Lesson: a success rate without a baseline says nothing.")}</p>
        </section>
      </div>

      <section className="card" aria-labelledby="src-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14 }}>
        <h2 id="src-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("Veri kaynakları", "Data sources")}</h2>
        <div className="tbl-wrap">
          <table className="t">
            <thead><tr><th scope="col">{f.L("Kaynak", "Source")}</th><th scope="col">{f.L("İçerik", "Content")}</th><th scope="col">{f.L("Dönem", "Period")}</th><th scope="col">{f.L("Hacim", "Size")}</th></tr></thead>
            <tbody>
              {[
                [f.L("SPK haftalık bültenleri + yaptırım kayıtları", "SPK weekly bulletins + sanctions records"), f.L("Suç duyurusu, idari para cezası, işlem yasağı, tedbir kararları ve belirtilen dönemler", "Criminal complaints, fines, trading bans, measures and stated periods"), c.bulletinYears.join("–"), `${c.decisions} ${f.L("karar", "decisions")} · ${c.cases} ${f.L("vaka", "cases")}`],
                ["KAP", f.L("Özel durum açıklamaları, fiyat hareketi açıklamaları, finansal raporlar", "Material events, price-move statements, financial reports"), "2010–2026", kap],
                [f.L("Günlük piyasa verisi (İş Yatırım)", "Daily market data (İş Yatırım)"), f.L("Kapanış, VWAP, en yüksek/düşük, işlem hacmi, halka açıklık; işlemden kalkan hisseler dahil", "Close, VWAP, high/low, value traded, free float; delisted stocks included"), "2010–2026", `${c.minWeek}–${c.maxWeek} ${f.L("hisse / hafta", "stocks / week")}`],
                [f.L("Endeks verisi (İş Yatırım)", "Index data (İş Yatırım)"), f.L("BIST 100 (piyasa geneliyle karşılaştırma)", "BIST 100 (market comparison)"), "2010–2026", f.L("günlük", "daily")],
              ].map((r) => (
                <tr key={r[0]}><td style={{ fontWeight: 600, verticalAlign: "top", padding: "11px 12px" }}>{r[0]}</td><td className="muted" style={{ verticalAlign: "top", padding: "11px 12px" }}>{r[1]}</td><td style={{ verticalAlign: "top", padding: "11px 12px", whiteSpace: "nowrap" }}>{r[2]}</td><td style={{ verticalAlign: "top", padding: "11px 12px" }}>{r[3]}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(420px, 100%), 1fr))", gap: 20 }}>
        <section className="card" aria-labelledby="lim-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14 }}>
          <h2 id="lim-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("Sınırlılıklar", "Limitations")}</h2>
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              f.L("Yalnızca SPK'nın yakaladığı vakalar etiketli; yakalanmamış manipülasyon \"bilinmiyor\" olarak kalıyor.", "Only cases SPK caught are labelled; uncaught manipulation stays \"unknown\"."),
              f.L(`Yalnızca kararında dönem yazan vakalar değerlendirilebiliyor (2012–2026'da ${all.nCases} vaka).`, `Only cases whose decision states a period can be evaluated (${all.nCases} cases in 2012–2026).`),
              f.L("Günlük veri kullanılıyor; gün içi emir defteri ve hesap bazlı işlem verisi (AKD) yok. Yavaş, \"sessiz\" manipülasyonlar bu yüzden kaçabiliyor.", "Daily data only; no intraday order book or account-level trades (AKD), so slow, \"quiet\" manipulations can be missed."),
              f.L("Alarmların çoğu SPK vakası değil (ilk 10'da ~10/100). Sistem bir ön eleme aracıdır, karar değil.", "Most alarms are not SPK cases (~10 in 100 in the top 10). It is a triage tool, not a verdict."),
            ].map((t) => <li key={t} className="li"><Dash size={16} style={{ color: "var(--faint)" }} />{t}</li>)}
          </ul>
        </section>
        <section className="card" aria-labelledby="eth-h" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14 }}>
          <h2 id="eth-h" style={{ fontSize: 18, fontWeight: 600 }}>{f.L("Etik ilkeler", "Ethics")}</h2>
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              f.L("Skor bir suçlama değil, istatistiksel bir anomali sinyalidir.", "A score is a statistical anomaly signal, not an accusation."),
              f.L("SPK kararı olmayan hiçbir hisse \"manipüle edildi\" ya da \"temiz\" olarak etiketlenmez.", "No stock without an SPK decision is labelled \"manipulated\" or \"clean\"."),
              f.L("Gerçek haftalık listeler yalnızca yerelde gösterilir, internette yayımlanmaz.", "Real weekly lists are shown locally only and never published online."),
              f.L("SPK kararlarındaki kişisel veriler (isim, kimlik no) işlenmiş tablolarda tutulmaz.", "Personal data in SPK decisions (names, IDs) is never stored in processed tables."),
              f.L("Başarısız denemeler de başarılılar kadar açık raporlanır.", "Failed experiments are reported as openly as successful ones."),
            ].map((t) => <li key={t} className="li"><Shield size={16} style={{ color: "var(--teal-ink)" }} />{t}</li>)}
          </ul>
        </section>
      </div>
    </Page>
  );
}
