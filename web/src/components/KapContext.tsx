import { Link } from "react-router-dom";
import { addDays, type StockData } from "../data";
import { useT } from "../i18n";

export const KAP_DAYS = 30;
const CATS: Record<string, { cls: string; name: [string, string] }> = {
  news: { cls: "tag b-teal", name: ["Şirket haberi", "Company news"] },
  rumor: { cls: "tag b-amber", name: ["Söylenti açıklaması", "Rumor statement"] },
  price: { cls: "tag b-gray", name: ["Fiyat hareketi açıklaması", "Price-move statement"] },
};
const MAX = 5;

/** Seçili haftanın son KAP_DAYS günündeki şirket bildirimleri (yalnız o haftaya kadar yayımlananlar).
 *  Bilgi amaçlı: haber zamanlaması SPK vakalarını boş alarmlardan ayırmıyor (MEL-94). */
export function KapContext({ d, week }: { d: StockData; week: string }) {
  const f = useT();
  const from = addDays(week, -KAP_DAYS);
  const items = d.kap.filter((k) => k[2] !== "other" && k[0] > from && k[0] <= week); // en yeni önce
  const nNews = items.filter((k) => k[2] === "news").length;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <h3 style={{ fontSize: 15, fontWeight: 600 }}>{f.L(`KAP haberleri · son ${KAP_DAYS} gün`, `KAP news · last ${KAP_DAYS} days`)}</h3>
        <p style={{ fontSize: 12 }} className="faint">
          {nNews
            ? f.L(`${nNews} şirket haberi, ${items.length - nNews} diğer açıklama`, `${nNews} company news, ${items.length - nNews} other statements`)
            : f.L("Bu dönemde şirket haberi yok.", "No company news in this period.")}
        </p>
      </div>
      {items.length > 0 && (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column" }}>
          {items.slice(0, MAX).map((k) => (
            <li key={k[3]} style={{ display: "flex", flexDirection: "column", gap: 4, padding: "8px 0", borderTop: "1px solid var(--line)", fontSize: 13 }}>
              <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8 }}>
                <span className="muted" style={{ whiteSpace: "nowrap" }}>{f.date(k[0])}</span>
                <span className={CATS[k[2]].cls}>{f.L(...CATS[k[2]].name)}</span>
              </div>
              <a href={`https://www.kap.org.tr/tr/Bildirim/${k[3]}`} target="_blank" rel="noreferrer"
                 style={{ color: "var(--text)", textDecoration: "none", fontWeight: 500, overflowWrap: "anywhere" }}>
                {k[4] || k[1] || "—"}
              </a>
              {k[4] && k[1] && <span style={{ fontSize: 12, overflowWrap: "anywhere" }} className="faint">{k[1]}</span>}
            </li>
          ))}
        </ul>
      )}
      {items.length > MAX && (
        <Link to={`/hisse/${d.ticker}?hafta=${week}`} style={{ fontSize: 13 }}>
          {f.L(`${items.length - MAX} bildirim daha · hisse detayında`, `${items.length - MAX} more · on the stock page`)}
        </Link>
      )}
      <p style={{ fontSize: 12, lineHeight: 1.5 }} className="faint">
        {f.L("Bilgi amaçlı. Haber olması hareketi açıklamaz, şüpheyi de kaldırmaz: geçmişte SPK vakalarında ve boş alarmlarda haber benzer sıklıktaydı. Yalnız KAP; gazete, TV ve sosyal medya haberleri yok.",
             "For context only. News neither explains a move nor clears it: in the past, SPK cases and false alarms had news equally often. KAP only; no newspaper, TV or social media.")}
      </p>
    </div>
  );
}
