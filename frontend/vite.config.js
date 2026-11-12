import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// El backend Django corre en :8000 en desarrollo; /api se proxea para no
// pelear con CORS mientras se trabaja local.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
