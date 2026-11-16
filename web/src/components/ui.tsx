import type { ReactNode } from "react";
import { getResult, RULE_KEYS, type Index, type RuleVals, type SpkLink } from "../data";
import { useT } from "../i18n";
import { Check, Clock, Dash, Info, Tri } from "./Icons";

export const MODEL_NAMES: Record<string, [string, string]> = {
  random: ["Rastgele", "Random"],
  "0a_kural": ["Kurallar", "Rules"],
  "1_iforest": ["Isolation Forest", "Isolation Forest"],
  "2_lightgbm": ["LightGBM", "LightGBM"],
  "3a_pu_agirlikli": ["PU öğrenme (ağırlıklı)", "PU learning (weighted)"],
  "3b_pu_bagging": ["PU öğrenme (bagging)", "PU learning (bagging)"],
  "4_kural_pu": ["Kural + PU", "Rules + PU"],
};

export const DECISION_TYPES: Record<string, [string, string]> = {
  suc_duyurusu: ["Suç duyurusu", "Criminal complaint"],
  idari_para_cezasi: ["İdari para cezası", "Administrative fine"],
  islem_yasagi: ["İşlem yasağı", "Trading ban"],
  diger_tedbir: ["Tedbir", "Precautionary measure"],
  piyasa_tedbiri: ["Piyasa tedbiri", "Market measure"],
};

// ---- kural göstergeleri: kısa etiket, düz cümle ----
type RuleText = { label: [string, string]; chip: (v: number, f: Fmt) => string; sentence: (v: number, f: Fmt) => string; fmt: (v: number, f: Fmt) => string };
type Fmt = ReturnType<typeof useT>;
// Türkçe sayı ekleri: "10 günün 7'si", "10 günün 7'sinde"
const TR_POSS: Record<number, string> = { 6: "'sı", 7: "'si", 8: "'i", 9: "'u", 10: "'u" };
const TR_LOC: Record<number, string> = { 6: "'sında", 7: "'sinde", 8: "'inde", 9: "'unda", 10: "'unda" };

export const RULE_TEXT: Record<(typeof RULE_KEYS)[number], RuleText> = {
  excess_ret_20: {
    label: ["Endeks üstü getiri", "Excess return"],
    fmt: (v, f) => f.pct(v),
    chip: (v, f) => f.L(`20 günde endeks +${f.pct(v)}`, `+${f.pct(v)} vs index (20d)`),
    sentence: (v, f) => f.L(`Son 20 günde endeksin ${f.pct(v)} üzerinde getiri.`, `Return ${f.pct(v)} above the index over 20 days.`),
  },
  value_ratio_5d_60: {
    label: ["Hacim artışı", "Volume surge"],
    fmt: (v, f) => f.times(v),
    chip: (v, f) => f.L(`Hacim ${f.times(v)}`, `Volume ${f.times(v)}`),
    sentence: (v, f) => f.L(`Son 5 günün işlem hacmi, son 60 günün normalinin ${f.num(v, 1)} katı.`, `5-day trading value is ${f.times(v)} its 60-day normal.`),
  },
  close_loc_5: {
    label: ["Tepede kapanış", "Closes at high"],
    fmt: (v, f) => f.pct(v),
    chip: (_v, f) => f.L("Kapanışlar tepede", "Closes near high"),
    sentence: (v, f) => f.L(`Son 5 günde kapanışlar gün içi aralığın ${f.pct(v)} seviyesinde, tepeye yakın.`, `Over 5 days, closes sit at ${f.pct(v)} of the daily range, near the high.`),
  },
  limit_up_10: {
    label: ["Tavan serisi", "Limit-up days"],
    fmt: (v) => String(Math.round(v)),
    chip: (v, f) => f.L(`10 günde ${Math.round(v)} tavan`, `${Math.round(v)} limit-ups in 10d`),
    sentence: (v, f) => f.L(`Son 10 günde fiyat ${Math.round(v)} kez tavan yaptı.`, `The price hit the daily limit ${Math.round(v)} times in 10 days.`),
  },
  float_turnover_ratio_60: {
    label: ["Halka açık devir", "Free-float turnover"],
    fmt: (v, f) => f.times(v),
    chip: (v, f) => f.L(`Halka açık devir ${f.times(v)}`, `Float turnover ${f.times(v)}`),
    sentence: (v, f) => f.L(`Halka açık paylarda devir hızı normalinin ${f.num(v, 1)} katı.`, `Free-float turnover is ${f.times(v)} its normal level.`),
  },
  up_days_10: {
    label: ["Kesintisiz yükseliş", "Steady rise"],
    fmt: (v) => `${Math.round(v)}/10`,
    chip: (v, f) => f.L(`10 günün ${Math.round(v)}${TR_POSS[Math.round(v)] ?? "'i"} yükseliş`, `${Math.round(v)} of 10 days up`),
    sentence: (v, f) => f.L(`Son 10 işlem gününün ${Math.round(v)}${TR_LOC[Math.round(v)] ?? "'inde"} fiyat yükseldi.`, `The price rose on ${Math.round(v)} of the last 10 trading days.`),
  },
};

