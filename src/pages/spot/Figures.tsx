import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { RangeSlider } from '../../components/Controls';
import { assemblySteps } from '../../content/spot/story';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { ModelStage } from '../../three/ModelStage';
import { SpotModel, type Visibility } from '../../three/SpotModel';
import type { Part } from '../../three/spotModel';

function Figure({ children, caption }: { children: ReactNode; caption: ReactNode }) {
  return (
    <figure className="figure">
      {children}
      <figcaption>{caption}</figcaption>
    </figure>
  );
}

const explodeLabel = (v: number) => `${Math.round(v * 100)}% ανάλυση`;

/** Ένα πόδι (μπροστά αριστερά) μαζί με τον ώμο του, με slider ανάλυσης. */
export function LegFigure() {
  const [explode, setExplode] = useState(0.35);
  const inLeg = useCallback((p: Part) => p.leg === 'FL' || p.leg === 'F', []);
  const explodeFn = useCallback(() => explode, [explode]);
  const visibility = useCallback((p: Part): Visibility => (inLeg(p) ? 'show' : 'hide'), [inLeg]);

  return (
    <Figure caption="Σύρε για να χωρίσεις το μπροστινό αριστερό πόδι στα κομμάτια του. Σύρε πάνω στο σχήμα για να το περιστρέψεις.">
      <ModelStage
        label="Το μπροστινό αριστερό πόδι του Spot"
        className="figure__stage"
        controls={{ zoom: false }}
        focus={inLeg}
        distance={1.2}
        view={[1.2, 0.5, 1]}
      >
        {(model) => <SpotModel model={model} explode={explodeFn} visibility={visibility} />}
      </ModelStage>
      <RangeSlider
        label="Ανάλυση του ποδιού σε μέρη"
        value={explode}
        onChange={setExplode}
        startLabel="Ενωμένο"
        endLabel="Σε μέρη"
        valueText={explodeLabel(explode)}
      />
    </Figure>
  );
}

/** Animation συναρμολόγησης βήμα-βήμα. */
export function AssemblyFigure() {
  const reduced = useReducedMotion();
  const [step, setStep] = useState(assemblySteps.length - 1);
  const [playing, setPlaying] = useState(false);
  const last = assemblySteps.length - 1;

  const stepOf = useMemo(() => {
    const byType = new Map(assemblySteps.flatMap((s, i) => s.types.map((t) => [t, i] as const)));
    return (p: Part) => byType.get(p.typeKey) ?? last;
  }, [last]);

  useEffect(() => {
    if (!playing) return;
    if (step >= last) {
      setPlaying(false);
      return;
    }
    const t = setTimeout(() => setStep((s) => s + 1), reduced ? 2600 : 1900);
    return () => clearTimeout(t);
  }, [playing, step, last, reduced]);

  const explodeFn = useCallback((p: Part) => (stepOf(p) <= step ? 0 : 1), [stepOf, step]);
  const visibility = useCallback(
    (p: Part): Visibility => (stepOf(p) <= step ? 'show' : 'hide'),
    [stepOf, step],
  );

  const play = () => {
    if (step >= last) setStep(0);
    setPlaying(true);
  };
  const current = assemblySteps[step];

  return (
    <Figure
      caption={
        <>
          <strong>
            Βήμα {step + 1} από {assemblySteps.length}: {current.title}.
          </strong>{' '}
          {current.text}
        </>
      }
    >
      <ModelStage
        label="Το Spot συναρμολογείται βήμα-βήμα"
        className="figure__stage"
        controls={{ zoom: false }}
        distance={1.25}
      >
        {(model) => <SpotModel model={model} explode={explodeFn} visibility={visibility} smoothing={reduced ? 30 : 4} />}
      </ModelStage>
      <div className="stepper">
        <button
          type="button"
          className="btn btn--small"
          onClick={() => (playing ? setPlaying(false) : play())}
        >
          {playing ? 'Παύση' : step >= last ? 'Από την αρχή' : 'Αναπαραγωγή'}
        </button>
        <ol className="stepper__steps">
          {assemblySteps.map((s, i) => (
            <li key={s.title}>
              <button
                type="button"
                className="stepper__step"
                aria-current={i === step ? 'step' : undefined}
                data-done={i < step || undefined}
                onClick={() => {
                  setPlaying(false);
                  setStep(i);
                }}
              >
                <span className="stepper__dot" aria-hidden="true" />
                {s.title}
              </button>
            </li>
          ))}
        </ol>
      </div>
    </Figure>
  );
}

/** Οι κινητήρες τονισμένοι, ο υπόλοιπος σκελετός διάφανος. */
export function MotorsFigure() {
  const [explode, setExplode] = useState(0);
  const [motors, setMotors] = useState<number | null>(null);
  const explodeFn = useCallback(() => explode, [explode]);
  const visibility = useCallback(
    (p: Part): Visibility => (p.subsystem === 'motors' || p.typeKey === 'bearing' ? 'show' : 'ghost'),
    [],
  );

  return (
    <Figure caption="Οι σερβοκινητήρες και τα ρουλεμάν των αρθρώσεων· ο σκελετός φαίνεται διάφανος.">
      <ModelStage
        label="Οι σερβοκινητήρες του Spot μέσα στον σκελετό"
        className="figure__stage"
        controls={{ zoom: false }}
        distance={1.25}
        onReady={(m) => setMotors(m.parts.filter((p) => p.subsystem === 'motors').length)}
        overlay={
          motors === 0 ? (
            <div className="stage__status">Οι σερβοκινητήρες δεν έχουν μπει ακόμα στη συναρμολόγηση του CAD.</div>
          ) : null
        }
      >
        {(model) => <SpotModel model={model} explode={explodeFn} visibility={visibility} />}
      </ModelStage>
      <RangeSlider
        label="Ανάλυση σε μέρη"
        value={explode}
        onChange={setExplode}
        startLabel="Συναρμολογημένο"
        endLabel="Σε μέρη"
        valueText={explodeLabel(explode)}
      />
    </Figure>
  );
}
