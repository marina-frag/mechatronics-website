import { useCallback, useRef, useState } from 'react';
import { spotIntro } from '../../content/spot/story';
import { useScrollProgress } from '../../hooks/useScrollProgress';
import { ModelStage } from '../../three/ModelStage';
import { SpotModel } from '../../three/SpotModel';
import { Turntable } from '../../three/Turntable';
import type { SpotModelData } from '../../three/spotModel';

const smoothstep = (a: number, b: number, x: number) => {
  const t = Math.min(Math.max((x - a) / (b - a), 0), 1);
  return t * t * (3 - 2 * t);
};

type Counts = { total: number; printed: number; motors: number };

function countParts(model: SpotModelData): Counts {
  return {
    total: model.parts.length,
    printed: model.parts.filter((p) => p.subsystem === 'frame' && p.typeKey !== 'bearing').length,
    motors: model.parts.filter((p) => p.subsystem === 'motors').length,
  };
}

/**
 * Πρώτη οθόνη: το μοντέλο μένει σταθερό (sticky) και, όσο κάνεις scroll,
 * γυρίζει και ανοίγει στα κομμάτια του, με λεζάντες που αλλάζουν.
 */
export function ScrollHero() {
  const section = useRef<HTMLElement>(null);
  const [counts, setCounts] = useState<Counts | null>(null);
  const [captionAt, setCaptionAt] = useState(0);

  const captions = [
    <>
      <h1 className="display">{spotIntro.title}</h1>
      <p className="lead">{spotIntro.subtitle}</p>
      <p className="scroll-cue">Κάνε scroll για να ανοίξει ↓</p>
    </>,
    counts && (
      <p className="caption__big">
        <strong>{counts.total}</strong> εξαρτήματα, από τα πραγματικά αρχεία CAD της ομάδας.
      </p>
    ),
    counts && (
      <p className="caption__big">
        <strong>{counts.printed}</strong> από αυτά τυπώθηκαν σε 3D εκτυπωτή: ο σκελετός, οι ώμοι και τα πόδια.
      </p>
    ),
    counts && counts.motors > 0 && (
      <p className="caption__big">
        <strong>{counts.motors}</strong> σερβοκινητήρες, τρεις σε κάθε πόδι, κινούν τις αρθρώσεις.
      </p>
    ),
  ].filter(Boolean);

  const progress = useScrollProgress(section, (p) =>
    setCaptionAt(Math.min(Math.floor(p * captions.length * 0.999), captions.length - 1)),
  );
  const explode = useCallback(() => smoothstep(0.15, 0.85, progress.current), [progress]);
  const angle = useCallback(() => -0.6 + progress.current * 1.2, [progress]);

  return (
    <section ref={section} className="scroll-hero" aria-label="Το Spot ανοίγει στα κομμάτια του">
      <div className="scroll-hero__sticky">
        <ModelStage
          label="Το 3D μοντέλο του Spot, που χωρίζεται στα εξαρτήματά του καθώς κάνεις scroll"
          className="stage--fill"
          distance={1.7}
          shift={[0.16, 0.04]}
          onReady={(m) => setCounts(countParts(m))}
        >
          {(model) => (
            <Turntable model={model} angle={angle}>
              <SpotModel model={model} explode={explode} smoothing={12} />
            </Turntable>
          )}
        </ModelStage>
        <div className="scroll-hero__captions">
          {captions.map((c, i) => (
            <div key={i} className={`caption${i === captionAt ? ' is-active' : ''}`}>
              {c}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
