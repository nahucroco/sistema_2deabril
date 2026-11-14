import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// El Taller de Historias vive en /panel/: la raiz del sitio es la web publica
// (Django). En desarrollo, Vite proxea al backend en :8000 las rutas que son
// de Django, para no pelear con CORS ni con las cookies de sesion.
export default defineConfig({
  base: "/panel/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/admin": "http://localhost:8000",
      "/static": "http://localhost:8000",
      "/media": "http://localhost:8000",
    },
  },
});
