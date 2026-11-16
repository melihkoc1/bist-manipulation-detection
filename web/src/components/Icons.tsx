// Tasarımdaki çizgi ikonlar (aria-hidden; anlam her zaman yanındaki metinde).
import type { ReactNode } from "react";

type P = { size?: number; sw?: number; style?: React.CSSProperties };
const I = ({ size = 16, sw = 2, style, children }: P & { children: ReactNode }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={sw}
       strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={style}>{children}</svg>
);

export const Check = (p: P) => <I sw={2.6} {...p}><path d="M5 12l4 4 10-10" /></I>;
export const Clock = (p: P) => <I sw={2.2} {...p}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></I>;
export const Dash = (p: P) => <I sw={2.6} {...p}><path d="M6 12h12" /></I>;
export const Warn = (p: P) => <I sw={2.2} {...p}><path d="M12 3l9 16H3z" /><path d="M12 10v4" /></I>;
export const Info = (p: P) => <I sw={1.8} {...p}><circle cx="12" cy="12" r="9" /><path d="M12 11v6M12 7.5v.5" /></I>;
export const Arrow = (p: P) => <I {...p}><path d="M5 12h14M13 6l6 6-6 6" /></I>;
export const Back = (p: P) => <I {...p}><path d="M19 12H5M11 6l-6 6 6 6" /></I>;
export const ChevL = (p: P) => <I {...p}><path d="M15 6l-6 6 6 6" /></I>;
export const ChevR = (p: P) => <I {...p}><path d="M9 6l6 6-6 6" /></I>;
export const Cal = (p: P) => <I sw={1.8} {...p}><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></I>;
export const Search = (p: P) => <I sw={1.8} {...p}><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></I>;
export const Moon = (p: P) => <I sw={1.8} {...p}><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" /></I>;
export const Sun = (p: P) => <I sw={1.8} {...p}><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></I>;
export const Shield = (p: P) => <I {...p}><path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z" /></I>;
export const Doc = (p: P) => <I sw={1.8} {...p}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></I>;
export const Pulse = (p: P) => <I sw={1.8} {...p}><path d="M3 12h4l3-8 4 16 3-8h4" /></I>;
export const Layers = (p: P) => <I sw={1.8} {...p}><path d="M12 3l9 5-9 5-9-5z" /><path d="M3 13l9 5 9-5" /></I>;
export const List = (p: P) => <I sw={1.8} {...p}><path d="M10 6h11M10 12h11M10 18h11M4 6h1M4 12h1M4 18h1" /></I>;
export const Eye = (p: P) => <I sw={1.8} {...p}><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></I>;
export const Bulb = (p: P) => <I sw={1.8} {...p}><path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z" /></I>;
export const X = (p: P) => <I sw={2.6} {...p}><path d="M6 6l12 12M18 6L6 18" /></I>;
export const Half = (p: P) => <I sw={2.4} {...p}><circle cx="12" cy="12" r="9" /><path d="M12 3v18" /></I>;
export const Star = (p: P) => <I sw={2.4} {...p}><path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.3 6.5 20.2l1-6.2L3 9.6l6.2-.9z" /></I>;
export const Menu = (p: P) => <I {...p}><path d="M4 7h16M4 12h16M4 17h16" /></I>;
export const Person = (p: P) => <I sw={1.8} {...p}><circle cx="12" cy="8" r="4" /><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" /></I>;
export const Download = (p: P) => <I sw={1.8} {...p}><path d="M12 3v12M7 10l5 5 5-5M5 21h14" /></I>;
export const CalClock = (p: P) => <I sw={1.6} {...p}><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4M12 14v3l2 1" /></I>;
export const Github = (p: P) => (
  <I sw={1.8} {...p}>
    <path d="M9 19c-4 1.5-4-2-6-2.5m12 5v-3.5a3 3 0 0 0-.8-2.3c2.8-.3 5.8-1.4 5.8-6.3a4.9 4.9 0 0 0-1.3-3.4 4.6 4.6 0 0 0-.1-3.4s-1.1-.3-3.5 1.3a12 12 0 0 0-6.2 0C6.5 2.3 5.4 2.6 5.4 2.6a4.6 4.6 0 0 0-.1 3.4A4.9 4.9 0 0 0 4 9.4c0 4.9 3 6 5.8 6.3a3 3 0 0 0-.8 2.3V22" />
  </I>
);
export const Tri = ({ size = 10 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 10 10" aria-hidden="true"><path d="M5 0 L10 10 L0 10Z" fill="currentColor" /></svg>
);
export const Logo = () => (
  <svg width="32" height="32" viewBox="0 0 32 32" aria-hidden="true">
    <rect width="32" height="32" rx="8" fill="#1b6f65" />
    <path d="M6 20 L11 20 L14 11 L18 23 L21 15 L26 15" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="26" cy="15" r="2.2" fill="#f4a261" />
  </svg>
);
