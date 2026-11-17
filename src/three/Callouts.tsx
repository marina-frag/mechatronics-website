import { useFrame, useThree } from '@react-three/fiber';
import { useEffect, useMemo, useRef, type RefObject } from 'react';
import { Box3, MathUtils, Vector3 } from 'three';
import type { Part } from './spotModel';

/**
 * Ετικέτες με γραμμές-οδηγούς πάνω σε ένα 3D σχήμα (όπως στα exploded views).
 * match: ποιο κομμάτι δείχνει· αν ταιριάζουν πολλά (π.χ. δύο πλαϊνές πλάκες), διαλέγεται αυτό που βλέπει η κάμερα.
 *
 * Χρήση: <CalloutOverlay> ως overlay του ModelStage, <CalloutTracker> μέσα στο canvas (ίδιο ref),
 * <CalloutLegend> κάτω από το σχήμα (σε στενές οθόνες οι ετικέτες γίνονται αριθμοί + λίστα).
 */
export type Callout = { match: RegExp; title: string; text: string };

export function CalloutOverlay({ ref, callouts }: { ref: RefObject<HTMLDivElement | null>; callouts: Callout[] }) {
  return (
    <div className="callouts" ref={ref} aria-hidden="true">
      <svg className="callouts__lines">
        {callouts.map((c, i) => (
          <g key={c.title}>
            <polyline data-line={i} />
            <circle data-dot={i} r={3.5} />
          </g>
        ))}
      </svg>
      {callouts.map((c, i) => (
        <div key={c.title} className="callouts__label" data-label={i}>
          <strong>{c.title}</strong>
          <span>{c.text}</span>
        </div>
      ))}
      {callouts.map((c, i) => (
        <span key={c.title} className="callouts__badge" data-badge={i}>
          {i + 1}
        </span>
      ))}
    </div>
  );
}

/** Η ίδια πληροφορία ως λίστα: ορατή σε στενές οθόνες, αλλιώς μόνο για αναγνώστες οθόνης. */
export function CalloutLegend({ callouts }: { callouts: Callout[] }) {
  return (
    <ol className="callouts-legend">
      {callouts.map((c) => (
        <li key={c.title}>
          <strong>{c.title}</strong> {c.text}
        </li>
      ))}
    </ol>
  );
}

type Anchor = { part: Part; local: Vector3; offsetLength: number };

/**
 * Σημείο πάνω στην επιφάνεια του κομματιού, στη μεριά που βλέπει η κάμερα: η κορυφή του mesh που είναι
 * πιο κοντά σε ένα σημείο λίγο μπροστά από το κέντρο του (το κέντρο του κουτιού μπορεί να πέφτει στο κενό).
 */
function surfacePoint(part: Part, eye: Vector3): Vector3 {
  const box = new Box3().setFromObject(part.object);
  const c = box.getCenter(new Vector3());
  const r = box.getSize(new Vector3()).length() / 2;
  const target = eye.clone().sub(c).normalize().multiplyScalar(r).add(c);
  const best = c.clone();
  let bestD = Infinity;
  const v = new Vector3();
  for (const m of part.meshes) {
    const pos = m.geometry.getAttribute('position');
    if (!pos) continue;
    m.updateWorldMatrix(true, false);
    const step = Math.max(1, Math.floor(pos.count / 5000));
    for (let i = 0; i < pos.count; i += step) {
      v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld);
      const d = v.distanceToSquared(target);
      if (d < bestD) {
        bestD = d;
        best.copy(v);
      }
    }
  }
  return best;
}

/**
 * Σε κάθε frame: προβάλλει το κέντρο κάθε κομματιού στην οθόνη και στήνει τις ετικέτες σε δύο στήλες
 * (αριστερά/δεξιά του μοντέλου), χωρίς να πέφτει η μία πάνω στην άλλη. Γράφει κατευθείαν στο DOM.
 * fade: οι ετικέτες εμφανίζονται μόνο όταν τα κομμάτια έχουν σχεδόν ανοίξει.
 */
