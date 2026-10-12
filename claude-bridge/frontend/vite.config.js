import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// `npm run dev` serves the UI on :5173 and forwards /api to the FastAPI server on :8000.
// `npm run build` writes web/dist, which FastAPI serves directly on :8000.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
