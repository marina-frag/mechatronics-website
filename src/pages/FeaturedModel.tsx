import { useReducedMotion } from '../hooks/useReducedMotion';
import { ModelStage } from '../three/ModelStage';
import { SpotModel } from '../three/SpotModel';
import { Turntable } from '../three/Turntable';

const assembled = () => 0;

/** Το Spot να γυρίζει αργά στην αρχική σελίδα. */
export default function FeaturedModel() {
  const reduced = useReducedMotion();
  return (
    <ModelStage label="Το 3D μοντέλο του Spot" className="stage--fill" distance={1.05}>
      {(model) => (
        <Turntable model={model} speed={reduced ? 0 : 0.18}>
          <SpotModel model={model} explode={assembled} />
        </Turntable>
      )}
    </ModelStage>
  );
}
