'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { SignedIn, SignedOut, UserButton, SignInButton, SignUpButton } from '@clerk/nextjs';
import { Sparkles, BarChart2, Compass, MessageSquare, User, ClipboardList } from 'lucide-react';

export default function Navbar() {
  const pathname = usePathname();

  const links = [
    { href: '/chat', label: 'AI Assistant', icon: MessageSquare },
    { href: '/explorer', label: 'Scheme Explorer', icon: Compass },
    { href: '/surveys', label: 'Research Survey', icon: ClipboardList },
    { href: '/dashboard', label: 'Dashboard', icon: User },
    { href: '/admin', label: 'Impact Analytics', icon: BarChart2 },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-slate-950/80 backdrop-blur-md">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center space-x-2 text-xl font-bold tracking-tight text-white hover:opacity-90">
          <span className="bg-gradient-to-r from-indigo-400 via-sky-400 to-purple-500 bg-clip-text text-transparent">
            PolicyGPT
          </span>
          <Sparkles className="h-4 w-4 text-sky-400 animate-pulse" />
        </Link>

        {/* Navigation links */}
        <nav className="hidden md:flex items-center space-x-1 text-sm font-medium">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Auth Buttons */}
        <div className="flex items-center space-x-2">
          <SignedIn>
            <UserButton afterSignOutUrl="/" />
          </SignedIn>
          <SignedOut>
            <SignInButton mode="modal">
              <button className="cursor-pointer text-xs font-semibold text-slate-300 hover:text-white px-3 py-2 rounded-lg hover:bg-white/5 transition-colors">
                Sign In
              </button>
            </SignInButton>
            <SignUpButton mode="modal">
              <button className="cursor-pointer text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-lg shadow-md transition-colors">
                Sign Up
              </button>
            </SignUpButton>
          </SignedOut>
        </div>
      </div>
    </header>
  );
}
