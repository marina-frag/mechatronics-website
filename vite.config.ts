import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// BASE_PATH: για φιλοξενία σε υποφάκελο, π.χ. GitHub Pages → BASE_PATH=/mechatronics/
export default defineConfig({
  base: process.env.BASE_PATH ?? '/',
  plugins: [react()],
  // Το three.js (μαζί με το drei) είναι ~1 MB και φορτώνεται μόνο όταν χρειαστεί το 3D.
  build: { chunkSizeWarningLimit: 1200 },
  server: { port: 5173 },
});
