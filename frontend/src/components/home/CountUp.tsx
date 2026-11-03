'use client';

import { useEffect, useState } from 'react';

/** Animates a number from 0 to `value` once it is known. */
export default function CountUp({ value, suffix = '', duration = 1200 }: { value: number | null; suffix?: string; duration?: number }) {
  const [shown, setShown] = useState(0);

  useEffect(() => {
    if (value === null) return;
    const reduce = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = reduce ? 1 : Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setShown(Math.round(value * eased));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  if (value === null) return <span>–</span>;
  return (
    <span>
      {shown.toLocaleString('en-IN')}
      {suffix}
    </span>
  );
}
