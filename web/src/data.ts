// Veri sözleşmesi: scripts/export_web.py → public/data/*.json
import { useEffect, useState } from "react";

export const RULE_KEYS = [
  "excess_ret_20", "value_ratio_5d_60", "close_loc_5", "limit_up_10", "float_turnover_ratio_60", "up_days_10",
] as const;
export type RuleVals = (number | null)[]; // RULE_KEYS sırasıyla
export type SpkLink = "" | "in" | "later";
/** PU modelinin SHAP katkıları: [gösterge sırası (Index.shapFeats), log-odds katkı, göstergenin değeri] */
export type Shap = [number, number, number | null][];
/** [hisse, sıra, yüzdelik (0–1), kural göstergeleri, SPK bağlantısı, karara kalan gün, PU katkıları] */
export type ListRow = [string, number, number, RuleVals, SpkLink, number | null, Shap?];

export interface WeekEntry { end: string; start: string; n: number; inPeriod: number; lists: Record<string, ListRow[]> }
export interface WeekMeta { end: string; start: string; n: number }
export interface StockMeta { t: string; name: string; nDec: number; nCore: number; scored: boolean }
export interface ResultRow {
  model: string; period: string; auc: number; aucLo: number; aucHi: number; nCases: number;
  rec: number; rnd: number; lift: number; prePeak: number; prePeakRnd: number; lead: number;
  prec10: number; base10: number; plift10: number; rec10: number; rnd10: number; rec50: number; rnd50: number;
}
export interface Timing {
  nCaught: number; nCases: number; first: number[]; sanction: number[];
  medFirst: number; medSanction: number; pctBefore: number; leadMed: number;
}
export interface CaseStudy {
  id: string; ticker: string; start: string; end: string; caught: boolean; firstAlert: string | null;
  leadDays: number | null; pRandom: number; bestRank: number; daysToFirstSpk: number | null;
  daysToSanction: number | null; peak: string | null; startPx: number; peakPx: number; minAfter: number | null;
  firstSpk: string | null; firstSanction: string | null;
}
export interface Index {
  generated: string; models: string[]; rules: Record<string, number>; top: number; shapFeats?: string[];
  weeks: WeekMeta[]; stocks: StockMeta[]; results: ResultRow[]; timing: Timing; cases: CaseStudy[];
  counts: { cases: number; decisions: number; kap: number; bulletinYears: [number, number];
            minWeek: number; maxWeek: number; meanWeek: number };
}
export interface Decision { date: string; type: string; ref: string | null; tier: number; pStart: string | null; pEnd: string | null }
export interface StockCase { id: string; start: string; end: string; known: boolean; core: boolean; first: string }
/** [hafta sonu (cuma), sıra, o hafta puanlanan hisse, ...6 kural göstergesi] */
export type RankRow = [string, number, number, ...(number | null)[]];
export interface StockData {
  ticker: string; name: string;
  prices: { d: string[]; c: (number | null)[]; v: (number | null)[] };
  ranks: RankRow[]; decisions: Decision[]; cases: StockCase[];
  shap?: Record<string, Shap>; // hafta sonu → PU katkıları (yalnızca ilk 50'ye giren haftalar)
  /** [yayın günü, konu, grup, bildirim no, özet (yalnız haber / söylenti / fiyat açıklaması)] */
  kap: [string, string, "news" | "price" | "rumor" | "other", number, string?][];
}

const cache = new Map<string, Promise<unknown>>();

export function fetchJson<T>(path: string): Promise<T> {
  if (!cache.has(path)) {
    cache.set(path, fetch(`/data/${path}`).then((r) => {
      if (!r.ok) throw new Error(`${path}: ${r.status}`);
      return r.json();
    }).catch((e) => { cache.delete(path); throw e; }));
  }
  return cache.get(path) as Promise<T>;
}

export type Loadable<T> = { data?: T; error?: string; loading: boolean };

export function useJson<T>(path: string | null): Loadable<T> {
  const [state, setState] = useState<Loadable<T>>({ loading: !!path });
  useEffect(() => {
    if (!path) { setState({ loading: false }); return; }
    let alive = true;
    setState((s) => ({ data: s.data, loading: true }));
    fetchJson<T>(path).then(
      (data) => alive && setState({ data, loading: false }),
      (e: Error) => alive && setState({ error: e.message, loading: false }),
    );
    return () => { alive = false; };
  }, [path]);
  return state;
}

export const useIndex = () => useJson<Index>("index.json");
export const useStock = (t: string | null) => useJson<StockData>(t ? `stocks/${t}.json` : null);

/** Yeni halka arzlar (MEL-92): hisse → [ilk işlem günü, 60. işlem günü | null (henüz dolmadı)]. */
export type IpoMap = Record<string, [string, string | null]>;
export const useIpo = () => useJson<IpoMap>("ipo.json");
/** Hafta (cuma bitişli), hissenin ilk 60 işlem gününe değiyor mu? */
export function isNewIpo(ipo: IpoMap | undefined, t: string, weekEnd: string): boolean {
  const v = ipo?.[t];
  if (!v) return false;
  return weekEnd >= v[0] && (v[1] === null || addDays(weekEnd, -4) <= v[1]);
}

/** Zaman makinesi örnekleri: vakanın SPK döneminde en üst sıraya çıktığı hafta (Kural + PU). */
export const EXAMPLES = [
  { t: "IZFAS", week: "2018-06-01" },
  { t: "SANEL", week: "2019-05-17" },
  { t: "KGYO", week: "2022-07-15" },
];

// ---- yardımcılar ----
export const parseDate = (s: string) => new Date(s + "T00:00:00Z");
export const dayDiff = (a: string, b: string) => Math.round((parseDate(a).getTime() - parseDate(b).getTime()) / 864e5);
export const addDays = (s: string, n: number) => new Date(parseDate(s).getTime() + n * 864e5).toISOString().slice(0, 10);
/** Haftanın işlem günleri: pazartesi–cuma (dosyadaki başlangıç cumartesi). */
export const weekMonday = (end: string) => addDays(end, -4);

export function getResult(rows: ResultRow[], model: string, period = "2017–2026") {
  return rows.find((r) => r.model === model && r.period === period);
}

/** Bir vakanın ilk alarmı: dönemle çakışan haftalardan ilk 20'ye ilk girilen hafta. */
export function firstAlert(ranks: RankRow[], start: string, end: string, k = 20): RankRow | undefined {
  return ranks.find((r) => addDays(r[0], -6) <= end && r[0] >= start && r[1] <= k);
}
