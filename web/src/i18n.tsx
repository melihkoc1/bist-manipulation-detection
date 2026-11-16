// Dil (TR varsayılan, EN) ve tema (açık/koyu). Tercihler tarayıcıda saklanır.
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { parseDate } from "./data";

export type Lang = "tr" | "en";
type Ctx = {
  lang: Lang; setLang: (l: Lang) => void; dark: boolean; toggleDark: () => void;
  L: (tr: string, en: string) => string;
  pct: (x: number | null | undefined, digits?: number) => string;
  num: (x: number | null | undefined, digits?: number) => string;
  times: (x: number, digits?: number) => string;
  date: (s: string | null | undefined) => string;
  month: (s: string, withYear?: boolean) => string;
  range: (a: string, b: string) => string;
};

const I18n = createContext<Ctx | null>(null);
const store = {
  get: (k: string) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k: string, v: string) => { try { localStorage.setItem(k, v); } catch { /* yok say */ } },
};
const MONTHS = {
  tr: ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"],
  en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
};

export function I18nProvider({ children }: { children: ReactNode }) {
  const initialLang = (): Lang => {
    const q = new URLSearchParams(window.location.search).get("lang");
    if (q === "en" || q === "tr") return q;
    return store.get("lang") === "en" ? "en" : "tr";
  };
  const [lang, setLangState] = useState<Lang>(initialLang);
  const [dark, setDark] = useState<boolean>(() => {
    const s = store.get("theme");
    return s ? s === "dark" : window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    store.set("theme", dark ? "dark" : "light");
  }, [dark]);
  useEffect(() => { document.documentElement.lang = lang; store.set("lang", lang); }, [lang]);

  const setLang = useCallback((l: Lang) => setLangState(l), []);
  const toggleDark = useCallback(() => setDark((d) => !d), []);

  const value = useMemo<Ctx>(() => {
    const tr = lang === "tr";
    const dec = (x: number, d: number) => {
      const s = x.toFixed(d);
      return tr ? s.replace(".", ",") : s;
    };
    const two = (n: number) => String(n).padStart(2, "0");
    return {
      lang, setLang, dark, toggleDark,
      L: (a, b) => (tr ? a : b),
      pct: (x, d = 0) => (x == null || Number.isNaN(x) ? "—" : tr ? `%${dec(x * 100, d)}` : `${dec(x * 100, d)}%`),
      num: (x, d = 0) => (x == null || Number.isNaN(x) ? "—" : dec(x, d)),
      times: (x, d = 1) => `${dec(x, d)}×`,
      date: (s) => {
        if (!s) return "—";
        const t = parseDate(s);
        return `${two(t.getUTCDate())}.${two(t.getUTCMonth() + 1)}.${t.getUTCFullYear()}`;
      },
      month: (s, withYear = true) => {
        const t = parseDate(s);
        const m = MONTHS[lang][t.getUTCMonth()];
        return withYear ? `${m} ${t.getUTCFullYear()}` : m;
      },
      range: (a, b) => {
        const x = parseDate(a), y = parseDate(b);
        const dm = (t: Date) => `${two(t.getUTCDate())}.${two(t.getUTCMonth() + 1)}`;
        return `${dm(x)} – ${dm(y)}.${y.getUTCFullYear()}`;
      },
    };
  }, [lang, dark, setLang, toggleDark]);

  return <I18n.Provider value={value}>{children}</I18n.Provider>;
}

export function useT() {
  const c = useContext(I18n);
  if (!c) throw new Error("I18nProvider yok");
  return c;
}
