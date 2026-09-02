import { defineConfig } from 'vite';

export default defineConfig({
  base: './', // Utilise des chemins relatifs pour les assets dans le build
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  }
});