/** Eşiği geçen kurallar, eşiğe oranla büyükten küçüğe. */
export function firedRules(vals: RuleVals | undefined, thr: Record<string, number>) {
  if (!vals) return [];
  return RULE_KEYS.map((k, i) => ({ k, v: vals[i], ratio: vals[i] == null ? 0 : (vals[i] as number) / thr[k] }))
    .filter((x) => x.v != null && x.ratio >= 1)
    .sort((a, b) => b.ratio - a.ratio);
}

export function ReasonChips({ vals, thr, max = 3 }: { vals: RuleVals | undefined; thr: Record<string, number>; max?: number }) {
  const f = useT();
  const fired = firedRules(vals, thr);
  if (!fired.length) return <span className="chip faint">{f.L("Kural yok · model örüntüsü", "No rule · model pattern")}</span>;
  return <>{fired.slice(0, max).map((x) => <span className="chip" key={x.k}>{RULE_TEXT[x.k].chip(x.v as number, f)}</span>)}</>;
}

/** "Neden şüpheli?": her kural göstergesinin eşiğe oranı + eşiği geçenler için düz cümleler. */
export function WhyPanel({ vals, thr, compact = false }: { vals: RuleVals | undefined; thr: Record<string, number>; compact?: boolean }) {
  const f = useT();
  const fired = firedRules(vals, thr);
  const items = RULE_KEYS.map((k, i) => ({ k, v: vals?.[i] ?? null }))
    .map((x) => ({ ...x, ratio: x.v == null ? 0 : Math.max(0, x.v / thr[x.k]) }))
    .sort((a, b) => b.ratio - a.ratio);
  const shown = compact ? items.slice(0, 4) : items;
  const col = compact ? "120px 1fr 44px" : "150px 1fr 52px";
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: compact ? 10 : 14 }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {shown.map((x) => (
          <div key={x.k} style={{ display: "grid", gridTemplateColumns: col, gap: 10, alignItems: "center", fontSize: 13 }}>
            <span className="muted">{f.L(...RULE_TEXT[x.k].label)}</span>
            <span className="bar" style={{ height: compact ? 10 : 12, borderRadius: 3 }}
                  role="img" aria-label={`${f.L(...RULE_TEXT[x.k].label)}: ${f.pct(Math.min(x.ratio, 1))} ${f.L("eşik", "of threshold")}`}>
              <span className={x.ratio >= 1 ? "" : "rand"} style={{ width: `${Math.min(x.ratio, 1) * 100}%`, borderRadius: 3 }} />
            </span>
            <span style={{ textAlign: "right", fontWeight: 600 }}>{x.v == null ? "—" : RULE_TEXT[x.k].fmt(x.v, f)}</span>
          </div>
        ))}
      </div>
      {fired.length > 0 ? (
        <ul style={compact
          ? { margin: "4px 0 0", paddingLeft: 18, display: "flex", flexDirection: "column", gap: 6, fontSize: 13, lineHeight: 1.5 }
          : { margin: 0, padding: "14px 16px 14px 34px", borderRadius: 10, background: "var(--surface-2)", display: "flex", flexDirection: "column", gap: 8, fontSize: 14, lineHeight: 1.5 }}>
          {fired.map((x) => <li key={x.k}>{RULE_TEXT[x.k].sentence(x.v as number, f)}</li>)}
        </ul>
      ) : (
        <p style={{ fontSize: 13 }} className="muted">{f.L("Bu hafta hiçbir kural eşiği aşılmadı; sıra, PU modelinin öğrendiği örüntüden geliyor.", "No rule threshold was crossed this week; the rank comes from the pattern the PU model learned.")}</p>
      )}
      <p style={{ fontSize: 12 }} className="faint">
        {f.L("Çubuk, göstergenin kural eşiğine oranıdır (dolu ve yeşil = eşik aşıldı). Bunlar kural göstergeleridir; PU modelinin ayrıntılı katkıları değildir. Bir suçlama değildir.",
             "Each bar is the indicator relative to its rule threshold (full and green = crossed). These are rule indicators, not detailed PU model contributions. Not an accusation.")}
      </p>
    </div>
  );
}

