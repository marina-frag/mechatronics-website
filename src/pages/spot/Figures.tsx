import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode, type RefObject } from 'react';
import { Vector3 } from 'three';
import { RangeSlider } from '../../components/Controls';
import { assemblySteps } from '../../content/spot/story';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { CalloutLegend, CalloutOverlay, CalloutTracker, type Callout } from '../../three/Callouts';
import { ModelStage } from '../../three/ModelStage';
import { SpotModel, type Visibility } from '../../three/SpotModel';
import { groupOffsets, type Part, type SpotModelData } from '../../three/spotModel';

function Figure({ children, caption }: { children: ReactNode; caption: ReactNode }) {
  return (
    <figure className="figure">
      {children}
      <figcaption>{caption}</figcaption>
    </figure>
  );
}

const explodeLabel = (v: number) => `${Math.round(v * 100)}% ανάλυση`;

/** Το μπροστινό αριστερό πόδι, από το arm_joint ως το πέλμα (χωρίς τους ώμους του σώματος). */
const inLeg = (p: Part) => p.leg === 'FL';
const legVisibility = (p: Part): Visibility => (inLeg(p) ? 'show' : 'hide');
/** Κατά το πλάτος (άξονας z του κόσμου) τα κομμάτια είναι στοιβαγμένα, οπότε απομακρύνονται περισσότερο. */
const LEG_SPREAD = new Vector3(0.7, 0.5, 2.4);

const LEG_CALLOUTS: Callout[] = [
  { match: /arm_joint/i, title: 'Σύνδεσμος μηρού', text: 'Κρατά τον servo του ώμου' },
  { match: /^[LR]_shoulder_reinforcement/i, title: 'Ενίσχυση ώμου', text: 'Κρατά το ρουλεμάν του ισχίου' },
  { match: /motor_.*_top$/i, title: 'Servo ώμου', text: 'Γέρνει όλο το πόδι στο πλάι' },
  { match: /motor_.*_middle$/i, title: 'Servo ισχίου', text: 'Γυρίζει τον μηρό μπρος-πίσω' },
  { match: /arm_cover/i, title: 'Κάλυμμα μηρού', text: 'Μέσα του κάθεται ο servo του ισχίου' },
  { match: /^[LR]_arm_st/i, title: 'Μηρός', text: 'Από το ισχίο ως το γόνατο' },
  { match: /^Bearing/i, title: 'Ρουλεμάν', text: 'Ένα σε κάθε άρθρωση' },
  { match: /motor_.*_bottom$/i, title: 'Servo γονάτου', text: 'Μέσα στην κνήμη· λυγίζει το γόνατο' },
  { match: /wrist/i, title: 'Κνήμη', text: 'Από το γόνατο ως το πέλμα' },
  { match: /^foot/i, title: 'Πέλμα', text: 'Πατά στο έδαφος' },
];

function LegModel({
  model,
  explode,
  overlay,
}: {
  model: SpotModelData;
  explode: number;
  overlay: RefObject<HTMLDivElement | null>;
}) {
  const parts = useMemo(() => model.parts.filter(inLeg), [model]);
  const offsets = useMemo(
    () => groupOffsets(parts, (p, c) => p.box.getCenter(new Vector3()).sub(c).multiply(LEG_SPREAD)),
    [parts],
  );
  const explodeFn = useCallback(() => explode, [explode]);
  return (
    <>
      <SpotModel model={model} explode={explodeFn} visibility={legVisibility} offsets={offsets} />
      <CalloutTracker callouts={LEG_CALLOUTS} parts={parts} offsets={offsets} overlay={overlay} />
    </>
  );
}

/** Ένα πόδι με ετικέτες και slider ανάλυσης. */
export function LegFigure() {
  const [explode, setExplode] = useState(0.6);
  const overlay = useRef<HTMLDivElement>(null);

  return (
    <Figure
      caption={
        <>
          Σύρε για να χωρίσεις το μπροστινό αριστερό πόδι στα κομμάτια του. Σύρε πάνω στο σχήμα για να το περιστρέψεις.
          <CalloutLegend callouts={LEG_CALLOUTS} />
        </>
      }
    >
      <ModelStage
        label="Το μπροστινό αριστερό πόδι του Spot, με ετικέτες"
        className="figure__stage figure__stage--tall"
        controls={{ zoom: false }}
        focus={inLeg}
        distance={1.5}
        view={[-1, 0.35, -0.8]}
        overlay={<CalloutOverlay ref={overlay} callouts={LEG_CALLOUTS} />}
      >
        {(model) => <LegModel model={model} explode={explode} overlay={overlay} />}
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
