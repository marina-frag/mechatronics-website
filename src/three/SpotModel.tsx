import { useFrame, type ThreeEvent } from '@react-three/fiber';
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { MathUtils, MeshStandardMaterial, type Object3D, type Vector3 } from 'three';
import { originalMaterial, type Part, type SpotModelData } from './spotModel';

export type Visibility = 'show' | 'ghost' | 'hide';

type Props = {
  model: SpotModelData;
  /** Στόχος ανάλυσης 0 (συναρμολογημένο) έως 1 (σε μέρη). Καλείται σε κάθε frame. */
  explode: (part: Part) => number;
  visibility?: (part: Part) => Visibility;
  selectedId?: string | null;
  /** Αν δοθεί, τα κομμάτια γίνονται clickable. */
  onSelect?: (part: Part | null) => void;
  /** Πόσο γρήγορα φτάνουν τα κομμάτια στη θέση τους (μεγαλύτερο = πιο γρήγορα). */
  smoothing?: number;
  /** Δική της μετατόπιση ανάλυσης ανά κομμάτι (id → διάνυσμα στο σύστημα του γονέα). Αλλιώς του μοντέλου. */
  offsets?: Map<string, Vector3>;
};

const ACCENT = '#d4542c';

export function SpotModel({ model, explode, visibility, selectedId, onSelect, smoothing = 7, offsets }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const progress = useRef(new Map<string, number>());
  const modes = useRef(new Map<string, Visibility>());

  const materials = useMemo(
    () => ({
      ghost: new MeshStandardMaterial({ color: '#8f99a3', transparent: true, opacity: 0.1, depthWrite: false }),
      selected: new MeshStandardMaterial({ color: ACCENT, roughness: 0.5, emissive: ACCENT, emissiveIntensity: 0.25 }),
      hover: new MeshStandardMaterial({ color: '#f0a07f', roughness: 0.55 }),
    }),
    [],
  );
  useEffect(() => () => Object.values(materials).forEach((m) => m.dispose()), [materials]);

  // Ορατότητα και υλικά: φθηνό, τρέχει σε κάθε render.
  useLayoutEffect(() => {
    for (const p of model.parts) {
      const mode = visibility?.(p) ?? 'show';
      modes.current.set(p.id, mode);
      p.object.visible = mode !== 'hide';
      for (const m of p.meshes) {
        const base = originalMaterial.get(m) ?? m.material;
        if (p.id === selectedId) m.material = materials.selected;
        else if (mode === 'ghost') m.material = materials.ghost;
        else if (onSelect && p.id === hoveredId) m.material = materials.hover;
        else m.material = base;
        m.renderOrder = mode === 'ghost' && p.id !== selectedId ? 1 : 0;
      }
    }
  });

  useFrame((_, dt) => {
    const delta = Math.min(dt, 0.1);
    for (const p of model.parts) {
      const target = MathUtils.clamp(explode(p), 0, 1);
      const prev = progress.current.get(p.id);
      const next = prev === undefined ? target : MathUtils.damp(prev, target, smoothing, delta);
      progress.current.set(p.id, next);
      p.object.position.copy(p.basePosition).addScaledVector(offsets?.get(p.id) ?? p.explodeOffset, next);
    }
  });

  const partAt = (o: Object3D | null): Part | undefined => {
    for (let cur = o; cur; cur = cur.parent) {
      const p = model.byObject.get(cur);
      if (p) return p;
    }
    return undefined;
  };
  const clickable = (p: Part | undefined): p is Part =>
    !!p && (modes.current.get(p.id) === 'show' || p.id === selectedId);

  useEffect(() => () => void (document.body.style.cursor = ''), []);

  if (!onSelect) return <primitive object={model.root} />;

  return (
    <primitive
      object={model.root}
      onPointerOver={(e: ThreeEvent<PointerEvent>) => {
        const p = partAt(e.object);
        if (!clickable(p)) return; // διάφανα κομμάτια: το event περνά στο επόμενο
        e.stopPropagation();
        setHoveredId(p.id);
        document.body.style.cursor = 'pointer';
      }}
      onPointerOut={(e: ThreeEvent<PointerEvent>) => {
        const p = partAt(e.object);
        if (p && p.id === hoveredId) {
          setHoveredId(null);
          document.body.style.cursor = '';
        }
      }}
      onClick={(e: ThreeEvent<MouseEvent>) => {
        const p = partAt(e.object);
        if (!clickable(p)) return;
        e.stopPropagation();
        onSelect(p);
      }}
    />
  );
}
