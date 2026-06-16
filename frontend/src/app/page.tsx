import Link from 'next/link';
import { Compass, Sparkles, ShieldCheck, ClipboardCheck, Users, Award, Landmark, RefreshCw } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="flex flex-col space-y-24 py-10">
      {/* 1. Hero Section */}
      <section className="text-center max-w-4xl mx-auto space-y-6 pt-10">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-400 text-xs font-semibold animate-pulse">
          <span>SaaS Platform Live</span>
          <Sparkles className="h-3 w-3" />
        </div>
        <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight">
          Your AI Guide to{' '}
          <span className="bg-gradient-to-r from-indigo-400 via-sky-400 to-purple-500 bg-clip-text text-transparent">
            Government Opportunities
          </span>
        </h1>
        <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
          PolicyGPT aggregates welfare schemes, startup grants, and scholarships. Undergo automated eligibility audits and get step-by-step application blueprints instantly.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            href="/chat"
            className="w-full sm:w-auto px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/25 transition-all duration-300 hover:scale-[1.02]"
          >
            Start Chatting
          </Link>
          <Link
            href="/explorer"
            className="w-full sm:w-auto px-8 py-3 rounded-xl border border-white/10 hover:border-white/20 bg-white/5 hover:bg-white/10 text-slate-200 font-semibold text-sm transition-all duration-300 hover:scale-[1.02]"
          >
            Explore Schemes
          </Link>
        </div>
      </section>

      {/* 2. Features Grid */}
      <section className="space-y-12">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <h2 className="text-3xl font-bold tracking-tight">Features Crafted for Citizens</h2>
          <p className="text-sm text-slate-400">
            Simplifying complex government documentation and regulatory criteria using cutting-edge AI.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1 */}
          <div className="glass-panel glass-panel-hover p-6 rounded-2xl flex flex-col space-y-4">
            <div className="p-3 bg-indigo-500/10 rounded-xl text-indigo-400 w-fit">
              <Sparkles className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold">AI Assistant</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Conversational RAG agent providing precise, non-hallucinatory scheme matching backed by direct PDF references.
            </p>
          </div>

          {/* Card 2 */}
          <div className="glass-panel glass-panel-hover p-6 rounded-2xl flex flex-col space-y-4">
            <div className="p-3 bg-sky-500/10 rounded-xl text-sky-400 w-fit">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold">Eligibility Engine</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Pipes demographic profile rules and GPT analysis to evaluate matching criteria (age, gender, location, income).
            </p>
          </div>

          {/* Card 3 */}
          <div className="glass-panel glass-panel-hover p-6 rounded-2xl flex flex-col space-y-4">
            <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400 w-fit">
              <ClipboardCheck className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold">Document Checklists</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Generates customized required filing guidelines and updates document progress trackers dynamically.
            </p>
          </div>

          {/* Card 4 */}
          <div className="glass-panel glass-panel-hover p-6 rounded-2xl flex flex-col space-y-4">
            <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400 w-fit">
              <RefreshCw className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold">Multilingual Translation</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Supports Kannada, Hindi, and English query queries using automated LLM translation wrappers.
            </p>
          </div>
        </div>
      </section>

      {/* 3. Impact Section */}
      <section className="glass-panel p-8 sm:p-12 rounded-3xl bg-indigo-950/20 border-indigo-500/10">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
          <div className="space-y-2">
            <div className="text-4xl sm:text-5xl font-extrabold text-white">10k+</div>
            <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Citizens Assisted</p>
          </div>
          <div className="space-y-2">
            <div className="text-4xl sm:text-5xl font-extrabold text-indigo-400">400+</div>
            <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Schemes Indexed</p>
          </div>
          <div className="space-y-2">
            <div className="text-4xl sm:text-5xl font-extrabold text-sky-400">92%</div>
            <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Matching Success Rate</p>
          </div>
          <div className="space-y-2">
            <div className="text-4xl sm:text-5xl font-extrabold text-purple-400">₹12Cr+</div>
            <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Subsidy Volume Guided</p>
          </div>
        </div>
      </section>

      {/* 4. Testimonials Section */}
      <section className="space-y-12">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <h2 className="text-3xl font-bold tracking-tight font-sans">Empowering Communities</h2>
          <p className="text-sm text-slate-400 font-sans">
            Hear from startup founders, college students, and farm owners who found opportunities via PolicyGPT.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
            <p className="text-xs text-slate-300 leading-relaxed italic">
              "Being a 22-year-old female engineering graduate from Karnataka, I had no idea about the Udyogini Scheme. PolicyGPT verified my criteria and mapped out the Tahsildar filing requirements. Saved us months of legal consultation."
            </p>
            <div className="flex items-center space-x-3 pt-6">
              <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500" />
              <div>
                <h4 className="text-xs font-bold text-white">Ananya R.</h4>
                <p className="text-[10px] text-slate-500">Startup Founder, Bangalore</p>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
            <p className="text-xs text-slate-300 leading-relaxed italic">
              "I wanted to apply for agriculture loan subsidies but the official PDF guidelines were 80 pages long. The PolicyGPT conversational RAG gave me the bullet points and document checklists in under 10 seconds."
            </p>
            <div className="flex items-center space-x-3 pt-6">
              <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-sky-500 to-indigo-500" />
              <div>
                <h4 className="text-xs font-bold text-white">Ramesh Gowda</h4>
                <p className="text-[10px] text-slate-500">Marginal Farmer, Mandya</p>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
            <p className="text-xs text-slate-300 leading-relaxed italic">
              "Applying for professional course scholarships was a nightmare. PolicyGPT verified that I was eligible for the Rajiv Gandhi scholarship, compiled my documents tracker, and gave the State Scholarship Portal registry links."
            </p>
            <div className="flex items-center space-x-3 pt-6">
              <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-purple-500 to-pink-500" />
              <div>
                <h4 className="text-xs font-bold text-white">Amit Kumar</h4>
                <p className="text-[10px] text-slate-500">Student, Mumbai University</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. CTA Section */}
      <section className="text-center py-10 space-y-6">
        <h2 className="text-3xl font-extrabold text-white">Ready to Discover Your Opportunities?</h2>
        <p className="text-sm text-slate-400 max-w-md mx-auto">
          Create an account to save matching policies, evaluate eligibility, and track your applications.
        </p>
        <Link
          href="/chat"
          className="inline-block px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/25 transition-all duration-300 hover:scale-[1.02]"
        >
          Get Started Now
        </Link>
      </section>
    </div>
  );
}
