import { useEffect, useState } from "react";
import { NavLink, Link, Outlet, useLocation } from "react-router-dom";
import { useT } from "../i18n";
import { Github, Info, Logo, Menu, Moon, Sun, X } from "./Icons";

export const GITHUB = "https://github.com/melihkoc1/bist-manipulation-detection";

export function Layout() {
  const { L, lang, setLang, dark, toggleDark } = useT();
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  useEffect(() => { setOpen(false); window.scrollTo(0, 0); }, [loc.pathname]);

  const items: [string, string, string][] = [
    ["/", "Genel bakış", "Overview"],
    ["/zaman-makinesi", "Zaman makinesi", "Time machine"],
    ["/hisse", "Hisse detayı", "Stock detail"],
    ["/vakalar", "Vaka çalışmaları", "Case studies"],
    ["/sonuclar", "Sonuçlar", "Results"],
    ["/denemeler", "Denemeler", "Experiments"],
    ["/canli-test", "Canlı test", "Live test"],
    ["/yontem", "Yöntem", "Method"],
    ["/hakkinda", "Hakkında", "About"],
  ];

  return (
    <div className="app">
      <a href="#main" className="sr">{L("İçeriğe geç", "Skip to content")}</a>
      <header className="topbar">
        <div className="wrap topbar-in">
          <Link to="/" className="brand"><Logo /><span>{L("BIST Manipülasyon Tespiti", "BIST Manipulation Detection")}</span></Link>
          <div className="top-tools">
            <div className="seg" role="group" aria-label={L("Dil seçimi", "Language")}>
              <button type="button" className={lang === "tr" ? "on" : ""} aria-pressed={lang === "tr"} onClick={() => setLang("tr")}>TR</button>
              <button type="button" className={lang === "en" ? "on" : ""} aria-pressed={lang === "en"} onClick={() => setLang("en")}>EN</button>
            </div>
            <button type="button" className="icon-btn" onClick={toggleDark}
                    aria-label={dark ? L("Açık temaya geç", "Switch to light theme") : L("Koyu temaya geç", "Switch to dark theme")}>
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button type="button" className="icon-btn menu-btn" aria-expanded={open} aria-controls="mainnav"
                    aria-label={L("Menü", "Menu")} onClick={() => setOpen((o) => !o)}>
              {open ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
          <nav id="mainnav" aria-label={L("Ana menü", "Main menu")} className={`nav${open ? " open" : ""}`}>
            {items.map(([to, tr, en]) => (
              <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => (isActive ? "on" : "")}>
                {L(tr, en)}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <Outlet />
      <footer style={{ borderTop: "1px solid var(--line)", background: "var(--surface)" }}>
        <div className="wrap" style={{ padding: "22px clamp(16px, 3vw, 40px)", display: "flex", flexWrap: "wrap", gap: "12px 32px", justifyContent: "space-between", alignItems: "center", fontSize: 13, color: "var(--muted)" }}>
          <p style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <Info />{L("Skorlar istatistiksel anomali sinyalidir, suçlama değildir. Yatırım tavsiyesi değildir.",
                       "Scores are statistical anomaly signals, not accusations. Not investment advice.")}
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 20px", alignItems: "center" }}>
            <a href={GITHUB} target="_blank" rel="noreferrer" style={{ display: "inline-flex", alignItems: "center", gap: 6, fontWeight: 600 }}><Github />GitHub</a>
            <span>Melih Erdem Koçoğlu · {L("Yazılım Mühendisliği Bitirme Projesi 2026–2027", "Software Engineering Graduation Project 2026–2027")}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

/** Sayfa gövdesi: tasarımdaki <main> kabı. */
export function Page({ children, width = "wide", gap }: { children: React.ReactNode; width?: "wide" | "narrow" | "narrower"; gap?: number }) {
  return (
    <main id="main" className={`page wrap ${width === "wide" ? "" : width}`} style={gap ? { gap } : undefined}>
      {children}
    </main>
  );
}
