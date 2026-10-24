import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // `npm run dev` talks to the FastAPI server on :8000
    proxy: { "/api": "http://localhost:8000" },
  },
});
