'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@clerk/nextjs';
import { useMemo, useState } from 'react';
import { AlertTriangle, ArrowRight, CheckCircle2, Landmark, Loader, Plus, Save, X } from 'lucide-react';
import { getApi, getErrorMessage } from '@/services/api';

const CATEGORIES = ['Education', 'Business', 'Agriculture', 'Healthcare', 'Housing', 'Employment', 'Social Welfare', 'Women & Child', 'General'];
const STATES = [
  'Central', 'Andhra Pradesh', 'Assam', 'Bihar', 'Delhi', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
  'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Odisha', 'Punjab', 'Rajasthan', 'Tamil Nadu', 'Telangana',
  'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
];

type Field = 'age' | 'income' | 'gender' | 'state' | 'occupation' | 'education' | 'student_status' | 'startup_status';
type Op = '>=' | '<=' | '==' | '!=' | 'in';

const FIELD_INFO: Record<Field, { label: string; ops: Op[]; kind: 'number' | 'bool' | 'gender' | 'text'; placeholder: string }> = {
  age: { label: 'Age', ops: ['>=', '<=', '=='], kind: 'number', placeholder: '18' },
  income: { label: 'Annual family income (₹)', ops: ['<=', '>=', '=='], kind: 'number', placeholder: '250000' },
  gender: { label: 'Gender', ops: ['=='], kind: 'gender', placeholder: 'female' },
  state: { label: 'State', ops: ['==', 'in', '!='], kind: 'text', placeholder: 'karnataka' },
  occupation: { label: 'Occupation', ops: ['==', 'in', '!='], kind: 'text', placeholder: 'farmer' },
  education: { label: 'Education', ops: ['==', 'in', '!='], kind: 'text', placeholder: 'graduate' },
  student_status: { label: 'Is a student', ops: ['=='], kind: 'bool', placeholder: 'true' },
  startup_status: { label: 'Runs a startup / business', ops: ['=='], kind: 'bool', placeholder: 'true' },
};
const OP_LABEL: Record<Op, string> = { '>=': 'at least', '<=': 'at most', '==': 'is', '!=': 'is not', in: 'is one of' };

interface Rule { id: number; field_name: Field; operator: Op; expected_value: string }

const emptyForm = {
  title: '', description: '', benefits: '', eligibility_criteria: '', required_documents: '', application_steps: '',
  state: 'Central', category: 'Education', ministry: '', deadline: '',
  is_for_women: false, is_for_students: false, is_for_startups: false, is_for_farmers: false,
};

function ruleError(r: Rule): string | null {
  const v = r.expected_value.trim();
  const info = FIELD_INFO[r.field_name];
  if (!v) return 'Enter a value';
  if (info.kind === 'number') {
    const n = Number(v);
    if (!Number.isFinite(n)) return 'Must be a number';
    if (r.field_name === 'age' && (!Number.isInteger(n) || n < 0 || n > 120)) return 'Age must be 0-120';
    if (n < 0) return 'Cannot be negative';
  }
  return null;
}

