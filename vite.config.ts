import { rmSync } from 'node:fs';
import { resolve } from 'node:path';
import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';

// BASE_PATH: για φιλοξενία σε υποφάκελο, π.χ. GitHub Pages → BASE_PATH=/mechatronics/
// VITE_PUBLISH_SLIDES=true: τα PDF των διαλέξεων μπαίνουν στο build. Χωρίς αυτό (προεπιλογή) μένουν
// μόνο στο npm run dev, ώσπου να δοθεί άδεια από τον διδάσκοντα.
const publishSlides = process.env.VITE_PUBLISH_SLIDES === 'true';

/** Βγάζει τον φάκελο material/ (PDF διαλέξεων) από το dist/. */
function dropSlides(): Plugin {
  let outDir = 'dist';
  return {
    name: 'drop-slides',
    apply: 'build',
    configResolved(config) {
      outDir = resolve(config.root, config.build.outDir);
    },
    closeBundle() {
      rmSync(resolve(outDir, 'material'), { recursive: true, force: true });
    },
  };
}

export default defineConfig({
  base: process.env.BASE_PATH ?? '/',
  plugins: [react(), ...(publishSlides ? [] : [dropSlides()])],
  // Το three.js (μαζί με το drei) είναι ~1 MB και φορτώνεται μόνο όταν χρειαστεί το 3D.
  build: { chunkSizeWarningLimit: 1200 },
  server: { port: 5173 },
});
