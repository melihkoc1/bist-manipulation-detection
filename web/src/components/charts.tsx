// Elle çizilen SVG grafikler (tasarımdaki ölçüler: 1200×620 üç panel).
import { useMemo, useRef, useState } from "react";
import { addDays, dayDiff, parseDate, type StockData } from "../data";
import { useT } from "../i18n";
import { DECISION_TYPES } from "./ui";

const ms = (s: string) => parseDate(s).getTime();

function niceTicks(lo: number, hi: number, n = 4): number[] {
  if (!(hi > lo)) return [lo];
  const raw = (hi - lo) / n;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) ?? raw;
  const out: number[] = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(10));
  return out;
}

const fmtTick = (v: number, lang: string) => {
  const d = v >= 100 ? 0 : v >= 10 ? 1 : v >= 1 ? 2 : 3;
  const s = v.toFixed(d).replace(/\.?0+$/, "");
  return lang === "tr" ? s.replace(".", ",") : s;
};

/** Sıra ekseni (ters, parçalı): 1–20 üst bant, 20–100 orta, 100–200+ alt. */
const rankY = (k: number) =>
  k <= 20 ? 456 + ((k - 1) / 19) * 22 : k <= 100 ? 478 + ((k - 20) / 80) * 52 : 530 + Math.min(60, ((k - 100) / 100) * 60);

export interface Marker { date: string; label: string }

