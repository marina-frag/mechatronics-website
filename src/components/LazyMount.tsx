import { useEffect, useRef, useState, type ReactNode } from 'react';

/**
 * Φορτώνει το περιεχόμενο (π.χ. ένα 3D canvas) μόνο όταν πλησιάζει στην οθόνη
 * και το αφαιρεί όταν απομακρυνθεί, ώστε να μην τρέχουν πολλά WebGL μαζί.
 */
export function LazyMount({
  children,
  className,
  rootMargin = '400px 0px',
}: {
  children: ReactNode;
  className?: string;
  rootMargin?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [near, setNear] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([entry]) => setNear(entry.isIntersecting), { rootMargin });
    io.observe(el);
    return () => io.disconnect();
  }, [rootMargin]);

  return (
    <div ref={ref} className={className}>
      {near ? children : null}
    </div>
  );
}
