import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "./styles.css";
import { I18nProvider } from "./i18n";
import { Layout } from "./components/Layout";
import Overview from "./pages/Overview";
import TimeMachine from "./pages/TimeMachine";
import StockDetail from "./pages/StockDetail";
import Cases from "./pages/Cases";
import CaseDetail from "./pages/CaseDetail";
import Results from "./pages/Results";
import LiveTest from "./pages/LiveTest";
import Method from "./pages/Method";
import About from "./pages/About";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <I18nProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Overview />} />
            <Route path="zaman-makinesi" element={<TimeMachine />} />
            <Route path="hisse" element={<StockDetail />} />
            <Route path="hisse/:ticker" element={<StockDetail />} />
            <Route path="vakalar" element={<Cases />} />
            <Route path="vakalar/:id" element={<CaseDetail />} />
            <Route path="sonuclar" element={<Results />} />
            <Route path="canli-test" element={<LiveTest />} />
            <Route path="yontem" element={<Method />} />
            <Route path="hakkinda" element={<About />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </I18nProvider>
  </StrictMode>,
);
