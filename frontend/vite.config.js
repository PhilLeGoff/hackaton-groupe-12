import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const PORT = env.APP_PORT || 3000;

  return {
    plugins: [
      react(),
      tailwindcss(), // ← ajoute ça
    ],
    server: {
      proxy: {
        "/api": `http://localhost:${PORT}`,
      },
    },
  };
});