export function StockChart({ data, from, to, alarms = [], selected, peak, onPick, ariaLabel }: {
  data: StockData; from: string; to: string; alarms?: Marker[]; selected?: string; peak?: Marker;
  onPick?: (weekEnd: string) => void; ariaLabel: string;
}) {
  const f = useT();
  const svgRef = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<number | null>(null);
  const x0 = 60, x1 = 1160;
  const t0 = ms(from), t1 = ms(to);
  const X = (s: string) => x0 + ((ms(s) - t0) / (t1 - t0)) * (x1 - x0);

  const view = useMemo(() => {
    const { d, c, v } = data.prices;
    const idx: number[] = [];
    for (let i = 0; i < d.length; i++) if (d[i] >= from && d[i] <= to && c[i] != null) idx.push(i);
    const closes = idx.map((i) => c[i] as number);
    const lo = closes.length ? Math.min(...closes) : 0, hi = closes.length ? Math.max(...closes) : 1;
    const pad = (hi - lo) * 0.08 || hi * 0.1 || 1;
    const pLo = Math.max(0, lo - pad), pHi = hi + pad;
    const Y = (p: number) => 250 - ((p - pLo) / (pHi - pLo)) * 222;
    const pricePts = idx.map((i) => `${X(d[i]).toFixed(1)},${Y(c[i] as number).toFixed(1)}`).join(" ");
    // hacim: uzun aralıkta haftalık toplam
    const weekly = dayDiff(to, from) > 400;
    const buckets = new Map<string, number>();
    for (const i of idx) {
      const key = weekly ? addDays(d[i], (5 - parseDate(d[i]).getUTCDay() + 7) % 7) : d[i];
      buckets.set(key, (buckets.get(key) ?? 0) + (v[i] ?? 0));
    }
    const vmax = Math.max(1, ...buckets.values());
    const bw = Math.max(1, ((x1 - x0) / Math.max(1, dayDiff(to, from))) * (weekly ? 7 : 1) * 0.7);
    const vol = [...buckets].map(([k, val]) => ({ x: X(k) - bw / 2, h: (val / vmax) * 80, w: bw }));
    // sıra: 2 haftadan uzun boşlukta çizgiyi kes
    const rk = data.ranks.filter((r) => r[0] >= from && r[0] <= to);
    const segs: string[] = [];
    let cur: string[] = [];
    rk.forEach((r, i) => {
      if (i > 0 && dayDiff(r[0], rk[i - 1][0]) > 14) { if (cur.length) segs.push(cur.join(" ")); cur = []; }
      cur.push(`${X(r[0]).toFixed(1)},${rankY(r[1]).toFixed(1)}`);
    });
    if (cur.length) segs.push(cur.join(" "));
    const ticks = niceTicks(pLo, pHi).filter((t) => t >= pLo && t <= pHi);
    return { idx, Y, pricePts, vol, segs, rk, ticks };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, from, to]);

  const bands = data.cases.filter((c) => c.known && c.end >= from && c.start <= to);
  const decs = data.decisions.filter((d) => d.date >= from && d.date <= to);
  const span = dayDiff(to, from);
  const months: { x: number; l: string }[] = [];
  const step = span <= 270 ? 1 : span <= 900 ? 3 : span <= 2600 ? 12 : 24;
  const start = parseDate(from);
  for (let y = start.getUTCFullYear(), m = start.getUTCMonth() + 1; ; m++) {
    if (m > 11) { m = 0; y++; }
    const s = `${y}-${String(m + 1).padStart(2, "0")}-01`;
    if (s > to) break;
    if ((y * 12 + m) % step === 0) months.push({ x: X(s), l: m === 0 || step >= 12 ? f.month(s) : f.month(s, false) });
  }

  const toDate = (clientX: number) => {
    const el = svgRef.current;
    if (!el) return null;
    const rect = el.getBoundingClientRect();
    const sx = ((clientX - rect.left) / rect.width) * 1200;
    if (sx < x0 || sx > x1) return null;
    return t0 + ((sx - x0) / (x1 - x0)) * (t1 - t0);
  };
  const nearestRank = (t: number) => {
    let best = -1, bd = Infinity;
    view.rk.forEach((r, i) => { const dd = Math.abs(ms(r[0]) - t); if (dd < bd) { bd = dd; best = i; } });
    return best >= 0 && bd < 10 * 864e5 ? view.rk[best] : undefined;
  };
  const nearestPrice = (t: number) => {
    let best = -1, bd = Infinity;
    for (const i of view.idx) { const dd = Math.abs(ms(data.prices.d[i]) - t); if (dd < bd) { bd = dd; best = i; } }
    return best;
  };
  const hp = hover != null ? nearestPrice(hover) : -1;
  const hr = hover != null ? nearestRank(hover) : undefined;

  return (
    <svg ref={svgRef} viewBox="0 0 1200 620" style={{ width: "100%", height: "auto", display: "block", cursor: onPick ? "pointer" : "default", touchAction: "pan-y" }}
         role="img" aria-label={ariaLabel}
         onMouseMove={(e) => setHover(toDate(e.clientX))} onMouseLeave={() => setHover(null)}
         onClick={(e) => { const t = toDate(e.clientX); const r = t != null ? nearestRank(t) : undefined; if (r && onPick) onPick(r[0]); }}>
      <text x="8" y="16" fontSize="12" fontWeight="600" fill="var(--muted)">{f.L("Fiyat (TL, düzeltilmiş)", "Price (TRY, adjusted)")}</text>
      {bands.map((b) => {
        const a = Math.max(x0, X(b.start)), z = Math.min(x1, X(b.end));
        return <rect key={b.id} x={a} y="24" width={Math.max(2, z - a)} height="566" fill="#f4a261" fillOpacity=".2" />;
      })}
      {view.ticks.map((t) => (
        <g key={t}>
          <line x1={x0} x2={x1} y1={view.Y(t)} y2={view.Y(t)} stroke="var(--grid)" />
          <text x="52" y={view.Y(t) + 4} fontSize="11" textAnchor="end" fill="var(--faint)">{fmtTick(t, f.lang)}</text>
        </g>
      ))}
      <polyline points={view.pricePts} fill="none" stroke="var(--text)" strokeWidth="2" strokeLinejoin="round" />
      {peak && peak.date >= from && peak.date <= to && (() => {
        const i = nearestPrice(ms(peak.date));
        if (i < 0) return null;
        const px = X(data.prices.d[i]), py = view.Y(data.prices.c[i] as number);
        return <g><circle cx={px} cy={py} r="5" fill="none" stroke="var(--text)" strokeWidth="2" /><text x={px + 10} y={py + 4} fontSize="12" fontWeight="600" fill="var(--text)">{peak.label}</text></g>;
      })()}
      {decs.map((d, i) => {
        const x = X(d.date);
        return (
          <path key={i} d={`M${x} 262 L${x + 7} 276 L${x - 7} 276 Z`} fill="var(--text)">
            <title>{`${f.L(...(DECISION_TYPES[d.type] ?? [d.type, d.type]))} · ${f.date(d.date)}${d.ref ? ` · ${f.L("Bülten", "Bulletin")} ${d.ref}` : ""}`}</title>
          </path>
        );
      })}
      <text x="8" y="316" fontSize="12" fontWeight="600" fill="var(--muted)">{f.L("Hacim", "Volume")}{span > 400 ? f.L(" (haftalık)", " (weekly)") : ""}</text>
      <line x1={x0} x2={x1} y1="410" y2="410" stroke="var(--line)" />
      {view.vol.map((b, i) => <rect key={i} x={b.x} y={410 - b.h} width={b.w} height={b.h} fill="var(--vol)" />)}
      <text x="8" y="446" fontSize="12" fontWeight="600" fill="var(--muted)">{f.L("Haftalık sıra (1 = en şüpheli)", "Weekly rank (1 = most suspicious)")}</text>
      <line x1={x0} x2={x1} y1="456" y2="456" stroke="var(--grid)" />
      <text x="52" y="460" fontSize="11" textAnchor="end" fill="var(--faint)">1</text>
      <line x1={x0} x2={x1} y1="478" y2="478" stroke="#e63946" strokeWidth="1.5" strokeDasharray="6 5" />
      <text x="52" y="482" fontSize="11" textAnchor="end" fill="var(--red-ink)" fontWeight="600">20</text>
      <text x="1166" y="482" fontSize="11" fill="var(--red-ink)" fontWeight="600">{f.L("ilk 20", "top 20")}</text>
      <line x1={x0} x2={x1} y1="530" y2="530" stroke="var(--grid)" />
      <text x="52" y="534" fontSize="11" textAnchor="end" fill="var(--faint)">100</text>
      <line x1={x0} x2={x1} y1="590" y2="590" stroke="var(--line)" />
      <text x="52" y="594" fontSize="11" textAnchor="end" fill="var(--faint)">200+</text>
      {view.segs.map((s, i) => <polyline key={i} points={s} fill="none" stroke="var(--teal)" strokeWidth="2" strokeLinejoin="round" />)}
      {alarms.filter((a) => a.date >= from && a.date <= to).map((a) => {
        const x = X(a.date);
        const w = Math.max(96, a.label.length * 6.4 + 16);
        const lx = Math.min(Math.max(x, x0 + w / 2), x1 - w / 2);
        return (
          <g key={a.date}>
            <line x1={x} y1="24" x2={x} y2="590" stroke="#e63946" strokeWidth="2" />
            <rect x={lx - w / 2} y="290" width={w} height="20" rx="4" fill="#e63946" />
            <text x={lx} y="304" fontSize="11" fontWeight="600" textAnchor="middle" fill="#ffffff">{a.label}</text>
          </g>
        );
      })}
      {selected && selected >= from && selected <= to && !alarms.some((a) => a.date === selected) && (
        <g>
          <line x1={X(selected)} y1="24" x2={X(selected)} y2="590" stroke="var(--teal-ink)" strokeWidth="1.5" strokeDasharray="4 4" />
          <text x={Math.min(X(selected) + 6, x1 - 90)} y="38" fontSize="11" fontWeight="600" fill="var(--teal-ink)">{f.L("Seçili hafta", "Selected week")}</text>
        </g>
      )}
      {months.map((m, i) => <text key={i} x={m.x} y="612" fontSize="11" textAnchor="middle" fill="var(--faint)">{m.l}</text>)}
      {hover != null && hp >= 0 && (() => {
        const x = X(data.prices.d[hp]);
        const lines = [f.date(data.prices.d[hp]), `${f.L("Kapanış", "Close")} ${fmtTick(data.prices.c[hp] as number, f.lang)}`];
        if (hr) lines.push(`${f.L("Sıra", "Rank")} ${hr[1]} / ${hr[2]}`);
        const bx = x > 900 ? x - 158 : x + 10;
        return (
          <g pointerEvents="none">
            <line x1={x} y1="24" x2={x} y2="590" stroke="var(--line-2)" />
            <rect x={bx} y="30" width="148" height={14 + lines.length * 16} rx="6" fill="var(--surface)" stroke="var(--line-2)" />
            {lines.map((l, i) => <text key={i} x={bx + 10} y={48 + i * 16} fontSize="12" fontWeight={i === 0 ? 600 : 400} fill="var(--text)">{l}</text>)}
          </g>
        );
      })()}
    </svg>
  );
}