export default function NewSchemePage() {
  const { getToken } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState(emptyForm);
  const [rules, setRules] = useState<Rule[]>([]);
  const [nextId, setNextId] = useState(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [created, setCreated] = useState<{ id: string; title: string } | null>(null);

  const today = new Date().toISOString().slice(0, 10);

  const formErrors = useMemo(() => {
    const e: Record<string, string> = {};
    if (form.title.trim().length > 0 && form.title.trim().length < 3) e.title = 'At least 3 characters';
    if (form.description.trim().length > 0 && form.description.trim().length < 20) e.description = `At least 20 characters (${form.description.trim().length}/20)`;
    if (form.deadline && form.deadline < today) e.deadline = 'Deadline cannot be in the past';
    const minAge = rules.find((r) => r.field_name === 'age' && r.operator === '>=');
    const maxAge = rules.find((r) => r.field_name === 'age' && r.operator === '<=');
    if (minAge && maxAge && Number(minAge.expected_value) > Number(maxAge.expected_value)) e.rules = 'Minimum age is higher than maximum age';
    return e;
  }, [form, rules, today]);

  const canSubmit =
    form.title.trim().length >= 3 && form.description.trim().length >= 20 && Object.keys(formErrors).length === 0 &&
    rules.every((r) => !ruleError(r)) && !saving;

  const set = (key: keyof typeof emptyForm, value: string | boolean) => setForm((f) => ({ ...f, [key]: value }));

  const addRule = () => {
    setRules((rs) => [...rs, { id: nextId, field_name: 'age', operator: '>=', expected_value: '' }]);
    setNextId((n) => n + 1);
  };
  const updateRule = (id: number, patch: Partial<Rule>) =>
    setRules((rs) =>
      rs.map((r) => {
        if (r.id !== id) return r;
        const next = { ...r, ...patch };
        if (patch.field_name) {
          next.operator = FIELD_INFO[patch.field_name].ops[0];
          next.expected_value = FIELD_INFO[patch.field_name].kind === 'bool' ? 'true' : FIELD_INFO[patch.field_name].kind === 'gender' ? 'female' : '';
        }
        return next;
      }),
    );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    setSaving(true);
    setError('');
    try {
      const token = await getToken();
      const payload = {
        ...form,
        deadline: form.deadline || null,
        rules: rules.map(({ field_name, operator, expected_value }) => ({ field_name, operator, expected_value })),
      };
      const res = await getApi(token).post('/api/schemes', payload);
      setCreated({ id: res.data.id, title: res.data.title });
      setForm(emptyForm);
      setRules([]);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(getErrorMessage(err, 'Could not save the scheme.'));
    } finally {
      setSaving(false);
    }
  };

  const input = 'w-full rounded-xl border-2 border-line bg-paper px-3.5 py-2.5 text-ink placeholder:text-ink-mute/70 focus:border-chakra focus:outline-none';
  const label = 'mb-1.5 block font-bold text-ink';
  const hint = 'mt-1 text-sm text-ink-mute';
  const err = 'mt-1 text-sm font-bold text-seal';

  return (
    <div className="mx-auto max-w-4xl space-y-8 py-4">
      <div className="space-y-2">
        <Link href="/explorer" className="text-sm font-bold text-chakra hover:underline">Back to schemes</Link>
        <h1 className="font-display text-4xl font-extrabold text-ink">Add a scheme or scholarship</h1>
        <p className="max-w-2xl text-ink-soft">
          New schemes appear straight away in the scheme list, the Quick check, PolicyGPT&apos;s answers and
          eligibility checks. Add eligibility rules so PolicyGPT can tell people whether they qualify.
        </p>
      </div>

      {created && (
        <div className="flex flex-col gap-3 rounded-2xl border-2 border-leaf bg-leaf-tint p-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="flex items-center gap-2 font-bold text-leaf">
            <CheckCircle2 className="h-5 w-5" /> &ldquo;{created.title}&rdquo; was added.
          </p>
          <div className="flex gap-2">
            <button type="button" onClick={() => router.push(`/explorer?id=${created.id}`)} className="btn-primary cursor-pointer !py-2">
              View scheme <ArrowRight className="h-4 w-4" />
            </button>
            <button type="button" onClick={() => setCreated(null)} className="btn-ghost cursor-pointer !py-2">Add another</button>
          </div>
        </div>
      )}

      {error && (
        <div role="alert" className="flex items-start gap-2 rounded-2xl border-2 border-seal bg-seal-tint p-4 font-bold text-seal">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" /> {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8" noValidate>
        {/* Basics */}
        <section className="glass-panel space-y-5 rounded-2xl p-6 sm:p-8">
          <h2 className="flex items-center gap-2 font-display text-2xl font-bold text-ink">
            <Landmark className="h-6 w-6 text-chakra" /> Basic details
          </h2>
          <div>
            <label htmlFor="title" className={label}>Scheme name *</label>
            <input id="title" className={input} maxLength={200} value={form.title} onChange={(e) => set('title', e.target.value)} placeholder="Karnataka Vidya Siri Scholarship" />
            {formErrors.title && <p className={err}>{formErrors.title}</p>}
          </div>
          <div>
            <label htmlFor="description" className={label}>What it is and who it helps *</label>
            <textarea id="description" rows={3} maxLength={5000} className={input} value={form.description} onChange={(e) => set('description', e.target.value)} placeholder="Food and accommodation support for backward-class students studying in Karnataka." />
            {formErrors.description ? <p className={err}>{formErrors.description}</p> : <p className={hint}>At least 20 characters.</p>}
          </div>
          <div className="grid gap-5 sm:grid-cols-3">
            <div>
              <label htmlFor="state" className={label}>State</label>
              <select id="state" className={input} value={form.state} onChange={(e) => set('state', e.target.value)}>
                {STATES.map((s) => <option key={s} value={s}>{s === 'Central' ? 'Central (all India)' : s}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="category" className={label}>Category</label>
              <select id="category" className={input} value={form.category} onChange={(e) => set('category', e.target.value)}>
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="deadline" className={label}>Last date to apply</label>
              <input id="deadline" type="date" min={today} className={input} value={form.deadline} onChange={(e) => set('deadline', e.target.value)} />
              {formErrors.deadline && <p className={err}>{formErrors.deadline}</p>}
            </div>
          </div>
          <div>
            <label htmlFor="ministry" className={label}>Department or ministry</label>
            <input id="ministry" className={input} maxLength={200} value={form.ministry} onChange={(e) => set('ministry', e.target.value)} placeholder="Backward Classes Welfare Department, Karnataka" />
          </div>
          <fieldset>
            <legend className={label}>Meant for</legend>
            <div className="flex flex-wrap gap-2">
              {([['is_for_students', 'Students'], ['is_for_women', 'Women'], ['is_for_farmers', 'Farmers'], ['is_for_startups', 'Startups / businesses']] as const).map(([key, text]) => (
                <label key={key} className={`flex cursor-pointer items-center gap-2 rounded-xl border-2 px-3.5 py-2 font-bold ${form[key] ? 'border-chakra bg-chakra-tint text-chakra' : 'border-line text-ink-soft hover:border-ink'}`}>
                  <input type="checkbox" className="accent-[var(--color-chakra)]" checked={form[key]} onChange={(e) => set(key, e.target.checked)} />
                  {text}
                </label>
              ))}
            </div>
          </fieldset>
        </section>

        {/* Details */}
        <section className="glass-panel space-y-5 rounded-2xl p-6 sm:p-8">
          <h2 className="font-display text-2xl font-bold text-ink">What applicants need to know</h2>
          {([
            ['benefits', 'Benefits', 'Rs. 1,500 per month for 10 months'],
            ['eligibility_criteria', 'Eligibility in plain words', 'Karnataka students aged 17-30 with family income up to Rs. 2.5 lakh'],
            ['required_documents', 'Documents needed (comma separated)', 'Aadhaar card, Income certificate, Caste certificate'],
            ['application_steps', 'How to apply', '1. Register on the SSP portal. 2. Fill the form. 3. Submit documents to your college.'],
          ] as const).map(([key, text, ph]) => (
            <div key={key}>
              <label htmlFor={key} className={label}>{text}</label>
              <textarea id={key} rows={2} maxLength={3000} className={input} value={form[key]} onChange={(e) => set(key, e.target.value)} placeholder={ph} />
            </div>
          ))}
        </section>

        {/* Rules */}
        <section className="glass-panel space-y-5 rounded-2xl p-6 sm:p-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="font-display text-2xl font-bold text-ink">Eligibility rules</h2>
              <p className="text-ink-soft">Used for the automatic Eligible / Not eligible check. Optional, up to 20.</p>
            </div>
            <button type="button" onClick={addRule} disabled={rules.length >= 20} className="btn-ghost cursor-pointer !py-2 disabled:opacity-50">
              <Plus className="h-4 w-4" /> Add rule
            </button>
          </div>

          {rules.length === 0 && (
            <p className="rounded-xl border-2 border-dashed border-line px-4 py-6 text-center text-ink-mute">
              No rules yet. Without rules, everyone is shown as &ldquo;Eligible&rdquo; for this scheme.
            </p>
          )}

          <ul className="space-y-3">
            {rules.map((r) => {
              const info = FIELD_INFO[r.field_name];
              const problem = ruleError(r);
              return (
                <li key={r.id} className="rounded-xl border-2 border-line p-3">
                  <div className="grid items-center gap-2 sm:grid-cols-[1.3fr_1fr_1.3fr_auto]">
                    <select aria-label="Profile field" className={input} value={r.field_name} onChange={(e) => updateRule(r.id, { field_name: e.target.value as Field })}>
                      {(Object.keys(FIELD_INFO) as Field[]).map((f) => <option key={f} value={f}>{FIELD_INFO[f].label}</option>)}
                    </select>
                    <select aria-label="Condition" className={input} value={r.operator} onChange={(e) => updateRule(r.id, { operator: e.target.value as Op })}>
                      {info.ops.map((o) => <option key={o} value={o}>{OP_LABEL[o]}</option>)}
                    </select>
                    {info.kind === 'bool' ? (
                      <select aria-label="Value" className={input} value={r.expected_value} onChange={(e) => updateRule(r.id, { expected_value: e.target.value })}>
                        <option value="true">Yes</option>
                        <option value="false">No</option>
                      </select>
                    ) : info.kind === 'gender' ? (
                      <select aria-label="Value" className={input} value={r.expected_value} onChange={(e) => updateRule(r.id, { expected_value: e.target.value })}>
                        <option value="female">Female</option>
                        <option value="male">Male</option>
                        <option value="other">Other</option>
                      </select>
                    ) : (
                      <input
                        aria-label="Value"
                        className={input}
                        inputMode={info.kind === 'number' ? 'numeric' : 'text'}
                        value={r.expected_value}
                        placeholder={r.operator === 'in' ? 'karnataka, kerala' : info.placeholder}
                        onChange={(e) => updateRule(r.id, { expected_value: e.target.value })}
                      />
                    )}
                    <button type="button" aria-label="Remove rule" onClick={() => setRules((rs) => rs.filter((x) => x.id !== r.id))} className="flex h-11 w-11 cursor-pointer items-center justify-center rounded-xl border-2 border-line text-ink-mute hover:border-seal hover:text-seal">
                      <X className="h-5 w-5" />
                    </button>
                  </div>
                  {problem && r.expected_value !== '' && <p className={err}>{problem}</p>}
                </li>
              );
            })}
          </ul>
          {formErrors.rules && <p className={err}>{formErrors.rules}</p>}
        </section>

        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Link href="/explorer" className="btn-ghost">Cancel</Link>
          <button type="submit" disabled={!canSubmit} className="btn-primary cursor-pointer disabled:cursor-not-allowed disabled:opacity-50">
            {saving ? <Loader className="h-5 w-5 animate-spin" /> : <Save className="h-5 w-5" />}
            {saving ? 'Saving...' : 'Save scheme'}
          </button>
        </div>
      </form>
    </div>
  );
}
