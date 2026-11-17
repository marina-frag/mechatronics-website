import { useFrame } from '@react-three/fiber';
import { useMemo, useRef, type ReactNode } from 'react';
import { Vector3, type Group } from 'three';
import type { SpotModelData } from './spotModel';

/**
 * Περιστρέφει το μοντέλο γύρω από το κέντρο του (άξονας y).
 * speed: συνεχής περιστροφή σε rad/s · angle: απόλυτη γωνία ανά frame (π.χ. από το scroll).
 */
export function Turntable({
  model,
  speed = 0,
  angle,
  children,
}: {
  model: SpotModelData;
  speed?: number;
  angle?: () => number;
  children: ReactNode;
}) {
  const spin = useRef<Group>(null);
  const center = useMemo(() => model.box.getCenter(new Vector3()), [model]);
  const back = useMemo(() => center.clone().negate(), [center]);

  useFrame((_, dt) => {
    const g = spin.current;
    if (!g) return;
    if (angle) g.rotation.y = angle();
    else g.rotation.y += Math.min(dt, 0.1) * speed;
  });

  return (
    <group position={center}>
      <group ref={spin}>
        <group position={back}>{children}</group>
      </group>
    </group>
  );
}
