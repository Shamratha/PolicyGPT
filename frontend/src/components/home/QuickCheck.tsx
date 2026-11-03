'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { Briefcase, GraduationCap, Landmark, MapPin, Sparkles, UserCheck } from 'lucide-react';

export interface SchemeCard {
  id: string;
  title: string;
  state: string;
  category: string | null;
  benefits: string | null;
  is_for_women: boolean;
  is_for_students: boolean;
  is_for_startups: boolean;
  is_for_farmers: boolean;
}

const PERSONAS = [
  { key: 'is_for_students', label: 'Student', icon: GraduationCap },
  { key: 'is_for_farmers', label: 'Farmer', icon: Landmark },
  { key: 'is_for_women', label: 'Woman entrepreneur', icon: UserCheck },
  { key: 'is_for_startups', label: 'Startup founder', icon: Briefcase },
] as const;

type PersonaKey = (typeof PERSONAS)[number]['key'];

const STATES = ['Karnataka', 'Maharashtra', 'Tamil Nadu', 'Kerala', 'Delhi', 'Uttar Pradesh', 'Other state'];

export default function QuickCheck({ schemes, offline }: { schemes: SchemeCard[]; offline: boolean }) {
  const [persona, setPersona] = useState<PersonaKey>('is_for_women');
  const [state, setState] = useState('Karnataka');

  const matches = useMemo(
    () =>
      schemes.filter((s) => {
        const stateOk = s.state === 'Central' || s.state.toLowerCase() === state.toLowerCase();
        const anyTarget = s.is_for_students || s.is_for_farmers || s.is_for_women || s.is_for_startups;
        const personaOk = s[persona] || (!anyTarget && s.state !== 'Central');
        return stateOk && personaOk;
      }),
    [schemes, persona, state],
  );

  const resultKey = `${persona}-${state}`;

  return (
    <div className="relative rounded-3xl border-2 border-ink bg-paper shadow-[10px_10px_0_var(--color-chakra-tint)]">
      <div className="flex items-center justify-between border-b-2 border-ink px-6 py-4">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-marigold" />
          <span className="font-display text-lg font-bold">Quick check</span>
        </div>
        <span className="text-sm text-ink-mute">Live from the scheme database</span>
      </div>

      <div className="space-y-5 px-6 py-5">
        <fieldset>
          <legend className="mb-2 text-sm font-bold text-ink-soft">I am a</legend>
          <div className="grid grid-cols-2 gap-2">
            {PERSONAS.map(({ key, label, icon: Icon }) => {
              const active = persona === key;
              return (
                <button
                  key={key}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setPersona(key)}
                  className={`flex cursor-pointer items-center gap-2 rounded-xl border-2 px-3 py-2.5 text-left text-[15px] font-bold transition-colors ${
                    active ? 'border-chakra bg-chakra text-white' : 'border-line text-ink hover:border-ink'
                  }`}
                >
                  <Icon className={`h-4 w-4 shrink-0 ${active ? 'text-marigold' : 'text-chakra'}`} />
                  {label}
                </button>
              );
            })}
          </div>
        </fieldset>

        <label className="block">
          <span className="mb-2 flex items-center gap-1.5 text-sm font-bold text-ink-soft">
            <MapPin className="h-4 w-4" /> I live in
          </span>
          <select
            value={state}
            onChange={(e) => setState(e.target.value)}
            className="w-full cursor-pointer rounded-xl border-2 border-line bg-paper px-3 py-2.5 text-[15px] font-bold text-ink focus:border-chakra focus:outline-none"
          >
            {STATES.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="relative min-h-[196px] border-t-2 border-dashed border-line bg-mist/60 px-6 py-5 rounded-b-3xl">
        {offline ? (
          <p className="text-ink-mute">Start the backend on port 8000 to see live matches.</p>
        ) : (
          <div key={resultKey} className="result-in space-y-2">
            <p className="text-sm font-bold text-ink-soft">
              {matches.length === 0
                ? 'No exact match yet - ask PolicyGPT for alternatives.'
                : `${matches.length} scheme${matches.length > 1 ? 's' : ''} you can look at`}
            </p>
            {matches.slice(0, 3).map((s) => (
              <Link
                key={s.id}
                href={`/explorer?id=${s.id}`}
                className="group flex items-center justify-between gap-3 rounded-xl border border-line bg-paper px-4 py-3 hover:border-chakra"
              >
                <span className="min-w-0">
                  <span className="block truncate font-display text-[17px] font-bold text-ink group-hover:text-chakra">{s.title}</span>
                  <span className="block truncate text-sm text-ink-mute">
                    {s.state} · {s.category || 'General'}
                  </span>
                </span>
                <span className="shrink-0 rounded-md bg-chakra-tint px-2 py-1 text-xs font-bold text-chakra">View</span>
              </Link>
            ))}
            {matches.length > 0 && (
              <div className="pointer-events-none absolute -right-3 -top-6">
                <div className="stamp text-lg">MATCH FOUND</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
