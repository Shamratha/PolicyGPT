'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { BarChart2, Check, ClipboardCheck, Compass, Landmark, MessageSquare, ShieldCheck, UserCheck, X } from 'lucide-react';
import { getApi } from '@/services/api';
import ChakraWheel from '@/components/home/ChakraWheel';
import CountUp from '@/components/home/CountUp';
import QuickCheck, { type SchemeCard } from '@/components/home/QuickCheck';

interface Summary {
  users_served: number;
  schemes_indexed: number;
  searches_performed: number;
  eligibility_success_rate: number;
}

const RULES = [
  { label: 'Age 24', rule: '18 to 55', ok: true },
  { label: 'State: Karnataka', rule: 'Karnataka', ok: true },
  { label: 'Income ₹1.2 lakh', rule: 'up to ₹1.5 lakh', ok: true },
  { label: 'Gender: Male', rule: 'Female only', ok: false },
];

const DOCS = [
  { name: 'Aadhaar card', done: true },
  { name: 'Income certificate', done: true },
  { name: 'Caste certificate', done: false },
];

const BARS = [72, 48, 88, 35, 61, 80];

const STEPS = [
  { title: 'Fill in your profile', text: 'Age, state, income, occupation, and whether you study or run a business.' },
  { title: 'Ask or browse', text: 'Chat with PolicyGPT or open the scheme list to see what fits you.' },
  { title: 'Check and apply', text: 'Get a clear verdict, the documents you need and the steps to apply.' },
];