/** Küçük fiyat grafiği: turuncu SPK bantları + kırmızı dikey çizgi. */
export function MiniPrice({ data, from, to, mark, markLabel, w = 360, h = 170, ariaLabel }: {
  data: StockData; from: string; to: string; mark?: string; markLabel?: string; w?: number; h?: number; ariaLabel: string;
}) {
  const t0 = ms(from), t1 = ms(to);
  const X = (s: string) => ((ms(s) - t0) / (t1 - t0)) * w;
  const { d, c } = data.prices;
  const pts: [number, number][] = [];
  for (let i = 0; i < d.length; i++) if (d[i] >= from && d[i] <= to && c[i] != null) pts.push([X(d[i]), c[i] as number]);
  const lo = Math.min(...pts.map((p) => p[1])), hi = Math.max(...pts.map((p) => p[1]));
  const top = 8, bot = h - 12;
  const Y = (p: number) => (hi > lo ? bot - ((p - lo) / (hi - lo)) * (bot - top) : (top + bot) / 2);
  const bands = data.cases.filter((x) => x.known && x.end >= from && x.start <= to);
  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height: "auto", display: "block" }} role="img" aria-label={ariaLabel}>
      {bands.map((b) => {
        const a = Math.max(0, X(b.start)), z = Math.min(w, X(b.end));
        return <rect key={b.id} x={a} y={4} width={Math.max(2, z - a)} height={bot - 4} fill="#f4a261" fillOpacity=".24" />;
      })}
      <line x1="0" y1={bot} x2={w} y2={bot} stroke="var(--line)" />
      {mark && mark >= from && mark <= to && <line x1={X(mark)} y1="4" x2={X(mark)} y2={bot} stroke="#e63946" strokeWidth="2" />}
      <polyline points={pts.map(([x, p]) => `${x.toFixed(1)},${Y(p).toFixed(1)}`).join(" ")} fill="none" stroke="var(--text)" strokeWidth="2" strokeLinejoin="round" />
      {mark && markLabel && mark >= from && mark <= to && (
        <text x={X(mark) > w - 90 ? X(mark) - 4 : X(mark) + 4} y="18" fontSize="11" fontWeight="600" fill="var(--red-ink)" textAnchor={X(mark) > w - 90 ? "end" : "start"}>{markLabel}</text>
      )}
    </svg>
  );
}

