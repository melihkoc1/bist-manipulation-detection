import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { addDays, isNewIpo, useIpo, useJson, type StockData } from "../data";

/** Canlı test: kaydedilmiş bir haftanın ilk 20 CSV dosyası, olduğu gibi (yalnız yerel site).
 *  Dosyanın altında, dosyaya dahil olmayan notlar: listedeki yeni halka arzlar (MEL-92) ve
 *  hisselerin son 30 gündeki KAP bildirimleri (MEL-94; scripts/live_kap.py ile güncellenir). */
const KIND: Record<string, string> = { news: "şirket haberi", rumor: "söylenti açık.", price: "fiyat açıklaması" };

export default function LiveList() {
  const { week = "" } = useParams();
  const [text, setText] = useState("yükleniyor…");
  const [ok, setOk] = useState(false);
  const ipo = useIpo().data;
  const kap = useJson<Record<string, StockData["kap"]>>("live/kap.json").data;
  useEffect(() => {
    document.title = `${week}_ilk20.csv`;
    fetch(`/data/live/${week}_ilk20.csv`)
      .then((r) => (r.ok && !(r.headers.get("content-type") ?? "").includes("html") ? r.text() : Promise.reject(r.status)))
      .then((t) => { setText(t); setOk(true); },
            () => { setText(`${week}_ilk20.csv bulunamadı. Önce: python scripts/export_web.py --live`); setOk(false); });
  }, [week]);
  const tickers = ok ? text.split(/\r?\n/).slice(1).map((ln) => ln.split(",")[1]).filter(Boolean) : [];
  const from = addDays(week, -30);
  const kapLines: string[] = [];
  const none: string[] = [];
  for (const t of tickers) {
    const items = (kap?.[t] ?? []).filter((k) => k[2] !== "other" && k[0] > from && k[0] <= week);
    if (!items.length) { none.push(t); continue; }
    for (const k of items.slice(0, 3)) kapLines.push(`# ${t.padEnd(6)} ${k[0]}  ${KIND[k[2]].padEnd(14)} ${k[4] || k[1]}`);
    if (items.length > 3) kapLines.push(`# ${"".padEnd(6)} … ${items.length - 3} bildirim daha`);
  }
  const fresh = ipo ? tickers.filter((t) => isNewIpo(ipo, t, week)) : [];
  const mono = { margin: 0, padding: 24, background: "#000", font: "14px/1.6 ui-monospace, SFMono-Regular, Consolas, monospace",
                 whiteSpace: "pre-wrap" } as const;
  return (
    <div style={{ minHeight: "100vh", background: "#000" }}>
      <pre style={{ ...mono, color: "#e6e6e6" }}>{text}</pre>
      {ok && ipo && (
        <pre style={{ ...mono, color: "#9a9a9a", borderTop: "1px solid #333" }}>
          {"# Not (dosyaya dahil değil): yeni halka arz, ilk 60 işlem günü\n"}
          {fresh.length
            ? `# ${fresh.join(", ")}\n# Bu dönemde fiyat ve hacim doğal olarak oynak; geçmişte listeye giren yeni halka arzlar çoğunlukla boş alarm oldu.`
            : "# yok"}
        </pre>
      )}
      {ok && kap && (
        <pre style={{ ...mono, color: "#9a9a9a", borderTop: "1px solid #333" }}>
          {`# Not (dosyaya dahil değil): KAP bildirimleri, ${from} sonrası – ${week}\n`}
          {kapLines.length ? kapLines.join("\n") + "\n" : ""}
          {`# şirket bildirimi yok: ${none.length ? none.join(", ") : "—"}\n`}
          {"# Bilgi amaçlı: haber hareketi açıklamaz, şüpheyi de kaldırmaz; geçmişte SPK vakalarında ve boş alarmlarda benzer sıklıktaydı."}
        </pre>
      )}
    </div>
  );
}
