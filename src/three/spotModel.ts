import { useGLTF } from '@react-three/drei';
import { useMemo } from 'react';
import { Box3, Vector3, type Material, type Mesh, type Object3D } from 'three';
import { asset } from '../content/site';
import { partInfo, type PartTypeKey, type SubsystemKey } from '../content/spot/parts';

export const SPOT_MODEL_URL = asset('models/spot.glb');
export const DRACO_PATH = asset('draco/');

/** Πόσο απομακρύνεται κάθε κομμάτι στην πλήρη ανάλυση, ως πολλαπλάσιο της απόστασής του από το κέντρο. */
const EXPLODE_SCALE = 0.9;

export type Part = {
  id: string;
  label: string;
  subsystem: SubsystemKey;
  leg: string;
  typeKey: PartTypeKey;
  object: Object3D;
  meshes: Mesh[];
  /** Θέση στη συναρμολόγηση (στο σύστημα του γονέα). */
  basePosition: Vector3;
  /** Μετατόπιση στην πλήρη ανάλυση (στο σύστημα του γονέα). */
  explodeOffset: Vector3;
  /** Όρια στη συναρμολογημένη θέση (world). */
  box: Box3;
};

/** Απλά δεδομένα για UI εκτός canvas. */
export type PartSummary = Pick<Part, 'id' | 'label' | 'subsystem' | 'leg' | 'typeKey'>;

export type SpotModelData = {
  root: Object3D;
  parts: Part[];
  byObject: Map<Object3D, Part>;
  box: Box3;
};

/** Τα αρχικά υλικά κάθε mesh, για να επανέρχονται μετά από highlight. */
export const originalMaterial = new WeakMap<Mesh, Material | Material[]>();

/** Φορτώνει το spot.glb και δίνει δικό του αντίγραφο σε κάθε canvas (κοινή γεωμετρία). */
export function useSpotModel(): SpotModelData {
  const gltf = useGLTF(SPOT_MODEL_URL, DRACO_PATH);
  return useMemo(() => buildModel(gltf.scene), [gltf.scene]);
}

useGLTF.preload(SPOT_MODEL_URL, DRACO_PATH);

export function summarize(parts: Part[]): PartSummary[] {
  return parts.map(({ id, label, subsystem, leg, typeKey }) => ({ id, label, subsystem, leg, typeKey }));
}

export function boxOf(parts: Part[]): Box3 {
  const box = new Box3();
  for (const p of parts) box.union(p.box);
  return box;
}

/**
 * Μετατοπίσεις ανάλυσης για μια ομάδα κομματιών, γύρω από το δικό της κέντρο (όχι το κέντρο του ρομπότ).
 * worldOffset(p, center, radius) δίνει τη μετατόπιση του κομματιού σε συντεταγμένες κόσμου.
 */
export function groupOffsets(
  parts: Part[],
  worldOffset: (p: Part, center: Vector3, radius: number) => Vector3,
): Map<string, Vector3> {
  const box = boxOf(parts);
  const center = box.getCenter(new Vector3());
  const radius = Math.max(box.getSize(new Vector3()).length() / 2, 1e-3);
  const out = new Map<string, Vector3>();
  for (const p of parts) {
    const parent = p.object.parent;
    const d = worldOffset(p, center, radius);
    if (!parent) {
      out.set(p.id, d);
      continue;
    }
    const a = parent.worldToLocal(center.clone());
    out.set(p.id, parent.worldToLocal(center.clone().add(d)).sub(a));
  }
  return out;
}

function buildModel(source: Object3D): SpotModelData {
  const root = source.clone(true);
  root.updateMatrixWorld(true);

  const objects: Object3D[] = [];
  const visit = (o: Object3D) => {
    if (o !== root && typeof o.userData.label === 'string') {
      objects.push(o);
      return;
    }
    o.children.forEach(visit);
  };
  visit(root);

  const seen = new Map<string, number>();
  const parts: Part[] = objects.map((object) => {
    const label = String(object.userData.label);
    const n = (seen.get(label) ?? 0) + 1;
    seen.set(label, n);
    const meshes: Mesh[] = [];
    object.traverse((o) => {
      if ((o as Mesh).isMesh) {
        const m = o as Mesh;
        meshes.push(m);
        originalMaterial.set(m, m.material);
      }
    });
    return {
      id: n === 1 ? label : `${label}#${n}`,
      label,
      subsystem: (object.userData.subsystem as SubsystemKey) ?? 'frame',
      leg: String(object.userData.leg ?? ''),
      typeKey: partInfo(label).key,
      object,
      meshes,
      basePosition: object.position.clone(),
      explodeOffset: new Vector3(),
      box: new Box3().setFromObject(object),
    };
  });

  const box = boxOf(parts);
  const center = box.getCenter(new Vector3());
  const radius = Math.max(box.getSize(new Vector3()).length() / 2, 1e-3);

  for (const p of parts) {
    const parent = p.object.parent ?? root;
    const c = parent.worldToLocal(p.box.getCenter(new Vector3()));
    const c0 = parent.worldToLocal(center.clone());
    const dir = c.sub(c0);
    // Κομμάτια σχεδόν στο κέντρο ανεβαίνουν προς τα πάνω, για να μη μένουν κρυμμένα.
    if (dir.length() < radius * 0.12) dir.set(0, radius * 0.35, 0);
    p.explodeOffset.copy(dir.multiplyScalar(EXPLODE_SCALE));
  }

  return { root, parts, byObject: new Map(parts.map((p) => [p.object, p])), box };
}
