import { useId } from 'react';

/** Slider με ετικέτες στα δύο άκρα, όπως στα διαδραστικά σχήματα του Ciechanowski. */
export function RangeSlider({
  label,
  value,
  onChange,
  min = 0,
  max = 1,
  step = 0.001,
  startLabel,
  endLabel,
  valueText,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  startLabel?: string;
  endLabel?: string;
  valueText?: string;
}) {
  const id = useId();
  return (
    <div className="range">
      <label htmlFor={id} className="visually-hidden">
        {label}
      </label>
      {startLabel && <span className="range__end">{startLabel}</span>}
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        aria-valuetext={valueText}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      {endLabel && <span className="range__end">{endLabel}</span>}
    </div>
  );
}

export type SegmentOption<T extends string> = { value: T; label: string; disabled?: boolean; title?: string };

/** Ομάδα κουμπιών όπου ένα είναι ενεργό. */
export function Segmented<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: SegmentOption<T>[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          className="segmented__item"
          aria-pressed={o.value === value}
          disabled={o.disabled}
          title={o.title}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