export default function LandingPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [schemes, setSchemes] = useState<SchemeCard[]>([]);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const api = getApi();
        const [sumRes, schemeRes] = await Promise.all([api.get('/api/analytics/summary'), api.get('/api/schemes')]);
        if (!active) return;
        setSummary(sumRes.data);
        setSchemes(schemeRes.data);
      } catch {
        if (active) setOffline(true);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, []);

  const ticker = schemes.length ? [...schemes, ...schemes, ...schemes] : [];

  return (
    <div className="flex flex-col gap-24 pb-10 sm:gap-32">
      {/* ================================================================ HERO */}
      <section className="relative -mx-4 overflow-hidden px-4 pb-6 pt-6 sm:pt-12">
        <ChakraWheel className="chakra-spin pointer-events-none absolute -right-40 -top-24 h-[640px] w-[640px] text-chakra opacity-[0.07]" />
        <div className="relative grid items-center gap-14 lg:grid-cols-[1.1fr_1fr]">
          <div className="space-y-8">
            <p className="inline-flex items-center gap-2 rounded-full border-2 border-ink bg-marigold-tint px-4 py-1.5 text-sm font-bold text-ink">
              <Landmark className="h-4 w-4 text-chakra" />
              Central and state schemes, explained simply
            </p>
            <h1 className="font-display text-[2.9rem] font-extrabold leading-[0.98] text-ink sm:text-7xl xl:text-[5.5rem]">
              Every scheme you deserve,{' '}
              <span className="relative whitespace-nowrap">
                <span className="relative z-10">found in seconds.</span>
                <svg className="absolute -bottom-2 left-0 z-0 h-5 w-full text-marigold" viewBox="0 0 300 20" preserveAspectRatio="none" aria-hidden="true">
                  <path d="M2 14 C 80 4, 200 4, 298 12" stroke="currentColor" strokeWidth="8" fill="none" strokeLinecap="round" />
                </svg>
              </span>
            </h1>
            <p className="max-w-xl text-lg leading-relaxed text-ink-soft sm:text-xl">
              PolicyGPT reads the fine print for you. Tell it who you are, and it shows the scholarships, loans
              and subsidies you qualify for, the documents to keep ready, and how to apply.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Link href="/chat" className="btn-primary !px-6 !py-3.5 !text-base">
                <MessageSquare className="h-5 w-5" /> Ask PolicyGPT
              </Link>
              <Link href="/explorer" className="btn-ghost !px-6 !py-3.5 !text-base">
                <Compass className="h-5 w-5" /> Browse all schemes
              </Link>
            </div>
            <p className="text-sm text-ink-mute">
              Ask in <span className="font-bold text-ink">English</span>,{' '}
              <span className="font-bold text-ink" lang="hi">हिन्दी</span> or{' '}
              <span className="font-bold text-ink" lang="kn">ಕನ್ನಡ</span>
            </p>
          </div>

          <QuickCheck schemes={schemes} offline={offline} />
        </div>
      </section>

      {/* ================================================================ NUMBERS + TICKER */}
      <section className="space-y-10">
        <dl className="grid grid-cols-2 overflow-hidden rounded-3xl border-2 border-ink bg-paper lg:grid-cols-4">
          {[
            { label: 'schemes in the database', value: summary?.schemes_indexed ?? null, tone: 'bg-paper' },
            { label: 'citizens registered', value: summary?.users_served ?? null, tone: 'bg-marigold-tint' },
            { label: 'questions answered', value: summary?.searches_performed ?? null, tone: 'bg-chakra-tint' },
            { label: 'eligibility checks matched', value: summary ? Math.round(summary.eligibility_success_rate) : null, tone: 'bg-leaf-tint', suffix: '%' },
          ].map(({ label, value, tone, suffix }, i) => (
            <div
              key={label}
              className={`${tone} px-6 py-8 ${i % 2 === 0 ? 'border-r-2 border-ink' : ''} ${i < 2 ? 'border-b-2 border-ink lg:border-b-0' : ''} ${i === 1 ? 'lg:border-r-2' : ''}`}
            >
              <dd className="font-display text-5xl font-extrabold text-ink sm:text-6xl">
                <CountUp value={value} suffix={suffix} />
              </dd>
              <dt className="mt-2 font-bold text-ink-soft">{label}</dt>
            </div>
          ))}
        </dl>

        {ticker.length > 0 && (
          <div className="marquee -mx-4 overflow-hidden border-y-2 border-ink bg-chakra py-4">
            <div className="marquee-track">
              {ticker.map((s, i) => (
                <Link
                  key={`${s.id}-${i}`}
                  href={`/explorer?id=${s.id}`}
                  className="flex shrink-0 items-center gap-3 font-display text-xl font-bold text-white hover:text-marigold"
                >
                  <ChakraWheel className="h-6 w-6 text-marigold" />
                  {s.title}
                </Link>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* ================================================================ FEATURE BENTO */}
      <section className="space-y-10">
        <div className="max-w-2xl space-y-3">
          <h2 className="font-display text-4xl font-extrabold text-ink sm:text-5xl">One place, start to finish</h2>
          <p className="text-lg text-ink-soft">
            Each tool below is a working part of PolicyGPT. Open any of them to try it.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-6">
          {/* Chat */}
          <Link href="/chat" className="tile md:col-span-4 bg-chakra text-white">
            <div className="space-y-2">
              <MessageSquare className="h-7 w-7 text-marigold" />
              <h3 className="font-display text-2xl font-bold">Ask in your own words</h3>
              <p className="max-w-md text-white/80">Every answer names the schemes it comes from, so you can check the source.</p>
            </div>
            <div className="mt-6 space-y-3">
              <div className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-white px-4 py-2.5 text-ink">
                Scholarships for engineering students from low-income families?
              </div>
              <div className="w-fit max-w-[90%] rounded-2xl rounded-bl-md border border-white/25 bg-white/10 px-4 py-3">
                The <span className="font-bold">Rajiv Gandhi Scholarship for Technical Studies</span> waives 100% of tuition and pays
                ₹2,000 a month to Karnataka students with family income up to ₹2.5 lakh <sup className="rounded bg-marigold px-1 text-[0.7em] font-bold text-ink">1</sup>
              </div>
            </div>
          </Link>

          {/* Languages */}
          <div className="tile md:col-span-2 bg-marigold-tint">
            <h3 className="font-display text-2xl font-bold text-ink">Your language</h3>
            <div className="mt-4 space-y-1 font-display font-extrabold leading-tight text-ink [&>p]:text-3xl xl:[&>p]:text-4xl [&>p]:break-words">
              <p>Hello</p>
              <p className="text-chakra" lang="hi">नमस्ते</p>
              <p className="text-leaf" lang="kn">ನಮಸ್ಕಾರ</p>
            </div>
          </div>

          {/* Eligibility */}
          <Link href="/explorer" className="tile md:col-span-3 bg-paper">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-7 w-7 text-leaf" />
              <h3 className="font-display text-2xl font-bold text-ink">See why, not just yes or no</h3>
            </div>
            <ul className="mt-5 divide-y divide-line rounded-xl border border-line">
              {RULES.map((r) => (
                <li key={r.label} className="flex items-center justify-between gap-3 px-4 py-2.5">
                  <span className="text-ink">{r.label}</span>
                  <span className={`flex items-center gap-1.5 text-sm font-bold ${r.ok ? 'text-leaf' : 'text-seal'}`}>
                    {r.ok ? <Check className="h-4 w-4" /> : <X className="h-4 w-4" />}
                    {r.rule}
                  </span>
                </li>
              ))}
            </ul>
          </Link>

          {/* Tracker */}
          <Link href="/dashboard" className="tile md:col-span-3 bg-paper">
            <div className="flex items-center gap-2">
              <ClipboardCheck className="h-7 w-7 text-chakra" />
              <h3 className="font-display text-2xl font-bold text-ink">Never miss a document</h3>
            </div>
            <div className="mt-5 space-y-3">
              {DOCS.map((d) => (
                <div key={d.name} className="flex items-center gap-3">
                  <span className={`flex h-6 w-6 items-center justify-center rounded-md border-2 ${d.done ? 'border-leaf bg-leaf text-white' : 'border-line'}`}>
                    {d.done && <Check className="h-4 w-4" />}
                  </span>
                  <span className={d.done ? 'text-ink-mute line-through' : 'text-ink'}>{d.name}</span>
                </div>
              ))}
              <div>
                <div className="mb-1 flex justify-between text-sm font-bold text-ink-soft">
                  <span>Ready to apply</span>
                  <span>66%</span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-mist">
                  <div className="h-full w-2/3 rounded-full bg-leaf" />
                </div>
              </div>
            </div>
          </Link>

          {/* Insights */}
          <Link href="/admin" className="tile md:col-span-4 bg-ink text-white">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
              <div className="space-y-2">
                <BarChart2 className="h-7 w-7 text-marigold" />
                <h3 className="font-display text-2xl font-bold">Insights for policy makers</h3>
                <p className="max-w-sm text-white/75">Awareness by state, common bottlenecks and underserved groups, exportable as a PDF report.</p>
              </div>
              <div className="flex h-32 items-end gap-2" aria-hidden="true">
                {BARS.map((h, i) => (
                  <span key={i} className="bar-grow w-6 rounded-t-md bg-marigold" style={{ height: `${h}%`, animationDelay: `${i * 80}ms` }} />
                ))}
              </div>
            </div>
          </Link>

          {/* Survey */}
          <Link href="/surveys" className="tile md:col-span-2 bg-leaf-tint">
            <h3 className="font-display text-2xl font-bold text-ink">Report what went wrong</h3>
            <p className="mt-2 text-ink-soft">How hard was applying?</p>
            <div className="mt-4 flex gap-2" aria-hidden="true">
              {[1, 2, 3, 4, 5].map((n) => (
                <span
                  key={n}
                  className={`flex h-10 w-10 items-center justify-center rounded-lg border-2 font-display text-lg font-bold ${
                    n === 4 ? 'border-ink bg-ink text-white' : 'border-ink/20 bg-paper text-ink'
                  }`}
                >
                  {n}
                </span>
              ))}
            </div>
          </Link>
        </div>
      </section>

      {/* ================================================================ HOW IT WORKS */}
      <section className="grid gap-12 lg:grid-cols-[1fr_1.4fr]">
        <div className="space-y-4">
          <h2 className="font-display text-4xl font-extrabold text-ink sm:text-5xl">Three steps to your first application</h2>
          <p className="text-lg text-ink-soft">Most people find a scheme worth applying for in under five minutes.</p>
        </div>
        <ol className="relative space-y-8 border-l-2 border-dashed border-ink/25 pl-10">
          {STEPS.map(({ title, text }, i) => (
            <li key={title} className="relative">
              <span className="absolute -left-[3.6rem] top-0 flex h-11 w-11 items-center justify-center rounded-full border-2 border-ink bg-marigold font-display text-xl font-extrabold text-ink">
                {i + 1}
              </span>
              <h3 className="font-display text-2xl font-bold text-ink">{title}</h3>
              <p className="mt-1 text-lg text-ink-soft">{text}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* ================================================================ CTA */}
      <section className="relative overflow-hidden rounded-[2rem] border-2 border-ink bg-chakra px-8 py-14 text-white sm:px-14">
        <ChakraWheel className="chakra-spin pointer-events-none absolute -bottom-32 -right-24 h-[420px] w-[420px] text-white opacity-10" />
        <div className="relative max-w-2xl space-y-6">
          <h2 className="font-display text-4xl font-extrabold leading-tight sm:text-5xl">
            Your profile takes a minute. The benefits can last years.
          </h2>
          <p className="text-lg text-white/80">
            Save your details once and every answer, match and eligibility check is tailored to you.
          </p>
          <Link
            href="/profile"
            className="inline-flex items-center gap-2 rounded-xl border-2 border-ink bg-marigold px-6 py-3.5 text-base font-bold text-ink shadow-[4px_4px_0_var(--color-ink)] transition-transform hover:-translate-y-0.5"
          >
            <UserCheck className="h-5 w-5" /> Set up my profile
          </Link>
        </div>
      </section>
    </div>
  );
}
