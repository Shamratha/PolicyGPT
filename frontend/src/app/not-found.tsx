import Link from 'next/link';
import { Compass } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center gap-5 py-20 text-center">
      <p className="font-display text-7xl font-extrabold text-chakra">404</p>
      <h1 className="font-display text-3xl font-extrabold text-ink">This page doesn&apos;t exist</h1>
      <p className="text-ink-soft">The link may be old or mistyped. You can browse every scheme from the explorer.</p>
      <div className="flex flex-wrap justify-center gap-3">
        <Link href="/explorer" className="btn-primary">
          <Compass className="h-5 w-5" /> Browse schemes
        </Link>
        <Link href="/" className="btn-ghost">Home page</Link>
      </div>
    </div>
  );
}
