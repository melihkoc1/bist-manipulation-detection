import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { isNewIpo, useIpo } from "../data";

/** Canlı test: kaydedilmiş bir haftanın ilk 20 CSV dosyası, olduğu gibi (yalnız yerel site).
 *  Dosyanın altında, dosyaya dahil olmayan bir not: listedeki yeni halka arzlar (MEL-92). */
export default function LiveList() {
  const { week = "" } = useParams();
  const [text, setText] = useState("yükleniyor…");
  const [ok, setOk] = useState(false);
  const ipo = useIpo().data;
  useEffect(() => {
    document.title = `${week}_ilk20.csv`;
    fetch(`/data/live/${week}_ilk20.csv`)
      .then((r) => (r.ok && !(r.headers.get("content-type") ?? "").includes("html") ? r.text() : Promise.reject(r.status)))
      .then((t) => { setText(t); setOk(true); },
            () => { setText(`${week}_ilk20.csv bulunamadı. Önce: python scripts/export_web.py --live`); setOk(false); });
  }, [week]);
  const fresh = ok && ipo
    ? text.split(/\r?\n/).slice(1).map((ln) => ln.split(",")[1]).filter((t) => t && isNewIpo(ipo, t, week))
    : [];
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
    </div>
  );
}
