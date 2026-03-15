import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    proxy: {
      "/api/auth": {
        target: "http://127.0.0.1:3001",
        changeOrigin: true,
      },
      "/api/admin": {
        target: "http://127.0.0.1:3001",
        changeOrigin: true,
      },
      "/api/trip": {
        target: "http://127.0.0.1:3204",
        changeOrigin: true,
      },
      "/api/navigation": {
        target: "http://127.0.0.1:3204",
        changeOrigin: true,
      },
      "/cultural": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/cultural/, ''),
      },
    },
    hmr: {
      overlay: false,
    },
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