/** Histogram: sütunlar + medyan çizgisi. */
export function Histogram({ bins, labels, medianIdx, missIdx, aria }: {
  bins: number[]; labels: string[]; medianIdx: number; missIdx?: number; aria: string;
}) {
  const { L } = useT();
  const max = Math.max(1, ...bins);
  const bw = 62, gap = 72;
  const mx = 40 + medianIdx * gap + bw / 2;
  return (
    <svg viewBox="0 0 560 220" style={{ width: "100%", height: "auto", display: "block" }} role="img" aria-label={aria}>
      <line x1="30" x2="550" y1="180" y2="180" stroke="var(--line)" />
      {bins.map((n, i) => {
        const x = 40 + i * gap, hh = (n / max) * 150;
        return (
          <g key={i}>
            <rect x={x} y={180 - hh} width={bw} height={hh} rx="3" fill={i === missIdx ? "var(--rand)" : "var(--teal)"} />
            <text x={x + bw / 2} y={174 - hh} fontSize="12" fontWeight="600" textAnchor="middle" fill="var(--text)">{n}</text>
            <text x={x + bw / 2} y="200" fontSize="11" textAnchor="middle" fill="var(--faint)">{labels[i]}</text>
          </g>
        );
      })}
      <line x1={mx} x2={mx} y1="10" y2="180" stroke="var(--text)" strokeWidth="1.5" strokeDasharray="4 4" />
      <text x={mx + 6} y="20" fontSize="11" fill="var(--text)">{L("medyan", "median")}</text>
    </svg>
  );
}
