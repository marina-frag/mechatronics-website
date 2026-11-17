import { useCallback, useState } from 'react';
import { RangeSlider, Segmented } from '../../components/Controls';
import { PartCard, PartList } from '../../components/PartDetails';
import { SUBSYSTEM_ORDER, SUBSYSTEMS, type SubsystemKey } from '../../content/spot/parts';
import { ModelStage } from '../../three/ModelStage';
import { SpotModel, type Visibility } from '../../three/SpotModel';
import { summarize, type Part, type PartSummary } from '../../three/spotModel';

type Filter = 'all' | SubsystemKey;

/** Ελεύθερη εξερεύνηση: περιστροφή/zoom, ανάλυση σε μέρη, υποσυστήματα, κλικ σε κομμάτι. */
export function Explorer() {
  const [explode, setExplode] = useState(0);
  const [filter, setFilter] = useState<Filter>('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [parts, setParts] = useState<PartSummary[]>([]);

  const explodeFn = useCallback(() => explode, [explode]);
  const visibility = useCallback(
    (p: Part): Visibility => (filter === 'all' || p.subsystem === filter ? 'show' : 'ghost'),
    [filter],
  );
  const select = useCallback((p: Part | null) => setSelectedId(p?.id ?? null), []);

  const count = (k: SubsystemKey) => parts.filter((p) => p.subsystem === k).length;
  const listed = filter === 'all' ? parts : parts.filter((p) => p.subsystem === filter);
  const selected = parts.find((p) => p.id === selectedId) ?? null;

  return (
    <div className="explorer">
      <div className="explorer__stage">
        <ModelStage
          label="Διαδραστικό 3D μοντέλο του Spot: σύρε για περιστροφή, κάνε κλικ σε ένα εξάρτημα για πληροφορίες"
          className="stage--fill"
          controls={{ zoom: true }}
          distance={1.25}
          onReady={(m) => setParts(summarize(m.parts))}
        >
          {(model) => (
            <SpotModel
              model={model}
              explode={explodeFn}
              visibility={visibility}
              selectedId={selectedId}
              onSelect={select}
            />
          )}
        </ModelStage>
        <p className="explorer__hint">Σύρε για περιστροφή · ροδέλα ή τσίμπημα για zoom · κλικ σε εξάρτημα</p>
      </div>

      <aside className="explorer__panel" aria-label="Χειριστήρια μοντέλου">
        <div className="control">
          <span className="control__label">Ανάλυση σε μέρη</span>
          <RangeSlider
            label="Συναρμολογημένο ή αναλυμένο σε μέρη"
            value={explode}
            onChange={setExplode}
            startLabel="Συναρμολογημένο"
            endLabel="Σε μέρη"
            valueText={`${Math.round(explode * 100)}% ανάλυση`}
          />
        </div>

        <div className="control">
          <span className="control__label">Υποσύστημα</span>
          <Segmented<Filter>
            label="Επιλογή υποσυστήματος"
            value={filter}
            onChange={setFilter}
            options={[
              { value: 'all', label: 'Όλα' },
              ...SUBSYSTEM_ORDER.map((k) => ({
                value: k,
                label: SUBSYSTEMS[k].label,
                disabled: parts.length > 0 && count(k) === 0,
                title: count(k) === 0 ? 'Δεν υπάρχουν ακόμα στο 3D μοντέλο' : `${count(k)} ${SUBSYSTEMS[k].plural}`,
              })),
            ]}
          />
        </div>

        <PartCard part={selected} onClose={() => setSelectedId(null)} />

        {listed.length > 0 && (
          <details className="control" open>
            <summary className="control__label">Όλα τα εξαρτήματα ({listed.length})</summary>
            <PartList parts={listed} selectedId={selectedId} onSelect={setSelectedId} />
          </details>
        )}
      </aside>
    </div>
  );
}
