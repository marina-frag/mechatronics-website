import { Environment, Lightformer, OrbitControls, useProgress } from '@react-three/drei';
import { Canvas, useThree } from '@react-three/fiber';
import { Component, Suspense, useEffect, useLayoutEffect, useRef, type ReactNode } from 'react';
import { MathUtils, Vector3, type PerspectiveCamera } from 'three';
import type { OrbitControls as OrbitControlsImpl } from 'three/addons/controls/OrbitControls.js';
import { LazyMount } from '../components/LazyMount';
import { boxOf, useSpotModel, type Part, type SpotModelData } from './spotModel';

type Props = {
  /** Περιγραφή για αναγνώστες οθόνης. */
  label: string;
  className?: string;
  /** Περιστροφή με το ποντίκι· zoom: false για να μην «κλέβει» το scroll της σελίδας. */
  controls?: false | { zoom: boolean };
  /** Ποια κομμάτια να χωρούν στο κάδρο (προεπιλογή: όλα). */
  focus?: (p: Part) => boolean;
  /** Όταν αλλάζει, η κάμερα ξαναπλαισιώνει. */
  fitKey?: string | number;
  /** Κατεύθυνση της κάμερας από το κέντρο. */
  view?: [number, number, number];
  /** Απόσταση κάμερας ως πολλαπλάσιο του «ίσα-ίσα χωράει». */
  distance?: number;
  /** Μετακίνηση του μοντέλου στην οθόνη (κλάσμα πλάτους/ύψους), μόνο σε φαρδιές οθόνες. */
  shift?: [number, number];
  onReady?: (model: SpotModelData) => void;
  children: (model: SpotModelData) => ReactNode;
  overlay?: ReactNode;
};

export function ModelStage({ label, className, controls = false, overlay, ...scene }: Props) {
  return (
    <LazyMount className={`stage ${className ?? ''}`}>
      <StageErrorBoundary>
        <Canvas
          dpr={[1, 2]}
          camera={{ fov: 30, near: 0.01, far: 100, position: [1, 1, 1] }}
          gl={{ antialias: true, alpha: true }}
          aria-label={label}
          role="img"
        >
          <Lights />
          <Suspense fallback={null}>
            <Scene {...scene} />
          </Suspense>
          {controls && (
            <OrbitControls makeDefault enableDamping enablePan={false} enableZoom={controls.zoom} />
          )}
        </Canvas>
        <StageLoader />
        {overlay}
      </StageErrorBoundary>
    </LazyMount>
  );
}

function Scene({
  children,
  focus,
  fitKey,
  view = [-1, 0.75, 1.2],
  distance = 1.15,
  shift,
  onReady,
}: Omit<Props, 'label' | 'className' | 'controls' | 'overlay'>) {
  const model = useSpotModel();
  const onReadyRef = useRef(onReady);
  onReadyRef.current = onReady;
  useEffect(() => onReadyRef.current?.(model), [model]);

  const camera = useThree((s) => s.camera) as PerspectiveCamera;
  const width = useThree((s) => s.size.width);
  const height = useThree((s) => s.size.height);
  const orbit = useThree((s) => s.controls) as unknown as OrbitControlsImpl | null;
  const focusRef = useRef(focus);
  focusRef.current = focus;
  const [vx, vy, vz] = view;

  useLayoutEffect(() => {
    const chosen = focusRef.current ? model.parts.filter(focusRef.current) : model.parts;
    const box = boxOf(chosen.length ? chosen : model.parts);
    const center = box.getCenter(new Vector3());
    const radius = Math.max(box.getSize(new Vector3()).length() / 2, 0.01);
    const vFov = MathUtils.degToRad(camera.fov);
    const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
    const dist = (radius / Math.sin(Math.min(vFov, hFov) / 2)) * distance;
    camera.position.copy(center).addScaledVector(new Vector3(vx, vy, vz).normalize(), dist);
    camera.near = dist / 100;
    camera.far = dist * 10;
    if (shift && width >= 900) camera.setViewOffset(width, height, -shift[0] * width, -shift[1] * height, width, height);
    else camera.clearViewOffset();
    camera.updateProjectionMatrix();
    camera.lookAt(center);
    if (orbit) {
      orbit.target.copy(center);
      orbit.minDistance = dist * 0.2;
      orbit.maxDistance = dist * 3;
      orbit.update();
    }
  }, [model, fitKey, orbit, camera, width, height, distance, vx, vy, vz, shift?.[0], shift?.[1]]);

  return <>{children(model)}</>;
}

function Lights() {
  return (
    <>
      <ambientLight intensity={0.55} />
      <directionalLight position={[3, 5, 4]} intensity={1.6} />
      <directionalLight position={[-4, 2, -3]} intensity={0.5} />
      <Environment resolution={128} frames={1}>
        <Lightformer form="rect" intensity={2} position={[0, 4, 2]} scale={[8, 3, 1]} />
        <Lightformer form="rect" intensity={0.8} position={[-5, 1, -2]} rotation-y={Math.PI / 2} scale={[6, 3, 1]} />
        <Lightformer form="ring" intensity={1} position={[4, 2, -4]} scale={2} />
      </Environment>
    </>
  );
}

function StageLoader() {
  const { active, progress } = useProgress();
  if (!active) return null;
  return (
    <div className="stage__status" role="status">
      Φόρτωση μοντέλου… {Math.round(progress)}%
    </div>
  );
}

class StageErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="stage__status stage__status--error" role="alert">
          Το 3D μοντέλο δεν φορτώθηκε. Έλεγξε ότι υπάρχει το <code>public/models/spot.glb</code>{' '}
          (<code>npm run glb</code>).
        </div>
      );
    }
    return this.props.children;
  }
}
