'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { SignedIn, SignedOut, UserButton, SignInButton, SignUpButton } from '@clerk/nextjs';
import { BarChart2, Compass, MessageSquare, User, ClipboardList, Landmark, UserCheck } from 'lucide-react';

const links = [
  { href: '/chat', label: 'Ask PolicyGPT', icon: MessageSquare },
  { href: '/explorer', label: 'Schemes', icon: Compass },
  { href: '/dashboard', label: 'My dashboard', icon: User },
  { href: '/surveys', label: 'Survey', icon: ClipboardList },
  { href: '/admin', label: 'Insights', icon: BarChart2 },
];

export default function Navbar() {
  const pathname = usePathname();
  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-line bg-paper/90 backdrop-blur">
      {/* tricolour hairline */}
      <div className="flex h-1 w-full" aria-hidden="true">
        <span className="flex-1 bg-marigold" />
        <span className="flex-1 bg-paper" />
        <span className="flex-1 bg-leaf" />
      </div>
      <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link href="/" className="flex shrink-0 items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-chakra text-white">
            <Landmark className="h-5 w-5" />
          </span>
          <span className="font-display text-xl font-extrabold tracking-tight text-ink">PolicyGPT</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
          {links.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              aria-current={isActive(href) ? 'page' : undefined}
              className={`relative flex items-center gap-1.5 rounded-lg px-3 py-2 text-[15px] font-bold transition-colors ${
                isActive(href) ? 'text-chakra' : 'text-ink-soft hover:bg-mist hover:text-ink'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
              {isActive(href) && <span className="absolute inset-x-3 -bottom-[13px] h-[3px] rounded-full bg-chakra" />}
            </Link>
          ))}
        </nav>

        <div className="flex shrink-0 items-center gap-2">
          <SignedIn>
            <Link
              href="/profile"
              className={`hidden items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-bold sm:flex ${
                isActive('/profile') ? 'bg-chakra-tint text-chakra' : 'text-ink-soft hover:bg-mist hover:text-ink'
              }`}
            >
              <UserCheck className="h-4 w-4" />
              My profile
            </Link>
            <UserButton />
          </SignedIn>
          <SignedOut>
            <SignInButton mode="modal">
              <button className="cursor-pointer rounded-lg px-3 py-2 text-sm font-bold text-ink-soft hover:bg-mist hover:text-ink">
                Sign in
              </button>
            </SignInButton>
            <SignUpButton mode="modal">
              <button className="btn-primary cursor-pointer !px-4 !py-2 !text-sm">Create account</button>
            </SignUpButton>
          </SignedOut>
        </div>
      </div>

      <nav className="no-scrollbar flex gap-1 overflow-x-auto border-t border-line px-3 py-2 md:hidden" aria-label="Main">
        {links.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={`flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-bold ${
              isActive(href) ? 'bg-chakra-tint text-chakra' : 'text-ink-soft'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