export function SpkBadge({ link, days, short = false }: { link: SpkLink; days: number | null; short?: boolean }) {
  const { L } = useT();
  if (link === "in") {
    const txt = short ? L("SPK dönemi", "SPK period")
      : days != null && days >= 0 ? L(`SPK dönemi · ${days} gün sonra karar`, `SPK period · decision ${days} days later`)
      : L("SPK dönemi · karar önceden açıklanmıştı", "SPK period · decision already public");
    return <span className="badge b-green"><Check size={12} />{txt}</span>;
  }
  if (link === "later") {
    const txt = short ? L("2 yılda karar", "Decision ≤2y") : L(`${days} gün sonra SPK kararı`, `SPK decision ${days} days later`);
    return <span className="badge b-amber"><Clock size={12} />{txt}</span>;
  }
  return <span className="badge b-gray" aria-label={L("SPK kararı yok", "No SPK decision")}><Dash size={12} />—</span>;
}

export function SpkLegend() {
  const { L } = useT();
  const s = { display: "inline-flex", gap: 6, alignItems: "center" } as const;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 12, fontSize: 12, color: "var(--muted)" }}>
      <span style={s}><span className="badge b-green" style={{ padding: "2px 6px" }}><Check size={10} /></span>{L("SPK'nın yazdığı dönemde", "Inside SPK-stated period")}</span>
      <span style={s}><span className="badge b-amber" style={{ padding: "2px 6px" }}><Clock size={10} /></span>{L("2 yıl içinde karar (dönem yazmıyor)", "Decision within 2 years (no period)")}</span>
      <span style={s}><span className="badge b-gray" style={{ padding: "2px 6px" }}><Dash size={10} /></span>{L("SPK kararı yok", "No SPK decision")}</span>
    </div>
  );
}

export function Waffle({ n, cls, label }: { n: number; cls: "t1" | "g1"; label: string }) {
  return (
    <div className="w" role="img" aria-label={label}>
      {Array.from({ length: 100 }, (_, i) => <i key={i} className={i < Math.round(n) ? cls : ""} />)}
    </div>
  );
}

export function ChartLegend({ alarm = true, decision = true, threshold = false, alarmLabel }: { alarm?: boolean; decision?: boolean; threshold?: boolean; alarmLabel?: string }) {
  const { L } = useT();
  return (
    <div className="legend">
      <span><span className="sw-band" />{L("SPK'nın belirttiği manipülasyon dönemi", "Manipulation period stated by SPK")}</span>
      {decision && <span><Tri />{L("SPK kararı", "SPK decision")}</span>}
      {alarm && <span><span className="sw-line" />{alarmLabel ?? L("Sistemin ilk alarmı (ilk 20)", "System's first alarm (top 20)")}</span>}
      {threshold && <span><span className="sw-dash" />{L("İlk 20 eşiği", "Top-20 threshold")}</span>}
    </div>
  );
}

export function Note({ children }: { children: ReactNode }) {
  return <p style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 13 }} className="muted"><Info />{children}</p>;
}

export function Loading({ error }: { error?: string }) {
  const { L } = useT();
  if (error) return (
    <div className="card" style={{ padding: 24 }}>
      <p style={{ fontWeight: 600 }}>{L("Veri yüklenemedi", "Could not load data")}</p>
      <p className="muted" style={{ fontSize: 14, marginTop: 6 }}>
        {L("Önce veri dosyalarını üretin: ", "Generate the data files first: ")}<code>python scripts/export_web.py</code> ({error})
      </p>
    </div>
  );
  return <p className="loading">{L("Yükleniyor…", "Loading…")}</p>;
}

