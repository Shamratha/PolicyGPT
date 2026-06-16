'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { getApi } from '@/services/api';
import { Bookmark, Compass, FileText, CheckSquare, Search, Award, Loader, Settings, Plus, RefreshCw } from 'lucide-react';

export default function DashboardPage() {
  const { isLoaded, userId, getToken } = useAuth();
  const router = useRouter();

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Active Application checklist management
  const [selectedApp, setSelectedApp] = useState<any>(null);
  const [updatingChecklist, setUpdatingChecklist] = useState(false);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      const api = getApi(token);
      
      // Ensure user exists in SQL DB
      await api.post('/api/auth/sync-user');

      const response = await api.get('/api/dashboard');
      setData(response.data);
    } catch (e) {
      console.error('Failed to fetch dashboard data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isLoaded && !userId) {
      router.push('/');
      return;
    }
    if (userId) {
      fetchDashboard();
    }
  }, [isLoaded, userId]);

  const handleUnsave = async (schemeId: string) => {
    try {
      const token = await getToken();
      const api = getApi(token);
      await api.post(`/api/dashboard/unsave/${schemeId}`);
      // Simple filter local state
      setData((prev: any) => ({
        ...prev,
        saved_schemes: prev.saved_schemes.filter((s: any) => s.scheme_id !== schemeId)
      }));
    } catch (e) {
      console.error('Failed to unsave scheme:', e);
    }
  };

  const handleChecklistToggle = async (docName: string, currentVal: boolean) => {
    if (!selectedApp) return;
    try {
      setUpdatingChecklist(true);
      const token = await getToken();
      const api = getApi(token);

      const updatedChecklist = {
        ...selectedApp.document_checklist,
        [docName]: !currentVal
      };

      const res = await api.post(`/api/dashboard/applications/${selectedApp.id}/update`, {
        checklist: updatedChecklist,
        status: selectedApp.status
      });

      // Update local state for modal
      setSelectedApp(res.data);
      
      // Refresh general dashboard list
      const response = await api.get('/api/dashboard');
      setData(response.data);
    } catch (e) {
      console.error('Failed to update checklist:', e);
    } finally {
      setUpdatingChecklist(false);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    if (!selectedApp) return;
    try {
      setUpdatingChecklist(true);
      const token = await getToken();
      const api = getApi(token);

      const res = await api.post(`/api/dashboard/applications/${selectedApp.id}/update`, {
        checklist: selectedApp.document_checklist,
        status: newStatus
      });

      setSelectedApp(res.data);
      const response = await api.get('/api/dashboard');
      setData(response.data);
    } catch (e) {
      console.error('Failed to update status:', e);
    } finally {
      setUpdatingChecklist(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[50vh]">
        <Loader className="h-10 w-10 text-indigo-400 animate-spin" />
        <p className="mt-4 text-xs text-slate-400">Loading your personalized workspace...</p>
      </div>
    );
  }

  return (
    <div className="space-y-10 py-4">
      {/* Welcome header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-sky-400 bg-clip-text text-transparent">
            Personal Dashboard
          </h1>
          <p className="text-xs text-slate-400">
            Monitor saved programs, manage document checklists, and review automatic eligibility audits.
          </p>
        </div>

        <button
          onClick={() => router.push('/profile')}
          className="cursor-pointer flex items-center space-x-1 px-4 py-2 rounded-xl border border-white/10 hover:bg-white/5 text-xs text-slate-300 transition-colors"
        >
          <Settings className="h-4 w-4" />
          <span>Profile Settings</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Columns (Saved & Searches) */}
        <div className="lg:col-span-2 space-y-8">
          {/* Active Applications */}
          <div className="glass-panel p-6 rounded-2xl space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
              <CheckSquare className="h-4 w-4 text-indigo-400" />
              <span>Applications Progress Tracker</span>
            </h2>

            {data?.applications && data.applications.length > 0 ? (
              <div className="space-y-4">
                {data.applications.map((app: any) => (
                  <div
                    key={app.id}
                    onClick={() => setSelectedApp(app)}
                    className="p-4 rounded-xl border border-white/5 bg-slate-900/30 hover:border-indigo-500/20 transition-all cursor-pointer space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-bold text-white">{app.scheme_title}</h3>
                      <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400">
                        {app.status}
                      </span>
                    </div>

                    {/* Progress bar */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-[10px] text-slate-500">
                        <span>Documents Upload Checklist</span>
                        <span className="font-semibold text-slate-300">{app.progress}% Complete</span>
                      </div>
                      <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                          style={{ width: `${app.progress}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-10 border border-dashed border-white/5 rounded-xl text-slate-500 text-xs space-y-2">
                <p>No active filings started yet.</p>
                <button
                  onClick={() => router.push('/explorer')}
                  className="cursor-pointer text-[10px] text-indigo-400 font-bold hover:underline"
                >
                  Browse schemes to start applying
                </button>
              </div>
            )}
          </div>

          {/* Automatic Eligibility Matches */}
          <div className="glass-panel p-6 rounded-2xl space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
              <Award className="h-4 w-4 text-emerald-400" />
              <span>Direct Eligibility Audits</span>
            </h2>

            {data?.eligibility_matches && data.eligibility_matches.length > 0 ? (
              <div className="space-y-4">
                {data.eligibility_matches.map((match: any) => (
                  <div
                    key={match.scheme_id}
                    className="p-4 rounded-xl border border-white/5 bg-slate-900/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-xs font-bold text-white">{match.title}</h3>
                        <span
                          className={`px-2 py-0.5 rounded text-[9px] font-extrabold ${
                            match.status === 'Eligible'
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : 'bg-amber-500/10 text-amber-400'
                          }`}
                        >
                          {match.status}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400 max-w-lg">{match.reason}</p>
                    </div>

                    <button
                      onClick={() => router.push(`/explorer?id=${match.scheme_id}`)}
                      className="cursor-pointer text-[10px] font-bold text-indigo-400 hover:text-indigo-300 border border-white/10 hover:bg-white/5 px-3 py-1.5 rounded-lg whitespace-nowrap"
                    >
                      Audit / File Application
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 text-center py-6">
                No verified matches. Edit your profile attributes to calculate matches.
              </p>
            )}
          </div>
        </div>

        {/* Right Column (Saved list & searches) */}
        <div className="space-y-8">
          {/* Saved Schemes */}
          <div className="glass-panel p-6 rounded-2xl space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
              <Bookmark className="h-4 w-4 text-indigo-400" />
              <span>Saved Programs</span>
            </h2>

            {data?.saved_schemes && data.saved_schemes.length > 0 ? (
              <div className="space-y-3">
                {data.saved_schemes.map((s: any) => (
                  <div
                    key={s.id}
                    className="p-3 rounded-xl border border-white/5 bg-slate-900/40 flex items-center justify-between gap-2 text-xs"
                  >
                    <div className="truncate">
                      <h4 className="font-bold text-white truncate">{s.title}</h4>
                      <span className="text-[9px] text-slate-500">{s.state} | {s.category}</span>
                    </div>
                    <div className="flex space-x-2 ml-auto">
                      <button
                        onClick={() => router.push(`/explorer?id=${s.scheme_id}`)}
                        className="cursor-pointer text-[9px] font-bold text-indigo-400 hover:underline"
                      >
                        Open
                      </button>
                      <button
                        onClick={() => handleUnsave(s.scheme_id)}
                        className="cursor-pointer text-[9px] font-bold text-rose-500 hover:underline"
                      >
                        Unsave
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 text-center py-6">No saved opportunities yet.</p>
            )}
          </div>

          {/* Recent Searches */}
          <div className="glass-panel p-6 rounded-2xl space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
              <Search className="h-4 w-4 text-indigo-400" />
              <span>Search Inquiries</span>
            </h2>
            {data?.recent_searches && data.recent_searches.length > 0 ? (
              <div className="space-y-2">
                {data.recent_searches.map((h: any) => (
                  <div
                    key={h.id}
                    className="p-2.5 rounded-lg bg-slate-950/20 text-slate-400 text-xs truncate hover:text-white transition-colors cursor-pointer"
                    onClick={() => router.push(`/chat`)}
                  >
                    {h.query}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 text-center py-6">No searches performed.</p>
            )}
          </div>
        </div>
      </div>

      {/* Dynamic Application Checklist Modal */}
      {selectedApp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-md rounded-2xl p-6 space-y-5 animate-in fade-in-50 zoom-in-95 duration-200">
            <div className="flex justify-between items-center border-b border-white/5 pb-3">
              <h2 className="text-base font-bold text-white truncate pr-6">{selectedApp.scheme_title}</h2>
              <button
                onClick={() => setSelectedApp(null)}
                className="cursor-pointer text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            {/* Checklist items */}
            <div className="space-y-4">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-400">Required Document Checklist:</span>
                <span className="text-slate-500">{selectedApp.progress}% Done</span>
              </div>

              {Object.keys(selectedApp.document_checklist).length > 0 ? (
                <div className="space-y-2 text-xs">
                  {Object.entries(selectedApp.document_checklist).map(([doc, checked]: [string, any]) => (
                    <label
                      key={doc}
                      className="flex items-center space-x-3 p-3 rounded-xl border border-white/5 bg-slate-900/30 hover:bg-slate-900/60 cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => handleChecklistToggle(doc, checked)}
                        disabled={updatingChecklist}
                        className="h-4.5 w-4.5 accent-indigo-500 rounded border-white/10"
                      />
                      <span className={checked ? 'line-through text-slate-500' : 'text-slate-200'}>
                        {doc}
                      </span>
                    </label>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">No document requirements defined. General filing rules apply.</p>
              )}
            </div>

            {/* Application status updater */}
            <div className="border-t border-white/5 pt-4 flex items-center justify-between text-xs">
              <span className="font-bold text-slate-400">Application Status:</span>
              <select
                value={selectedApp.status}
                onChange={(e) => handleStatusChange(e.target.value)}
                disabled={updatingChecklist}
                className="bg-slate-950 border border-white/10 text-xs font-semibold rounded-lg px-2 py-1 text-slate-300 cursor-pointer"
              >
                <option value="Draft">Draft</option>
                <option value="Submitted">Submitted</option>
                <option value="Approved">Approved</option>
                <option value="Rejected">Rejected</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
