'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { getApi, getErrorMessage } from '@/services/api';
import { Send, Loader, Sparkles, Star } from 'lucide-react';

interface Scheme {
  id: string;
  title: string;
}

const BOTTLENECK_REASONS = [
  'Complex documentation',
  'Online portal broken',
  'No response from department',
  'Opaque process flow',
  'Lack of local support centers',
  'Intermediaries / Bribery requested'
];

const APPLICATION_STATUSES = [
  'Completed',
  'In Progress',
  'Approved',
  'Rejected',
  'Not Applied'
];

export default function SurveyPage() {
  const { isLoaded, userId, getToken } = useAuth();
  const router = useRouter();

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  // Form State
  const [formData, setFormData] = useState({
    scheme_id: '',
    aware_of_scheme: true,
    applied_for_scheme: false,
    difficulty_rating: 3,
    application_status: 'In Progress',
    bottleneck_reason: '',
    feedback_comments: ''
  });

  const fetchSchemes = async () => {
    try {
      setLoading(true);
      const api = getApi();
      const response = await api.get('/api/schemes/');
      setSchemes(response.data || []);
      if (response.data && response.data.length > 0) {
        setFormData((prev) => ({ ...prev, scheme_id: response.data[0].id }));
      }
    } catch (e) {
      console.error('Failed to load schemes list:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isLoaded && !userId) {
      router.push('/');
      return;
    }
    if (!userId) return;
    const t = setTimeout(fetchSchemes, 0);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoaded, userId]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleRadioChange = (name: string, value: boolean) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleDifficultyClick = (rating: number) => {
    setFormData((prev) => ({ ...prev, difficulty_rating: rating }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccess(false);

    try {
      const token = await getToken();
      const api = getApi(token);
      
      const payload: Record<string, any> = {
        scheme_id: formData.scheme_id,
        aware_of_scheme: formData.aware_of_scheme,
        feedback_comments: formData.feedback_comments
      };

      if (formData.aware_of_scheme) {
        payload.applied_for_scheme = formData.applied_for_scheme;
        if (formData.applied_for_scheme) {
          payload.difficulty_rating = formData.difficulty_rating;
          payload.application_status = formData.application_status;
          payload.bottleneck_reason = formData.bottleneck_reason || null;
        }
      }

      await api.post('/api/surveys/submit', payload);
      setSuccess(true);
      setTimeout(() => {
        router.push('/dashboard');
      }, 1500);
    } catch (err) {
      console.error('Error submitting survey:', err);
      setError(`Failed to submit survey: ${getErrorMessage(err)}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[50vh]">
        <Loader className="h-10 w-10 text-chakra animate-spin" />
        <p className="mt-4 text-xs text-ink-mute">Loading scheme registry lists...</p>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto py-6 space-y-6">
      <div className="space-y-2">
        <h1 className="font-display text-4xl font-extrabold text-ink">
          Policy Accessibility Survey
        </h1>
        <p className="text-xs text-ink-mute">
          Share your experience accessing government schemes. Your input helps us trace access roadblocks.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="glass-panel p-8 rounded-2xl space-y-6">
        {success && (
          <div className="p-3 bg-leaf/10 border border-leaf/20 text-leaf text-xs rounded-xl flex items-center space-x-2">
            <Sparkles className="h-4 w-4 animate-bounce" />
            <span>Feedback submitted successfully! Redirecting...</span>
          </div>
        )}
        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-seal text-xs rounded-xl">
            {error}
          </div>
        )}

        {/* Scheme Selection */}
        <div className="flex flex-col space-y-2">
          <label className="text-xs font-semibold text-ink-soft">Select Government Scheme</label>
          <select
            name="scheme_id"
            value={formData.scheme_id}
            onChange={handleInputChange}
            className="bg-paper border border-line rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-chakra cursor-pointer text-ink"
          >
            {schemes.map((s) => (
              <option key={s.id} value={s.id}>{s.title}</option>
            ))}
          </select>
        </div>

        {/* Aware of Scheme */}
        <div className="flex flex-col space-y-2">
          <label className="text-xs font-semibold text-ink-soft">Were you aware of this scheme before visiting PolicyGPT?</label>
          <div className="flex space-x-4 pt-1">
            <button
              type="button"
              onClick={() => handleRadioChange('aware_of_scheme', true)}
              className={`flex-1 py-2 rounded-xl border text-xs font-semibold transition-all ${
                formData.aware_of_scheme
                  ? 'bg-chakra border-chakra text-white shadow'
                  : 'border-line text-ink-mute hover:text-ink hover:bg-mist'
              }`}
            >
              Yes, I was aware
            </button>
            <button
              type="button"
              onClick={() => handleRadioChange('aware_of_scheme', false)}
              className={`flex-1 py-2 rounded-xl border text-xs font-semibold transition-all ${
                !formData.aware_of_scheme
                  ? 'bg-chakra border-chakra text-white shadow'
                  : 'border-line text-ink-mute hover:text-ink hover:bg-mist'
              }`}
            >
              No, discovered here
            </button>
          </div>
        </div>

        {formData.aware_of_scheme && (
          <>
            {/* Applied for Scheme */}
            <div className="flex flex-col space-y-2 border-t border-line pt-4">
              <label className="text-xs font-semibold text-ink-soft">Have you ever attempted to apply for this scheme?</label>
              <div className="flex space-x-4 pt-1">
                <button
                  type="button"
                  onClick={() => handleRadioChange('applied_for_scheme', true)}
                  className={`flex-1 py-2 rounded-xl border text-xs font-semibold transition-all ${
                    formData.applied_for_scheme
                      ? 'bg-chakra border-chakra text-white shadow'
                      : 'border-line text-ink-mute hover:text-ink hover:bg-mist'
                  }`}
                >
                  Yes, I have applied
                </button>
                <button
                  type="button"
                  onClick={() => handleRadioChange('applied_for_scheme', false)}
                  className={`flex-1 py-2 rounded-xl border text-xs font-semibold transition-all ${
                    !formData.applied_for_scheme
                      ? 'bg-chakra border-chakra text-white shadow'
                      : 'border-line text-ink-mute hover:text-ink hover:bg-mist'
                  }`}
                >
                  No, I did not apply
                </button>
              </div>
            </div>

            {formData.applied_for_scheme && (
              <div className="space-y-4 border-t border-line pt-4 animate-in fade-in slide-in-from-top-1 duration-200">
                {/* Difficulty Rating */}
                <div className="flex flex-col space-y-2">
                  <label className="text-xs font-semibold text-ink-soft">Application Difficulty Level</label>
                  <div className="flex space-x-2 pt-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => handleDifficultyClick(star)}
                        className="cursor-pointer p-1 transition-transform hover:scale-110"
                      >
                        <Star
                          className={`h-6 w-6 ${
                            star <= formData.difficulty_rating
                              ? 'text-amber-700 fill-amber-400'
                              : 'text-ink-mute'
                          }`}
                        />
                      </button>
                    ))}
                  </div>
                  <span className="text-xs text-ink-mute">1: Very Easy | 5: Extremely Difficult</span>
                </div>

                {/* Application Status */}
                <div className="flex flex-col space-y-2">
                  <label className="text-xs font-semibold text-ink-soft">Current Filing Status</label>
                  <select
                    name="application_status"
                    value={formData.application_status}
                    onChange={handleInputChange}
                    className="bg-paper border border-line rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-chakra cursor-pointer text-ink"
                  >
                    {APPLICATION_STATUSES.map((status) => (
                      <option key={status} value={status}>{status}</option>
                    ))}
                  </select>
                </div>

                {/* Bottleneck Reason (shows if difficulty is high or status is stuck) */}
                {formData.difficulty_rating >= 3 && (
                  <div className="flex flex-col space-y-2 animate-in fade-in duration-200">
                    <label className="text-xs font-semibold text-ink-soft">Primary Access Bottleneck / Roadblock</label>
                    <select
                      name="bottleneck_reason"
                      value={formData.bottleneck_reason}
                      onChange={handleInputChange}
                      className="bg-paper border border-line rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-chakra cursor-pointer text-ink"
                    >
                      <option value="">Select the main issue faced</option>
                      {BOTTLENECK_REASONS.map((reason) => (
                        <option key={reason} value={reason}>{reason}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Comments */}
        <div className="flex flex-col space-y-2 border-t border-line pt-4">
          <label className="text-xs font-semibold text-ink-soft">Detailed Feedback or Suggestions</label>
          <textarea
            name="feedback_comments"
            rows={4}
            value={formData.feedback_comments}
            onChange={handleInputChange}
            placeholder="Describe the application process or details of what could be simplified..."
            className="bg-paper border border-line rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-chakra transition-colors"
          />
        </div>

        {/* Submit */}
        <div className="border-t border-line pt-6 flex justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="cursor-pointer flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl bg-chakra hover:bg-chakra-dark disabled:opacity-50 text-white font-semibold text-sm shadow-md transition-colors"
          >
            {submitting ? (
              <>
                <Loader className="h-4 w-4 animate-spin" />
                <span>Submitting Feedback...</span>
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                <span>Submit Survey</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