export function CalloutTracker({
  callouts,
  parts,
  offsets,
  overlay,
  fade = false,
}: {
  callouts: Callout[];
  parts: Part[];
  offsets: Map<string, Vector3>;
  overlay: RefObject<HTMLDivElement | null>;
  fade?: boolean;
}) {
  const camera = useThree((s) => s.camera);
  const anchors = useRef<(Anchor | null)[] | null>(null);
  const v = useMemo(() => new Vector3(), []);

  useEffect(() => {
    anchors.current = null;
  }, [parts, callouts]);

  useFrame((state) => {
    const root = overlay.current;
    if (!root) return;
    const { width: w, height: h } = state.size;

    if (!anchors.current) {
      const dist = (p: Part) => p.box.getCenter(new Vector3()).distanceTo(camera.position);
      anchors.current = callouts.map((c) => {
        const matches = parts.filter((p) => c.match.test(p.label));
        if (!matches.length) return null;
        const part = matches.reduce((a, b) => (dist(b) < dist(a) ? b : a));
        // στο σύστημα του γονέα, στη συναρμολογημένη θέση (αφαιρείται η τωρινή μετατόπιση ανάλυσης)
        const shift = part.object.position.clone().sub(part.basePosition);
        return {
          part,
          local: part.object.parent!.worldToLocal(surfacePoint(part, camera.position)).sub(shift),
          offsetLength: offsets.get(part.id)?.length() ?? 1,
        };
      });
    }

    // πόσο έχει ανοίξει (0..1)
    let open = 1;
    const pts: { i: number; x: number; y: number; ly: number }[] = [];
    anchors.current.forEach((a, i) => {
      if (!a) return;
      const moved = v.copy(a.part.object.position).sub(a.part.basePosition);
      open = Math.min(open, moved.length() / Math.max(a.offsetLength, 1e-6));
      v.add(a.local);
      a.part.object.parent!.localToWorld(v);
      v.project(camera);
      pts.push({ i, x: ((v.x + 1) / 2) * w, y: ((1 - v.y) / 2) * h, ly: 0 });
    });
    root.style.opacity = fade ? String(MathUtils.smoothstep(open, 0.55, 0.95)) : '1';

    const pad = 12;
    const labelW = MathUtils.clamp(w * 0.2, 140, 200);
    const labels = root.querySelectorAll<HTMLElement>('[data-label]');
    // ύψος κάθε ετικέτας (όσες γραμμές πιάνει) + κενό· η γραμμή δείχνει στη μέση του τίτλου
    const mid = 11;
    const space = Array.from(labels, (el) => (el.offsetHeight || 36) + 8);
    const columns = [pts.filter((p) => p.x < w / 2), pts.filter((p) => p.x >= w / 2)];
    for (const col of columns) {
      col.sort((a, b) => a.y - b.y);
      let next = pad + mid;
      for (const p of col) {
        p.ly = Math.max(p.y, next);
        next = p.ly + space[p.i];
      }
      let limit = h - pad - (space[col[col.length - 1]?.i] ?? 36) + 8 + mid;
      for (let k = col.length - 1; k >= 0; k--) {
        col[k].ly = Math.min(col[k].ly, limit);
        if (k > 0) limit = col[k].ly - space[col[k - 1].i];
      }
    }

    for (const [side, col] of columns.entries()) {
      for (const p of col) {
        const label = labels[p.i];
        const line = root.querySelector<SVGPolylineElement>(`[data-line="${p.i}"]`);
        const dot = root.querySelector<SVGCircleElement>(`[data-dot="${p.i}"]`);
        const badge = root.querySelector<HTMLElement>(`[data-badge="${p.i}"]`);
        const left = side === 0;
        const edge = left ? pad + labelW : w - pad - labelW;
        const elbow = left ? edge + 14 : edge - 14;
        const end = left ? edge + 4 : edge - 4;
        if (label) {
          label.dataset.side = left ? 'left' : 'right';
          label.style.width = `${labelW}px`;
          label.style.transform = `translate(${left ? pad : edge}px, ${p.ly - mid}px)`;
        }
        line?.setAttribute('points', `${p.x},${p.y} ${elbow},${p.ly} ${end},${p.ly}`);
        dot?.setAttribute('cx', String(p.x));
        dot?.setAttribute('cy', String(p.y));
        if (badge) badge.style.transform = `translate(${p.x - 11}px, ${p.y - 11}px)`;
      }
    }
  });

  return null;
}
