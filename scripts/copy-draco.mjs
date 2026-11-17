// Αντιγράφει τον Draco decoder του three.js στο public/draco, ώστε το spot.glb
// να αποσυμπιέζεται χωρίς εξωτερικό CDN.
import { cpSync, existsSync, mkdirSync } from 'node:fs';

const src = 'node_modules/three/examples/jsm/libs/draco/gltf';
const dst = 'public/draco';
if (existsSync(src)) {
  mkdirSync(dst, { recursive: true });
  cpSync(src, dst, { recursive: true });
  console.log(`draco decoder -> ${dst}`);
}
