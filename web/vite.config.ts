import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Yalnızca yerel: sunucu localhost dışına açılmaz (gerçek haftalık listeler internete açılmamalı).
export default defineConfig({
  plugins: [react()],
  server: { host: "localhost", port: 5173, strictPort: true },
  preview: { host: "localhost", port: 4173, strictPort: true },
});
