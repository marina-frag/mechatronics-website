import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode, type RefObject } from 'react';
import { Vector3 } from 'three';
import { useMediaQuery } from '../../hooks/useMediaQuery';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { CalloutLegend, CalloutOverlay, CalloutTracker, type Callout } from '../../three/Callouts';
import { ModelStage } from '../../three/ModelStage';
import { SpotModel, type Visibility } from '../../three/SpotModel';
import { groupOffsets, type Part, type SpotModelData } from '../../three/spotModel';

/** Το σώμα: πλάκα, καλύμματα, πλαϊνά και οι ώμοι στους οποίους δένουν τα πόδια. */
const inBody = (p: Part) => p.typeKey === 'body' || p.typeKey === 'shoulder';
const bodyVisibility = (p: Part): Visibility => (inBody(p) ? 'show' : 'hide');

const CALLOUTS: Callout[] = [
  { match: /T_cover/i, title: 'Πάνω κάλυμμα', text: 'Κλείνει το σώμα από πάνω' },
  { match: /^plate/i, title: 'Πλάκα ηλεκτρονικών', text: 'Εδώ στερεώνονται τα ηλεκτρονικά' },
  { match: /side_plate/i, title: 'Πλαϊνές πλάκες', text: 'Τα δύο τοιχώματα του σώματος' },
  { match: /mega_B_cover/i, title: 'Κάτω κάλυμμα', text: 'Κλείνει το σώμα από κάτω' },
  { match: /^F_cover/i, title: 'Μπροστινό κάλυμμα', text: 'Κλείνει το σώμα μπροστά' },
  { match: /^B_cover_st/i, title: 'Πίσω κάλυμμα', text: 'Κλείνει το σώμα πίσω' },
  { match: /^O_shoulder/i, title: 'Εξωτερικός ώμος', text: 'Εδώ βιδώνει η κόρνα του servo' },
  { match: /^I_shoulder/i, title: 'Εσωτερικός ώμος', text: 'Κρατά το ρουλεμάν του ώμου' },
];

/** Πού πάει κάθε κομμάτι στην ανάλυση (κόσμος: +y πάνω, −x μπροστά, z πλάγια). r = ακτίνα του σώματος. */
function bodyOffset(p: Part, center: Vector3, r: number): Vector3 {
  const d = p.box.getCenter(new Vector3()).sub(center);
  const sx = Math.sign(d.x) || 1;
  const sz = Math.sign(d.z) || 1;
  const l = p.label;
  if (/T_cover/i.test(l)) return new Vector3(0, 0.5 * r, 0);
  if (/^plate/i.test(l)) return new Vector3(0, 0.24 * r, 0);
  if (/mega_B_cover/i.test(l)) return new Vector3(0, -0.36 * r, 0);
  if (/side_plate/i.test(l)) return new Vector3(0, 0, 0.42 * r * sz);
  if (/^O_shoulder/i.test(l)) return new Vector3(0.46 * r * sx, 0, 0);
  if (/^I_shoulder/i.test(l)) return new Vector3(0.26 * r * sx, 0, 0);
  if (/cover/i.test(l)) return new Vector3(0.66 * r * sx, 0, 0);
  return d.multiplyScalar(0.5);
}

type Props = {
  /** Κείμενο δίπλα στο μοντέλο (eyebrow, τίτλος, παράγραφος). */
  children: ReactNode;
};

/** Το σώμα ανοιγμένο, με ετικέτες που δείχνουν κάθε κομμάτι. */
export function BodyFigure({ children }: Props) {
  const reduced = useReducedMotion();
  // σε στενές οθόνες οι ετικέτες γίνονται αριθμοί, οπότε το μοντέλο μπορεί να πιάσει όλο το πλάτος
  const narrow = useMediaQuery('(max-width: 700px)');
  const ref = useRef<HTMLDivElement>(null);
  const overlay = useRef<HTMLDivElement>(null);
  const [apart, setApart] = useState(reduced);

  // Ανοίγει μόνο του την πρώτη φορά που φαίνεται στην οθόνη.
  useEffect(() => {
    const el = ref.current;
    if (!el || apart) return;
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setApart(true);
          io.disconnect();
        }
      },
      { threshold: 0.45 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [apart]);

  return (
    <div className="anatomy" ref={ref}>
      <div className="anatomy__text">
        {children}
        <button type="button" className="btn btn--small" onClick={() => setApart((a) => !a)}>
          {apart ? 'Ένωσε τα κομμάτια' : 'Χώρισε τα κομμάτια'}
        </button>
      </div>
      <figure className="anatomy__figure">
        <ModelStage
          label="Το σώμα του Spot ανοιγμένο σε κομμάτια, με ετικέτες"
          className="anatomy__stage"
          controls={{ zoom: false }}
          focus={inBody}
          distance={narrow ? 1.32 : 1.55}
          view={[-1.05, 0.8, -1]}
          overlay={<CalloutOverlay ref={overlay} callouts={CALLOUTS} />}
        >
          {(model) => <BodyModel model={model} apart={apart} overlay={overlay} smoothing={reduced ? 30 : 3} />}
        </ModelStage>
        <figcaption>
          <CalloutLegend callouts={CALLOUTS} />
        </figcaption>
      </figure>
    </div>
  );
}

function BodyModel({
  model,
  apart,
  overlay,
  smoothing,
}: {
  model: SpotModelData;
  apart: boolean;
  overlay: RefObject<HTMLDivElement | null>;
  smoothing: number;
}) {
  const parts = useMemo(() => model.parts.filter(inBody), [model]);
  const offsets = useMemo(() => groupOffsets(parts, bodyOffset), [parts]);
  const explode = useCallback(() => (apart ? 1 : 0), [apart]);
  return (
    <>
      <SpotModel model={model} explode={explode} visibility={bodyVisibility} offsets={offsets} smoothing={smoothing} />
      <CalloutTracker callouts={CALLOUTS} parts={parts} offsets={offsets} overlay={overlay} fade />
    </>
  );
}
