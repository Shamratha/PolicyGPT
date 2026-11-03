import Link from 'next/link';
import { Landmark } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="mt-auto w-full border-t border-line bg-mist">
      <div className="container mx-auto grid max-w-7xl gap-8 px-4 py-10 text-sm sm:grid-cols-[2fr_1fr_2fr] sm:px-6">
        <div className="space-y-3">
          <div className="flex items-center gap-2 font-display text-lg font-extrabold text-ink">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-chakra text-white">
              <Landmark className="h-4 w-4" />
            </span>
            PolicyGPT
          </div>
          <p className="max-w-sm text-ink-mute">
            Helps citizens find central and state schemes, check eligibility and prepare their applications.
          </p>
        </div>
        <nav className="flex flex-col gap-2 text-ink-soft" aria-label="Footer">
          <Link href="/chat" className="hover:text-chakra">Ask PolicyGPT</Link>
          <Link href="/explorer" className="hover:text-chakra">Browse schemes</Link>
          <Link href="/dashboard" className="hover:text-chakra">My dashboard</Link>
          <Link href="/admin" className="hover:text-chakra">Insights</Link>
        </nav>
        <p className="text-ink-mute">
          PolicyGPT gives guidance, not a legal decision. Confirm eligibility and deadlines on the official
          government portal before you apply.
        </p>
      </div>
      <div className="border-t border-line py-4 text-center text-xs text-ink-mute">
        © {new Date().getFullYear()} PolicyGPT
      </div>
    </footer>
  );
}