/** Genel bakış ve Sonuçlar'daki 4 ana KPI kartı. */
export function KpiCards({ idx, period = "2017–2026" }: { idx: Index; period?: string }) {
  const f = useT();
  const r = getResult(idx.results, "4_kural_pu", period);
  if (!r) return null;
  const tm = idx.timing;
  const months = Math.round(tm.medSanction / 30.4);
  const main = period === "2017–2026";
  const cardS = { padding: 22, display: "flex", flexDirection: "column", gap: 14 } as const;
  const cap = { fontSize: 14, fontWeight: 500, color: "var(--muted)" } as const;
  const sub = { fontSize: 13, color: "var(--faint)" } as const;
  const twoBars = (a: number, b: number, label: string) => (
    <div role="img" aria-label={label} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <span className="bar" style={{ height: 6, borderRadius: 3 }}><span style={{ width: `${a * 100}%` }} /></span>
      <span className="bar" style={{ height: 6, borderRadius: 3 }}><span className="rand" style={{ width: `${b * 100}%` }} /></span>
    </div>
  );
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: 16 }}>
      <div className="card" style={cardS}>
        <p style={cap}>{f.L("Yakalanan vaka (ilk 20)", "Cases caught (top 20)")}</p>
        <p className="kpi-num">{f.pct(r.rec)}</p>
        {twoBars(r.rec, r.rnd, f.L(`Sistem ${f.pct(r.rec)}, rastgele ${f.pct(r.rnd)}`, `System ${f.pct(r.rec)}, random ${f.pct(r.rnd)}`))}
        <p style={sub}>{f.L(`rastgele ${f.pct(r.rnd)} · ${f.num(r.rec / r.rnd, 1)} kat`, `random ${f.pct(r.rnd)} · ${f.num(r.rec / r.rnd, 1)}×`)}</p>
      </div>
      <div className="card" style={cardS}>
        <p style={cap}>{f.L("Fiyat zirvesinden önce", "Before the price peak")}</p>
        <p className="kpi-num">{f.pct(r.prePeak)}</p>
        {twoBars(r.prePeak, r.prePeakRnd, f.L(`Sistem ${f.pct(r.prePeak)}, rastgele ${f.pct(r.prePeakRnd)}`, `System ${f.pct(r.prePeak)}, random ${f.pct(r.prePeakRnd)}`))}
        <p style={sub}>{f.L(`rastgele ${f.pct(r.prePeakRnd)} · ${f.num(r.prePeak / r.prePeakRnd, 1)} kat`, `random ${f.pct(r.prePeakRnd)} · ${f.num(r.prePeak / r.prePeakRnd, 1)}×`)}</p>
      </div>
      {main ? (
        <div className="card" style={cardS}>
          <p style={cap}>{f.L("SPK'nın ilk cezasından önce", "Before SPK's first sanction")}</p>
          <p className="kpi-num">{months} <span style={{ fontSize: 24, fontWeight: 500, color: "var(--muted)" }}>{f.L("ay", "mo")}</span></p>
          <div role="img" aria-label={f.L(`Medyan: ilk alarm, SPK ilk cezasından ${months} ay önce`, `Median: first alarm ${months} months before SPK's first sanction`)} style={{ position: "relative", height: 18 }}>
            <span style={{ position: "absolute", left: 0, right: 0, top: 8, height: 2, background: "var(--line)" }} />
            <span style={{ position: "absolute", left: "8%", top: 3, width: 12, height: 12, borderRadius: "50%", background: "var(--red)" }} />
            <span style={{ position: "absolute", left: "8%", right: "8%", top: 8, height: 2, background: "var(--teal)" }} />
            <span style={{ position: "absolute", right: "8%", top: 2, width: 0, height: 0, borderLeft: "7px solid transparent", borderRight: "7px solid transparent", borderBottom: "12px solid var(--text)" }} />
          </div>
          <p style={sub}>{f.L(`medyan · ilk tedbir/karardan ${Math.round(tm.medFirst)} gün önce`, `median · ${Math.round(tm.medFirst)} days before the first measure`)}</p>
        </div>
      ) : (
        <div className="card" style={cardS}>
          <p style={cap}>{f.L("Değerlendirilen vaka", "Evaluated cases")}</p>
          <p className="kpi-num">{r.nCases}</p>
          <p style={sub}>{f.L(`dönemi SPK kararında yazan vakalar · ${period}`, `cases with a stated period · ${period}`)}</p>
        </div>
      )}
      <div className="card" style={cardS}>
        <p style={cap}>{f.L("Ayırt etme gücü (AUC)", "Discrimination (AUC)")}</p>
        <p className="kpi-num">{f.num(r.auc, 2)}</p>
        <div role="img" aria-label={`AUC ${f.num(r.auc, 2)}`} style={{ position: "relative", height: 18 }}>
          <span style={{ position: "absolute", left: 0, right: 0, top: 7, height: 4, borderRadius: 2, background: "var(--surface-2)" }} />
          <span style={{ position: "absolute", left: 0, width: `${Math.max(0, (r.auc - 0.5) / 0.5) * 100}%`, top: 7, height: 4, borderRadius: 2, background: "var(--teal)" }} />
          <span style={{ position: "absolute", left: 0, top: 1, width: 2, height: 16, background: "var(--rand)" }} />
        </div>
        <p style={sub}>{f.L(`0,5 = rastgele · %95 GA ${f.num(r.aucLo, 2)}–${f.num(r.aucHi, 2)}`, `0.5 = random · 95% CI ${f.num(r.aucLo, 2)}–${f.num(r.aucHi, 2)}`)}</p>
      </div>
    </div>
  );
}
