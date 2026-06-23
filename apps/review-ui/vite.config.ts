import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://review-api:8080",
        changeOrigin: true,
      },
      "/health": {
        target: "http://review-api:8080",
        changeOrigin: true,
      },
      "/readiness": {
        target: "http://review-api:8080",
        changeOrigin: true,
      },
      "/ready": {
        target: "http://review-api:8080",
        changeOrigin: true,
      },
    },
  },
});