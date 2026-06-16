export default function Footer() {
  return (
    <footer className="w-full border-t border-white/5 bg-slate-950/40 py-6 text-center text-xs text-slate-500 mt-auto">
      <div className="container mx-auto px-4">
        <p className="mb-2">© {new Date().getFullYear()} PolicyGPT. Empowering citizens through AI-guided public service navigation.</p>
        <p className="text-slate-600">
          This is an independent policy matching engine grounded in official department schemes. 
          Answers should be verified against standard government portals.
        </p>
      </div>
    </footer>
  );
}
