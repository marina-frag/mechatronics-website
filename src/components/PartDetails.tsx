import { LEG_ORDER, LEGS, SUBSYSTEMS, partInfo, sourceFile, type PartTypeKey } from '../content/spot/parts';
import { assemblySteps } from '../content/spot/story';
import type { PartSummary } from '../three/spotModel';

const TYPE_ORDER: PartTypeKey[] = assemblySteps.flatMap((s) => s.types);

/** Αριστερά (L_) πριν από δεξιά (R_). */
const sideRank = (label: string) => (/(^|[_-])L_/.test(label) ? 0 : /(^|[_-])R_/.test(label) ? 1 : 2);

/** Κάρτα με όνομα, λειτουργία και σχετικό αρχείο του επιλεγμένου κομματιού. */
export function PartCard({ part, onClose }: { part: PartSummary | null; onClose: () => void }) {
  if (!part) {
    return (
      <div className="part-card part-card--empty">
        <p>Κάνε κλικ σε ένα εξάρτημα (στο 3D ή στη λίστα) για να δεις τι κάνει.</p>
      </div>
    );
  }
  const info = partInfo(part.label);
  const leg = LEGS[part.leg];
  return (
    <div className="part-card" aria-live="polite">
      <div className="part-card__head">
        <div>
          <p className="eyebrow">
            {SUBSYSTEMS[part.subsystem].label}
            {leg ? ` · ${leg.label}` : ''}
          </p>
          <h3>{info.title}</h3>
        </div>
        <button type="button" className="icon-button" onClick={onClose} aria-label="Κλείσιμο">
          ×
        </button>
      </div>
      {info.description && <p>{info.description}</p>}
      <dl className="part-card__meta">
        <dt>Σχετικό αρχείο</dt>
        <dd>
          <code>{sourceFile(part.label)}</code>
        </dd>
      </dl>
    </div>
  );
}

/** Λίστα όλων των κομματιών, ομαδοποιημένων ανά είδος, με κουμπί για κάθε πόδι. */
export function PartList({
  parts,
  selectedId,
  onSelect,
}: {
  parts: PartSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const groups = new Map<string, PartSummary[]>();
  for (const p of parts) {
    const title = partInfo(p.label).title;
    groups.set(title, [...(groups.get(title) ?? []), p]);
  }
  const rows = [...groups.entries()]
    .map(([title, items]) => ({
      title,
      order: TYPE_ORDER.indexOf(items[0].typeKey),
      items: items.sort(
        (a, b) =>
          LEG_ORDER.indexOf(a.leg) - LEG_ORDER.indexOf(b.leg) ||
          sideRank(a.label) - sideRank(b.label) ||
          a.label.localeCompare(b.label),
      ),
    }))
    .sort((a, b) => a.order - b.order);

  // Όταν ένα πόδι έχει πολλά ίδια κομμάτια (π.χ. 3 κινητήρες): ΜΑ1, ΜΑ2, ΜΑ3.
  const chipText = (items: PartSummary[], p: PartSummary, i: number) => {
    const leg = LEGS[p.leg];
    if (!leg) {
      if (items.length === 1) return 'Επιλογή';
      if (/(^|[_-])L_/.test(p.label)) return 'Αρ';
      if (/(^|[_-])R_/.test(p.label)) return 'Δε';
      return String(i + 1);
    }
    const sameLeg = items.filter((x) => x.leg === p.leg);
    return sameLeg.length > 1 ? `${leg.short}${sameLeg.indexOf(p) + 1}` : leg.short;
  };

  return (
    <ul className="part-list">
      {rows.map(({ title, items }) => (
        <li key={title} className="part-list__row">
          <span className="part-list__title">{title}</span>
          <span className="part-list__chips">
            {items.map((p, i) => {
              const leg = LEGS[p.leg];
              return (
                <button
                  key={p.id}
                  type="button"
                  className="chip"
                  aria-pressed={p.id === selectedId}
                  title={leg ? `${leg.label} · ${p.label}` : p.label}
                  onClick={() => onSelect(p.id)}
                >
                  {chipText(items, p, i)}
                </button>
              );
            })}
          </span>
        </li>
      ))}
    </ul>
  );
}
