// Três páginas: a principal (clientes), a dos técnicos e a das empresas.
import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  build: {
    rollupOptions: {
      input: { principal: resolve(import.meta.dirname, "index.html"), tecnicos: resolve(import.meta.dirname, "tecnicos.html"), empresas: resolve(import.meta.dirname, "empresas.html") },
    },
  },
});
