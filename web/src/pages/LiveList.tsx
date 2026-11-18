import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

/** Canlı test: kaydedilmiş bir haftanın ilk 20 CSV dosyası, olduğu gibi (yalnız yerel site). */
export default function LiveList() {
  const { week = "" } = useParams();
  const [text, setText] = useState("yükleniyor…");
  useEffect(() => {
    document.title = `${week}_ilk20.csv`;
    fetch(`/data/live/${week}_ilk20.csv`)
      .then((r) => (r.ok && !(r.headers.get("content-type") ?? "").includes("html") ? r.text() : Promise.reject(r.status)))
      .then(setText, () => setText(`${week}_ilk20.csv bulunamadı. Önce: python scripts/export_web.py --live`));
  }, [week]);
  return (
    <pre style={{ margin: 0, minHeight: "100vh", padding: 24, background: "#000", color: "#e6e6e6",
                  font: "14px/1.6 ui-monospace, SFMono-Regular, Consolas, monospace", whiteSpace: "pre-wrap" }}>
      {text}
    </pre>
  );
}
