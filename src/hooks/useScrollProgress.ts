import { useEffect, useRef, type RefObject } from 'react';

/**
 * Πρόοδος 0→1 καθώς η σελίδα περνά μέσα από ένα ψηλό section (για sticky σκηνές).
 * Επιστρέφει ref ώστε το 3D να το διαβάζει σε κάθε frame χωρίς re-render·
 * το onChange καλείται σε κάθε αλλαγή για όποιο UI χρειάζεται state.
 */
export function useScrollProgress(target: RefObject<HTMLElement | null>, onChange?: (p: number) => void) {
  const progress = useRef(0);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    let frame = 0;
    const update = () => {
      frame = 0;
      const el = target.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const travel = rect.height - window.innerHeight;
      const p = travel > 0 ? Math.min(Math.max(-rect.top / travel, 0), 1) : 0;
      if (p !== progress.current) {
        progress.current = p;
        onChangeRef.current?.(p);
      }
    };
    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('scroll', schedule);
      window.removeEventListener('resize', schedule);
    };
  }, [target]);

  return progress;
}
