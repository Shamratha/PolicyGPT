'use client';

import Link from 'next/link';
import { useEffect } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

/** Shown instead of a blank screen when any page throws while rendering. */
export default function PageError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error('PolicyGPT page error:', error);
  }, [error]);

  return (
    <div className="mx-auto flex max-w-xl flex-col items-center gap-5 py-20 text-center">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-seal-tint text-seal">
        <AlertTriangle className="h-7 w-7" />
      </span>
      <h1 className="font-display text-3xl font-extrabold text-ink">Something went wrong on this page</h1>
      <p className="text-ink-soft">
        Your data is safe. Try again, and if it keeps happening, check that the PolicyGPT server is running.
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <button type="button" onClick={reset} className="btn-primary cursor-pointer">
          <RefreshCw className="h-5 w-5" /> Try again
        </button>
        <Link href="/" className="btn-ghost">Go to the home page</Link>
      </div>
    </div>
  );
}
