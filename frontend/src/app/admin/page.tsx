'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { getApi, getDownloadApi } from '@/services/api';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, Legend } from 'recharts';
import { FileText, Loader, Users, Compass, Search, Award, ShieldAlert, BarChart2, Globe, Sparkles, CheckCircle2, AlertTriangle } from 'lucide-react';

const CHART_COLORS = ['#6366f1', '#0ea5e9', '#8b5cf6', '#10b981', '#f59e0b', '#f43f5e'];

export default function AdminPage() {
  const { isLoaded, userId, getToken } = useAuth();
  const router = useRouter();

  const [summary, setSummary] = useState<any>(null);
  const [surveyStats, setSurveyStats] = useState<any>(null);
  
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  // Scraper pipeline states
  const [scrapeUrl, setScrapeUrl] = useState('');
  const [scraping, setScraping] = useState(false);
  const [scrapeStep, setScrapeStep] = useState(0); // 1: web scrape, 2: gpt parsing, 3: database ingest
  const [scrapeResult, setScrapeResult] = useState<any>(null);
  const [scrapeError, setScrapeError] = useState<string | null>(null);

  const handleScrape = async () => {
    if (!scrapeUrl.trim()) return;
    setScraping(true);
    setScrapeStep(1);
    setScrapeResult(null);
    setScrapeError(null);

    // Simulate progress steps while API performs parsing
    const timer1 = setTimeout(() => setScrapeStep(2), 2000);
    const timer2 = setTimeout(() => setScrapeStep(3), 5000);

    try {
      const token = await getToken();
      const api = getApi(token);
      
      const response = await api.post('/api/schemes/scrape', {
        url: scrapeUrl.trim()
      });

      clearTimeout(timer1);
      clearTimeout(timer2);
      
      setScrapeStep(3);
      setScrapeResult(response.data);
      
      // Refresh statistics (total schemes count card will increment)
      fetchAdminStats();
    } catch (e: any) {
      clearTimeout(timer1);
      clearTimeout(timer2);
      const detail = e.response?.data?.detail || e.message || 'An unknown network error occurred.';
      setScrapeError(detail);
    } finally {
      setScraping(false);
      setScrapeStep(0);
    }
  };

  const fetchAdminStats = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      const api = getApi(token);
      
      // Ensure user synced
      await api.post('/api/auth/sync-user');

      const [summaryRes, surveyRes] = await Promise.all([
        api.get('/api/analytics/summary'),
        api.get('/api/surveys/stats')
      ]);

      setSummary(summaryRes.data);
      setSurveyStats(surveyRes.data);
    } catch (e) {
      console.error('Failed to load admin stats:', e);
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
      fetchAdminStats();
    }
  }, [isLoaded, userId]);

  const handleDownloadReport = async () => {
    try {
      setDownloading(true);
      const token = await getToken();
      const api = getDownloadApi(token);
      
      const response = await api.get('/api/surveys/report');
      
      // Create a URL and click a dynamic link to download PDF in browser
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = 'Policy_Access_Report.pdf';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (e) {
      console.error('Failed to download PDF report:', e);
      alert('Failed to compile PDF report.');
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[50vh]">
        <Loader className="h-10 w-10 text-indigo-400 animate-spin" />
        <p className="mt-4 text-xs text-slate-400">Compiling database logs and survey summaries...</p>
      </div>
    );
  }

  // Formatting chart data structures
  const popularityData = summary?.most_requested_schemes?.map((s: any) => ({
    name: s.scheme_title.length > 20 ? s.scheme_title.substring(0, 20) + '...' : s.scheme_title,
    Requests: s.count
  })) || [];

  const bottleneckData = surveyStats?.bottlenecks 
    ? Object.entries(surveyStats.bottlenecks).map(([reason, count]) => ({ name: reason, value: count }))
    : [];

  const stateAwarenessData = surveyStats?.state_awareness?.map((s: any) => ({
    name: s.state,
    Awareness: s.awareness_rate
  })) || [];

  const demographicsData = surveyStats?.underserved_demographics?.map((d: any) => ({
    name: d.demographic,
    'Success Rate': d.match_rate
  })) || [];

  return (
    <div className="space-y-10 py-4">
      {/* Title & Download report button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-sky-400 bg-clip-text text-transparent">
            SaaS Platform Impact Analytics
          </h1>
          <p className="text-xs text-slate-400">
            Review live KPIs, monitor application bottlenecks, and compile Policy Access Reports.
          </p>
        </div>

        <button
          onClick={handleDownloadReport}
          disabled={downloading}
          className="cursor-pointer flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs sm:text-sm shadow-md transition-colors"
        >
          {downloading ? (
            <>
              <Loader className="h-4 w-4 animate-spin" />
              <span>Compiling PDF Report...</span>
            </>
          ) : (
            <>
              <FileText className="h-4 w-4" />
              <span>Download PDF Report</span>
            </>
          )}
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-panel p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 bg-indigo-500/10 rounded-xl text-indigo-400">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{summary?.users_served || 0}</div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Users Served</p>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 bg-sky-500/10 rounded-xl text-sky-400">
            <Compass className="h-6 w-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{summary?.schemes_indexed || 0}</div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Schemes Indexed</p>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400">
            <Search className="h-6 w-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{summary?.searches_performed || 0}</div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Searches Logged</p>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
            <Award className="h-6 w-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{summary?.eligibility_success_rate || 0}%</div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Eligibility Success</p>
          </div>
        </div>
      </div>

      {/* AI Policy Ingestion Pipeline Card */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-white/5 pb-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Globe className="h-5 w-5 text-indigo-400" />
              <h2 className="text-lg font-bold text-white">AI Policy Ingestion Pipeline</h2>
            </div>
            <p className="text-xs text-slate-400">
              Scrape government portal webpages to automatically ingest schemes, extract parameters, synthesize logical eligibility rules, and index text inside ChromaDB.
            </p>
          </div>
          <div>
            <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[10px] font-semibold text-indigo-300">
              <Sparkles className="h-3 w-3 animate-pulse text-indigo-400" />
              <span>GPT-4o Auto-Ingest</span>
            </span>
          </div>
        </div>

        {/* Preset Links */}
        <div className="space-y-2">
          <label className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
            Quick Ingestion Presets
          </label>
          <div className="flex flex-wrap gap-2">
            {[
              {
                label: 'Rajiv Gandhi Entrepreneurship (Karnataka)',
                url: 'https://eitbt.karnataka.gov.in/startup/public/107/rajiv-gandhi-entrepreneurship-program/en'
              },
              {
                label: 'Jan Dhan Yojana (myScheme)',
                url: 'https://www.myscheme.gov.in/schemes/pmjdy'
              },
              {
                label: 'Government Schemes Search (India.gov)',
                url: 'https://www.india.gov.in/my-government/schemes/search'
              }
            ].map((preset, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setScrapeUrl(preset.url);
                  setScrapeError(null);
                  setScrapeResult(null);
                }}
                className="cursor-pointer px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 text-xs transition-colors border border-white/5 hover:border-indigo-500/30 font-medium"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Form */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="url"
              placeholder="Enter official scheme detail page URL (e.g. https://www.myscheme.gov.in/...)"
              value={scrapeUrl}
              onChange={(e) => {
                setScrapeUrl(e.target.value);
                setScrapeError(null);
              }}
              disabled={scraping}
              className="flex-1 bg-slate-900/80 border border-white/10 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/50 transition-colors"
            />
            <button
              onClick={handleScrape}
              disabled={scraping || !scrapeUrl.trim()}
              className="cursor-pointer bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-sm px-6 py-3 rounded-xl shadow-md transition-colors flex items-center justify-center space-x-2 min-w-[160px]"
            >
              {scraping ? (
                <>
                  <Loader className="h-4 w-4 animate-spin" />
                  <span>Ingesting...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Start Ingestion</span>
                </>
              )}
            </button>
          </div>

          {/* Scraping Steps / Status Indicator */}
          {scraping && (
            <div className="bg-slate-900/50 border border-white/5 rounded-xl p-4 space-y-3 animate-pulse">
              <div className="flex items-center space-x-2 text-xs text-indigo-400 font-semibold">
                <Loader className="h-3 w-3 animate-spin" />
                <span>Running Pipeline: {
                  scrapeStep === 1 ? 'Downloading website HTML...' :
                  scrapeStep === 2 ? 'AI parsing & logical rule extraction...' :
                  'Vector DB indexing & SQL commit...'
                }</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div 
                  className="bg-indigo-500 h-1.5 transition-all duration-500 rounded-full" 
                  style={{ width: `${(scrapeStep / 3) * 100}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 flex justify-between">
                <span className={scrapeStep >= 1 ? "text-indigo-300 font-medium" : ""}>1. Web Scrape</span>
                <span className={scrapeStep >= 2 ? "text-indigo-300 font-medium" : ""}>2. GPT Parameterize</span>
                <span className={scrapeStep >= 3 ? "text-indigo-300 font-medium" : ""}>3. Database Ingestion</span>
              </div>
            </div>
          )}

          {/* Success Result Display */}
          {scrapeResult && (
            <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-5 space-y-4">
              <div className="flex items-center space-x-2 text-emerald-400">
                <CheckCircle2 className="h-5 w-5" />
                <span className="text-sm font-bold">Scheme Ingested Successfully!</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="space-y-1">
                  <span className="text-slate-500 block uppercase text-[10px] tracking-wider font-semibold">Official Title</span>
                  <span className="text-white font-medium">{scrapeResult.title}</span>
                </div>
                <div className="space-y-1">
                  <span className="text-slate-500 block uppercase text-[10px] tracking-wider font-semibold">Unique Name Slug</span>
                  <code className="text-indigo-300 bg-indigo-500/10 px-1.5 py-0.5 rounded font-mono">{scrapeResult.name}</code>
                </div>
                <div className="space-y-1">
                  <span className="text-slate-500 block uppercase text-[10px] tracking-wider font-semibold">Jurisdiction & Category</span>
                  <span className="text-slate-300 font-medium">{scrapeResult.state} • {scrapeResult.category || 'General'}</span>
                </div>
                <div className="space-y-1">
                  <span className="text-slate-500 block uppercase text-[10px] tracking-wider font-semibold">Target Demographics</span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {scrapeResult.is_for_startups && <span className="bg-blue-500/10 border border-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded text-[10px] font-medium">Startups</span>}
                    {scrapeResult.is_for_women && <span className="bg-pink-500/10 border border-pink-500/20 text-pink-300 px-1.5 py-0.5 rounded text-[10px] font-medium">Women</span>}
                    {scrapeResult.is_for_students && <span className="bg-yellow-500/10 border border-yellow-500/20 text-yellow-300 px-1.5 py-0.5 rounded text-[10px] font-medium">Students</span>}
                    {scrapeResult.is_for_farmers && <span className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded text-[10px] font-medium">Farmers</span>}
                    {!scrapeResult.is_for_startups && !scrapeResult.is_for_women && !scrapeResult.is_for_students && !scrapeResult.is_for_farmers && (
                      <span className="bg-slate-500/10 border border-slate-500/20 text-slate-400 px-1.5 py-0.5 rounded text-[10px] font-medium">General Public</span>
                    )}
                  </div>
                </div>
              </div>
              {scrapeResult.rules && scrapeResult.rules.length > 0 && (
                <div className="space-y-2 border-t border-white/5 pt-3">
                  <span className="text-slate-500 block uppercase text-[10px] tracking-wider font-semibold font-semibold">Extracted Rules ({scrapeResult.rules.length})</span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {scrapeResult.rules.map((rule: any, idx: number) => (
                      <div key={idx} className="bg-slate-900/60 border border-white/5 rounded-lg p-2 flex items-center justify-between font-mono text-[10px]">
                        <span className="text-slate-400">{rule.field_name}</span>
                        <span className="text-indigo-400 font-semibold">{rule.operator}</span>
                        <span className="text-slate-200">{rule.expected_value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Error Display */}
          {scrapeError && (
            <div className="bg-rose-500/5 border border-rose-500/20 rounded-xl p-4 flex items-start space-x-3 text-xs text-rose-400">
              <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <div className="space-y-1">
                <span className="font-bold">Ingestion Failed</span>
                <p className="text-slate-300">{scrapeError}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Visual Charts Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Chart 1: Most Requested Schemes */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Most Requested Schemes</h3>
          <div className="h-72 w-full text-xs">
            {popularityData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={popularityData} margin={{ left: -20, bottom: 20 }}>
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#64748b' }} angle={-25} textAnchor="end" />
                  <YAxis stroke="#64748b" tick={{ fill: '#64748b' }} allowDecimals={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }} />
                  <Bar dataKey="Requests" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChartMsg />
            )}
          </div>
        </div>

        {/* Chart 2: State-wise Policy Awareness */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">State-wise Policy Awareness (%)</h3>
          <div className="h-72 w-full text-xs">
            {stateAwarenessData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stateAwarenessData} margin={{ left: -20, bottom: 10 }}>
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#64748b' }} />
                  <YAxis stroke="#64748b" tick={{ fill: '#64748b' }} domain={[0, 100]} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }} />
                  <Bar dataKey="Awareness" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChartMsg />
            )}
          </div>
        </div>

        {/* Chart 3: Application Bottlenecks */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Application Bottlenecks Distribution</h3>
          <div className="h-72 w-full text-xs flex flex-col items-center justify-center">
            {bottleneckData.length > 0 ? (
              <ResponsiveContainer width="100%" height="80%">
                <PieChart>
                  <Pie
                    data={bottleneckData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {bottleneckData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }} />
                  <Legend verticalAlign="bottom" align="center" wrapperStyle={{ fontSize: '9px', color: '#94a3b8', paddingTop: '10px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChartMsg />
            )}
          </div>
        </div>

        {/* Chart 4: Success rate of underserved demographics */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Demographic Match & Filing Success (%)</h3>
          <div className="h-72 w-full text-xs">
            {demographicsData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart layout="vertical" data={demographicsData} margin={{ left: 10, right: 10 }}>
                  <XAxis type="number" stroke="#64748b" tick={{ fill: '#64748b' }} domain={[0, 100]} />
                  <YAxis type="category" dataKey="name" stroke="#64748b" tick={{ fill: '#64748b', fontSize: '9px' }} width={120} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }} />
                  <Bar dataKey="Success Rate" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChartMsg />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function EmptyChartMsg() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-slate-600 text-[10px]">
      <ShieldAlert className="h-6 w-6 text-slate-700 mb-1" />
      <span>Insufficient survey metrics to construct visualisation.</span>
    </div>
  );
}
