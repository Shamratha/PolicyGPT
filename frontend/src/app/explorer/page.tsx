'use client';

import { useState, useEffect, Suspense } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { getApi, getErrorMessage } from '@/services/api';
import { Search, Compass, FileText, CheckCircle2, Bookmark, BookmarkCheck, Upload, Loader, UserCheck, Plus } from 'lucide-react';

interface Scheme {
  id: string;
  name: string;
  title: string;
  description: string;
  benefits: string;
  eligibility_criteria: string;
  required_documents: string;
  application_steps: string;
  state: string;
  category: string;
  ministry: string;
}

function ExplorerContent() {
  const { userId, getToken } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();

  // Search & Filter State
  const [search, setSearch] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  
  const [filterWomen, setFilterWomen] = useState(false);
  const [filterStudents, setFilterStudents] = useState(false);
  const [filterStartups, setFilterStartups] = useState(false);
  const [filterFarmers, setFilterFarmers] = useState(false);

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(true);

  // Dialog / Details States
  const [activeScheme, setActiveScheme] = useState<Scheme | null>(null);
  const [eligibilityResult, setEligibilityResult] = useState<any>(null);
  const [checkingEligibility, setCheckingEligibility] = useState(false);
  
  // Saved state list
  const [savedSchemeIds, setSavedSchemeIds] = useState<string[]>([]);

  // Admin Ingestion State
  const [adminFile, setAdminFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState('');

  // Admin: delete scheme
  const [isAdmin, setIsAdmin] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  useEffect(() => {
    if (!userId) return;
    let active = true;
    const loadRole = async () => {
      try {
        const token = await getToken();
        const res = await getApi(token).get('/api/auth/me');
        if (active) setIsAdmin(Boolean(res.data?.is_admin));
      } catch {
        if (active) setIsAdmin(false);
      }
    };
    loadRole();
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const handleDeleteScheme = async () => {
    if (!activeScheme) return;
    setDeleting(true);
    setDeleteError('');
    try {
      const token = await getToken();
      await getApi(token).delete(`/api/schemes/${activeScheme.id}`);
      setSchemes((prev) => prev.filter((s) => s.id !== activeScheme.id));
      setActiveScheme(null);
      setConfirmDelete(false);
    } catch (err) {
      setDeleteError(getErrorMessage(err, 'Could not delete the scheme.'));
    } finally {
      setDeleting(false);
    }
  };

  const fetchSchemes = async () => {
    try {
      setLoading(true);
      const api = getApi();
      
      const params: Record<string, any> = {};
      if (selectedState) params.state = selectedState;
      if (selectedCategory) params.category = selectedCategory;
      if (filterWomen) params.women = true;
      if (filterStudents) params.students = true;
      if (filterStartups) params.startups = true;
      if (filterFarmers) params.farmers = true;

      const response = await api.get('/api/schemes/', { params });
      setSchemes(response.data || []);
    } catch (e) {
      console.error('Failed to load schemes:', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchSavedList = async () => {
    try {
      const token = await getToken();
      const api = getApi(token);
      
      // Ensure user record is synced with local SQL database
      await api.post('/api/auth/sync-user');
      
      const res = await api.get('/api/dashboard');
      if (res.data && res.data.saved_schemes) {
        setSavedSchemeIds(res.data.saved_schemes.map((s: any) => s.scheme_id));
      }
    } catch (e) {
      console.error('Error loading saved bookmarks:', e);
    }
  };

  const handleOpenDetails = (scheme: Scheme) => {
    setConfirmDelete(false);
    setDeleteError('');
    setActiveScheme(scheme);
    setEligibilityResult(null);
  };

  useEffect(() => {
    const t = setTimeout(() => {
      fetchSchemes();
      if (userId) fetchSavedList();
    }, 0);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, selectedState, selectedCategory, filterWomen, filterStudents, filterStartups, filterFarmers]);

  // Handle auto-focus from URL queries
  useEffect(() => {
    const focusId = searchParams.get('id');
    if (focusId && schemes.length > 0) {
      const match = schemes.find((s) => s.id === focusId);
      if (match) {
        const t = setTimeout(() => handleOpenDetails(match), 0);
        return () => clearTimeout(t);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, schemes]);

  const toggleSaveScheme = async (schemeId: string) => {
    if (!userId) {
      alert('Please Sign In to save matching opportunities.');
      return;
    }
    const isSaved = savedSchemeIds.includes(schemeId);
    try {
      const token = await getToken();
      const api = getApi(token);
      if (isSaved) {
        await api.post(`/api/dashboard/unsave/${schemeId}`);
        setSavedSchemeIds((prev) => prev.filter((id) => id !== schemeId));
      } else {
        await api.post(`/api/dashboard/save/${schemeId}`);
        setSavedSchemeIds((prev) => [...prev, schemeId]);
      }
    } catch (e) {
      console.error('Failed to save bookmark:', e);
    }
  };

  const checkEligibility = async (schemeId: string) => {
    if (!userId) {
      alert('Please Sign In to audit your profile eligibility.');
      return;
    }
    try {
      setCheckingEligibility(true);
      const token = await getToken();
      const api = getApi(token);
      const res = await api.get(`/api/schemes/${schemeId}/eligibility`);
      setEligibilityResult(res.data);
    } catch (e) {
      console.error('Failed to check eligibility:', e);
      setEligibilityResult({
        status: 'Unavailable',
        reason: `Could not run the eligibility check: ${getErrorMessage(e)}`,
        required_documents: [],
        application_steps: []
      });
    } finally {
      setCheckingEligibility(false);
    }
  };

  const handleUploadGuidelines = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeScheme || !adminFile) return;

    try {
      setUploading(true);
      setUploadMsg('');
      const token = await getToken();
      
      const formData = new FormData();
      formData.append('scheme_id', activeScheme.id);
      formData.append('file', adminFile);

      const response = await getApi(token).post('/api/schemes/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadMsg(response.data.message || 'Indexed guidelines successfully.');
      setAdminFile(null);
    } catch (err: any) {
      console.error('Failed to index PDF:', err);
      setUploadMsg(`Error: ${getErrorMessage(err, 'Ingestion pipeline failed.')}`);
    } finally {
      setUploading(false);
    }
  };

  const filteredSchemes = schemes.filter(
    (s) =>
      s.title.toLowerCase().includes(search.toLowerCase()) ||
      s.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8 py-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-2">
          <h1 className="font-display text-4xl font-extrabold text-ink">
            Government Opportunities Explorer
          </h1>
          <p className="text-ink-mute">
            Search, filter, and check your eligibility for state and central schemes.
          </p>
        </div>
        <Link href="/explorer/new" className="btn-primary shrink-0">
          <Plus className="h-5 w-5" /> Add a scheme
        </Link>
      </div>

      {/* Filter panel */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search box */}
          <div className="relative">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-ink-mute" />
            <input
              type="text"
              placeholder="Search scheme name or details..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-paper border border-line rounded-xl pl-10 pr-4 py-2.5 text-xs focus:outline-none focus:border-chakra transition-colors"
            />
          </div>

          {/* State selector */}
          <select
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            className="bg-paper border border-line rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-chakra transition-colors cursor-pointer text-ink-soft"
          >
            <option value="">All States / Regional Filters</option>
            <option value="Central">Central Govt (All India)</option>
            {['Andhra Pradesh', 'Bihar', 'Delhi', 'Gujarat', 'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Odisha', 'Rajasthan', 'Tamil Nadu', 'Telangana', 'Uttar Pradesh', 'West Bengal'].map((st) => (
              <option key={st} value={st}>{st}</option>
            ))}
          </select>

          {/* Category selector */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-paper border border-line rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-chakra transition-colors cursor-pointer text-ink-soft"
          >
            <option value="">All Category Verticals</option>
            <option value="Business">Entrepreneurship & Startups</option>
            <option value="Education">Scholarships & Students</option>
            <option value="Agriculture">Agriculture & Farmers</option>
            <option value="Healthcare">Healthcare</option>
            <option value="Housing">Housing</option>
            <option value="Employment">Employment & Skills</option>
            <option value="Social Welfare">Social Welfare</option>
            <option value="Women & Child">Women & Child</option>
            <option value="General">General</option>
          </select>
        </div>

        {/* Toggles filters */}
        <div className="flex flex-wrap gap-4 pt-2 border-t border-line">
          <label className="flex items-center space-x-2 text-xs text-ink-soft cursor-pointer">
            <input
              type="checkbox"
              checked={filterWomen}
              onChange={(e) => setFilterWomen(e.target.checked)}
              className="accent-indigo-500 h-4.5 w-4.5 rounded border-line"
            />
            <span>Women Beneficiaries</span>
          </label>
          <label className="flex items-center space-x-2 text-xs text-ink-soft cursor-pointer">
            <input
              type="checkbox"
              checked={filterStudents}
              onChange={(e) => setFilterStudents(e.target.checked)}
              className="accent-indigo-500 h-4.5 w-4.5 rounded border-line"
            />
            <span>Students / Youth</span>
          </label>
          <label className="flex items-center space-x-2 text-xs text-ink-soft cursor-pointer">
            <input
              type="checkbox"
              checked={filterStartups}
              onChange={(e) => setFilterStartups(e.target.checked)}
              className="accent-indigo-500 h-4.5 w-4.5 rounded border-line"
            />
            <span>Startup Grants</span>
          </label>
          <label className="flex items-center space-x-2 text-xs text-ink-soft cursor-pointer">
            <input
              type="checkbox"
              checked={filterFarmers}
              onChange={(e) => setFilterFarmers(e.target.checked)}
              className="accent-indigo-500 h-4.5 w-4.5 rounded border-line"
            />
            <span>Farmers & Agriculture</span>
          </label>
        </div>
      </div>

      {/* Explorer Results Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader className="h-8 w-8 text-chakra animate-spin" />
          <p className="mt-4 text-xs text-ink-mute">Querying policy registry database...</p>
        </div>
      ) : filteredSchemes.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredSchemes.map((s) => (
            <div key={s.id} className="glass-panel p-6 rounded-2xl flex flex-col justify-between space-y-4 relative">
              <button
                onClick={() => toggleSaveScheme(s.id)}
                className="absolute right-4 top-4 text-ink-mute hover:text-chakra-dark transition-colors p-1"
              >
                {savedSchemeIds.includes(s.id) ? (
                  <BookmarkCheck className="h-5 w-5 text-chakra" />
                ) : (
                  <Bookmark className="h-5 w-5" />
                )}
              </button>

              <div className="space-y-2">
                <span className="inline-block px-2 py-0.5 rounded text-xs font-bold bg-chakra/10 text-chakra border border-chakra/15">
                  {s.state} | {s.category}
                </span>
                <h3 className="text-lg font-bold text-ink pr-6">{s.title}</h3>
                <span className="text-xs text-ink-mute block">{s.ministry}</span>
                <p className="text-xs text-ink-mute line-clamp-3 leading-relaxed pt-2">{s.description}</p>
              </div>

              <div className="flex items-center space-x-3 pt-4 border-t border-line">
                <button
                  onClick={() => handleOpenDetails(s)}
                  className="cursor-pointer flex-1 py-2 rounded-xl text-center text-xs font-semibold border border-line hover:bg-mist text-ink transition-colors"
                >
                  View Scheme Guidelines
                </button>
                <button
                  onClick={() => {
                    handleOpenDetails(s);
                    checkEligibility(s.id);
                  }}
                  className="cursor-pointer flex-1 py-2 rounded-xl text-center text-xs font-semibold bg-chakra hover:bg-chakra-dark text-white shadow transition-colors"
                >
                  Verify Eligibility
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 glass-panel rounded-2xl">
          <Compass className="h-10 w-10 text-ink-mute mx-auto" />
          <h3 className="mt-4 text-sm font-bold text-ink">No Schemes Found</h3>
          <p className="text-xs text-ink-mute mt-2">Adjust your filters to see central or regional opportunities.</p>
        </div>
      )}

      {/* Expanded Scheme Drawer / Dialog Overlay */}
      {activeScheme && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/40 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-3xl max-h-[85vh] rounded-3xl overflow-hidden flex flex-col animate-in fade-in-50 zoom-in-95 duration-200">
            {/* Header */}
            <div className="p-6 border-b border-line bg-paper flex justify-between items-center">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-chakra bg-chakra/10 px-2 py-0.5 rounded">
                  {activeScheme.state} | {activeScheme.category}
                </span>
                <h2 className="text-lg sm:text-xl font-bold text-ink mt-1">{activeScheme.title}</h2>
              </div>
              <button
                onClick={() => {
                  setActiveScheme(null);
                  setEligibilityResult(null);
                  router.push('/explorer'); // clear query param
                }}
                className="cursor-pointer text-ink-mute hover:text-ink text-lg font-bold"
              >
                ✕
              </button>
            </div>

            {/* Scrollable Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Detailed Columns */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2 space-y-4">
                  <div>
                    <h4 className="text-xs uppercase font-bold text-ink-mute tracking-wider">Description</h4>
                    <p className="text-xs text-ink-soft leading-relaxed pt-1.5">{activeScheme.description}</p>
                  </div>
                  <div>
                    <h4 className="text-xs uppercase font-bold text-ink-mute tracking-wider">Benefits & Financial Subsidy</h4>
                    <p className="text-xs text-ink-soft leading-relaxed pt-1.5">{activeScheme.benefits}</p>
                  </div>
                  <div>
                    <h4 className="text-xs uppercase font-bold text-ink-mute tracking-wider">Eligibility Requirements</h4>
                    <p className="text-xs text-ink-soft leading-relaxed pt-1.5">{activeScheme.eligibility_criteria}</p>
                  </div>
                </div>

                {/* Right side panels: docs, workflow */}
                <div className="space-y-4 bg-paper p-4 rounded-2xl border border-line h-fit text-xs">
                  <div>
                    <span className="font-semibold text-ink-mute flex items-center space-x-1.5">
                      <FileText className="h-3.5 w-3.5 text-chakra" />
                      <span>Documents Needed</span>
                    </span>
                    <p className="text-ink-soft mt-1.5 leading-relaxed">{activeScheme.required_documents}</p>
                  </div>
                  <div>
                    <span className="font-semibold text-ink-mute flex items-center space-x-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-leaf" />
                      <span>Filing Steps</span>
                    </span>
                    <p className="text-ink-soft mt-1.5 leading-relaxed">{activeScheme.application_steps}</p>
                  </div>
                </div>
              </div>

              {/* Admin-only tools: delete scheme + guideline PDF uploader */}
              {isAdmin && (
              <div className="space-y-4 border-t border-line pt-4">
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border-2 border-seal/30 bg-seal-tint/60 p-3">
                  <p className="text-sm font-bold text-seal">
                    {confirmDelete ? 'Delete this scheme permanently? Saved bookmarks and applications for it are removed too.' : 'Admin: remove this scheme'}
                  </p>
                  <div className="flex gap-2">
                    {confirmDelete && (
                      <button type="button" onClick={() => setConfirmDelete(false)} className="cursor-pointer rounded-lg border-2 border-line bg-paper px-3 py-1.5 text-sm font-bold text-ink">
                        Cancel
                      </button>
                    )}
                    <button
                      type="button"
                      disabled={deleting}
                      onClick={() => (confirmDelete ? handleDeleteScheme() : setConfirmDelete(true))}
                      className="cursor-pointer rounded-lg bg-seal px-3 py-1.5 text-sm font-bold text-white disabled:opacity-50"
                    >
                      {deleting ? 'Deleting...' : confirmDelete ? 'Yes, delete' : 'Delete scheme'}
                    </button>
                  </div>
                  {deleteError && <p className="w-full text-sm font-bold text-seal">{deleteError}</p>}
                </div>
              <details className="group">
                <summary className="cursor-pointer text-xs font-bold text-ink-mute hover:text-chakra-dark flex items-center space-x-1">
                  <span>Admin: upload the official guidelines PDF</span>
                </summary>
                <form onSubmit={handleUploadGuidelines} className="mt-4 p-4 bg-paper border border-line rounded-2xl space-y-4 text-xs">
                  <p className="text-xs text-ink-mute">
                    Upload official government PDF instructions to vectorize and save in ChromaDB, updating RAG answers.
                  </p>
                  {uploadMsg && <div className="p-2 bg-chakra/10 border border-chakra/10 text-chakra rounded-lg">{uploadMsg}</div>}
                  <div className="flex flex-col sm:flex-row items-center gap-3">
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={(e) => setAdminFile(e.target.files?.[0] || null)}
                      className="text-xs text-ink-mute file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-mist file:text-ink file:hover:bg-mist cursor-pointer"
                    />
                    <button
                      type="submit"
                      disabled={uploading || !adminFile}
                      className="cursor-pointer w-full sm:w-auto px-4 py-1.5 rounded-lg bg-chakra hover:bg-chakra-dark disabled:opacity-50 text-white font-semibold flex items-center justify-center space-x-1.5"
                    >
                      {uploading ? (
                        <>
                          <Loader className="h-3 w-3 animate-spin" />
                          <span>Index Document...</span>
                        </>
                      ) : (
                        <>
                          <Upload className="h-3 w-3" />
                          <span>Upload PDF</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </details>
              </div>
              )}

              {/* Eligibility evaluation result display */}
              <div className="border-t border-line pt-4 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-ink flex items-center space-x-2">
                    <UserCheck className="h-4 w-4 text-chakra" />
                    <span>User Profile Eligibility Check</span>
                  </h3>
                  {!eligibilityResult && (
                    <button
                      onClick={() => checkEligibility(activeScheme.id)}
                      disabled={checkingEligibility}
                      className="cursor-pointer text-xs font-semibold px-4 py-1.5 rounded-xl bg-chakra hover:bg-chakra-dark disabled:opacity-50 text-white flex items-center space-x-1"
                    >
                      {checkingEligibility && <Loader className="h-3 w-3 animate-spin" />}
                      <span>Run Audit Engine</span>
                    </button>
                  )}
                </div>

                {eligibilityResult && (
                  <div className="p-4 bg-paper border border-line rounded-2xl space-y-4">
                    <div className="flex items-center space-x-3">
                      <span className="text-xs font-bold text-ink-mute">Match Status:</span>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-extrabold ${
                          eligibilityResult.status === 'Eligible'
                            ? 'bg-leaf/15 text-leaf'
                            : eligibilityResult.status === 'Potentially Eligible'
                            ? 'bg-amber-500/15 text-amber-700'
                            : 'bg-rose-500/15 text-seal'
                        }`}
                      >
                        {eligibilityResult.status}
                      </span>
                    </div>

                    <div className="space-y-3 text-xs leading-relaxed text-ink-soft">
                      <div>
                        <span className="font-bold text-ink block">Audit Rationale:</span>
                        <p className="mt-1 text-ink-mute">{eligibilityResult.reason}</p>
                      </div>

                      {eligibilityResult.required_documents.length > 0 && (
                        <div>
                          <span className="font-bold text-ink block">Dynamic Document Checklists:</span>
                          <ul className="list-disc pl-4 mt-1 space-y-1 text-ink-mute">
                            {eligibilityResult.required_documents.map((d: string, dIdx: number) => (
                              <li key={dIdx}>{d}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {eligibilityResult.application_steps.length > 0 && (
                        <div>
                          <span className="font-bold text-ink block">Next Application Steps:</span>
                          <ol className="list-decimal pl-4 mt-1 space-y-1 text-ink-mute">
                            {eligibilityResult.application_steps.map((s: string, sIdx: number) => (
                              <li key={sIdx}>{s}</li>
                            ))}
                          </ol>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Bottom Actions */}
            <div className="p-6 border-t border-line bg-paper flex justify-end space-x-3">
              <button
                onClick={async () => {
                  try {
                    const token = await getToken();
                    const api = getApi(token);
                    await api.post(`/api/dashboard/applications/${activeScheme.id}/start`);
                    setActiveScheme(null);
                    router.push('/dashboard');
                  } catch (err) {
                    console.error(err);
                  }
                }}
                className="cursor-pointer text-xs font-semibold px-6 py-2 rounded-xl bg-chakra hover:bg-chakra-dark text-white shadow"
              >
                File Online Application
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ExplorerPage() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-[50vh]">
        <Loader className="h-10 w-10 text-chakra animate-spin" />
        <p className="mt-4 text-xs text-ink-mute">Loading policy explorer...</p>
      </div>
    }>
      <ExplorerContent />
    </Suspense>
  );
}
