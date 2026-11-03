'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { getApi, getDownloadApi, getErrorMessage } from '@/services/api';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, Legend } from 'recharts';
import { FileText, Loader, Users, Compass, Search, Award, ShieldAlert, Globe, Sparkles, CheckCircle2, AlertTriangle } from 'lucide-react';

const CHART_COLORS = ['#2338a8', '#f0a202', '#0e7a55', '#c4313b', '#676d8a', '#7d5bd6'];

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
      setScrapeError(getErrorMessage(e, 'An unknown network error occurred.'));
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
    if (!userId) return;
    // defer so state updates don't run synchronously inside the effect
    const t = setTimeout(fetchAdminStats, 0);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      alert(`Failed to compile PDF report: ${getErrorMessage(e)}`);
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[50vh]">
        <Loader className="h-10 w-10 text-chakra animate-spin" />
        <p className="mt-4 text-xs text-ink-mute">Compiling database logs and survey summaries...</p>
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
          <h1 className="font-display text-4xl font-extrabold text-ink">
            SaaS Platform Impact Analytics
          </h1>
          <p className="text-xs text-ink-mute">
            Review live KPIs, monitor application bottlenecks, and compile Policy Access Reports.
          </p>
        </div>

        <button
          onClick={handleDownloadReport}
          disabled={downloading}
          className="cursor-pointer flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl bg-chakra hover:bg-chakra-dark disabled:opacity-50 text-white font-semibold text-sm shadow-md transition-colors"
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
          <div className="p-3 bg-chakra/10 rounded-xl text-chakra">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-ink">{summary?.users_served || 0}</div>
            <p className="text-xs text-ink-mute uppercase tracking-wider font-semibold">Users Served</p>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 bg-sky-500/10 rounded-xl text-sky-700">
            <Compass className="h-6 w-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-ink">{summary?.schemes_indexed || 0}</div>
            <p className="text-xs text-ink-mute uppercase tracking-wider font-semibold">Schemes Indexed</p>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 bg-purple-500/10 rounded-xl text-purple-700">
            <Search className="h-6 w-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-ink">{summary?.searches_performed || 0}</div>
            <p className="text-xs text-ink-mute uppercase tracking-wider font-semibold">Searches Logged</p>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 bg-leaf/10 rounded-xl text-leaf">
            <Award className="h-6 w-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-ink">{summary?.eligibility_success_rate || 0}%</div>
            <p className="text-xs text-ink-mute uppercase tracking-wider font-semibold">Eligibility Success</p>
          </div>
        </div>
      </div>

      {/* AI Policy Ingestion Pipeline Card */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-line pb-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Globe className="h-5 w-5 text-chakra" />
              <h2 className="text-lg font-bold text-ink">AI Policy Ingestion Pipeline</h2>
            </div>
            <p className="text-xs text-ink-mute">
              Scrape government portal webpages to automatically ingest schemes, extract parameters, synthesize logical eligibility rules, and index text inside ChromaDB.
            </p>
          </div>
          <div>
            <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full bg-chakra/10 border border-chakra/20 text-xs font-semibold text-chakra">
              <Sparkles className="h-3 w-3 animate-pulse text-chakra" />
              <span>GPT-4o Auto-Ingest</span>
            </span>
          </div>
        </div>

        {/* Preset Links */}
        <div className="space-y-2">
          <label className="text-xs text-ink-mute font-semibold uppercase tracking-wider">
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
                className="cursor-pointer px-3 py-1.5 rounded-lg bg-mist hover:bg-line text-ink-soft text-xs transition-colors border border-line hover:border-chakra/30 font-medium"
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
              className="flex-1 bg-paper border border-line rounded-xl px-4 py-3 text-sm text-ink placeholder:text-ink-mute/70 focus:outline-none focus:border-chakra transition-colors"
            />
            <button
              onClick={handleScrape}
              disabled={scraping || !scrapeUrl.trim()}
              className="cursor-pointer bg-chakra hover:bg-chakra-dark disabled:opacity-50 text-white font-semibold text-sm px-6 py-3 rounded-xl shadow-md transition-colors flex items-center justify-center space-x-2 min-w-[160px]"
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
            <div className="bg-paper border border-line rounded-xl p-4 space-y-3 animate-pulse">
              <div className="flex items-center space-x-2 text-xs text-chakra font-semibold">
                <Loader className="h-3 w-3 animate-spin" />
                <span>Running Pipeline: {
                  scrapeStep === 1 ? 'Downloading website HTML...' :
                  scrapeStep === 2 ? 'AI parsing & logical rule extraction...' :
                  'Vector DB indexing & SQL commit...'
                }</span>
              </div>
              <div className="w-full bg-mist rounded-full h-1.5 overflow-hidden">
                <div 
                  className="bg-chakra h-1.5 transition-all duration-500 rounded-full" 
                  style={{ width: `${(scrapeStep / 3) * 100}%` }}
                />
              </div>
              <div className="text-xs text-ink-mute flex justify-between">
                <span className={scrapeStep >= 1 ? "text-chakra font-medium" : ""}>1. Web Scrape</span>
                <span className={scrapeStep >= 2 ? "text-chakra font-medium" : ""}>2. GPT Parameterize</span>
                <span className={scrapeStep >= 3 ? "text-chakra font-medium" : ""}>3. Database Ingestion</span>
              </div>
            </div>
          )}

          {/* Success Result Display */}
          {scrapeResult && (
            <div className="bg-leaf/5 border border-leaf/20 rounded-xl p-5 space-y-4">
              <div className="flex items-center space-x-2 text-leaf">
                <CheckCircle2 className="h-5 w-5" />
                <span className="text-sm font-bold">Scheme Ingested Successfully!</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="space-y-1">
                  <span className="text-ink-mute block uppercase text-xs tracking-wider font-semibold">Official Title</span>
                  <span className="text-ink font-medium">{scrapeResult.title}</span>
                </div>
                <div className="space-y-1">
                  <span className="text-ink-mute block uppercase text-xs tracking-wider font-semibold">Unique Name Slug</span>
                  <code className="text-chakra bg-chakra/10 px-1.5 py-0.5 rounded font-mono">{scrapeResult.name}</code>
                </div>
                <div className="space-y-1">
                  <span className="text-ink-mute block uppercase text-xs tracking-wider font-semibold">Jurisdiction & Category</span>
                  <span className="text-ink-soft font-medium">{scrapeResult.state} • {scrapeResult.category || 'General'}</span>
                </div>
                <div className="space-y-1">
                  <span className="text-ink-mute block uppercase text-xs tracking-wider font-semibold">Target Demographics</span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {scrapeResult.is_for_startups && <span className="bg-blue-500/10 border border-blue-500/20 text-blue-700 px-1.5 py-0.5 rounded text-xs font-medium">Startups</span>}
                    {scrapeResult.is_for_women && <span className="bg-pink-500/10 border border-pink-500/20 text-pink-700 px-1.5 py-0.5 rounded text-xs font-medium">Women</span>}
                    {scrapeResult.is_for_students && <span className="bg-yellow-500/10 border border-yellow-500/20 text-amber-700 px-1.5 py-0.5 rounded text-xs font-medium">Students</span>}
                    {scrapeResult.is_for_farmers && <span className="bg-leaf/10 border border-leaf/20 text-leaf px-1.5 py-0.5 rounded text-xs font-medium">Farmers</span>}
                    {!scrapeResult.is_for_startups && !scrapeResult.is_for_women && !scrapeResult.is_for_students && !scrapeResult.is_for_farmers && (
                      <span className="bg-ink-mute border border-line text-ink-mute px-1.5 py-0.5 rounded text-xs font-medium">General Public</span>
                    )}
                  </div>
                </div>
              </div>
              {scrapeResult.rules && scrapeResult.rules.length > 0 && (
                <div className="space-y-2 border-t border-line pt-3">
                  <span className="text-ink-mute block uppercase text-xs tracking-wider font-semibold font-semibold">Extracted Rules ({scrapeResult.rules.length})</span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {scrapeResult.rules.map((rule: any, idx: number) => (
                      <div key={idx} className="bg-paper border border-line rounded-lg p-2 flex items-center justify-between font-mono text-xs">
                        <span className="text-ink-mute">{rule.field_name}</span>
                        <span className="text-chakra font-semibold">{rule.operator}</span>
                        <span className="text-ink">{rule.expected_value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Error Display */}
          {scrapeError && (
            <div className="bg-rose-500/5 border border-rose-500/20 rounded-xl p-4 flex items-start space-x-3 text-xs text-seal">
              <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <div className="space-y-1">
                <span className="font-bold">Ingestion Failed</span>
                <p className="text-ink-soft">{scrapeError}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Visual Charts Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Chart 1: Most Requested Schemes */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-ink-mute">Most Requested Schemes</h3>
          <div className="h-72 w-full text-xs">
            {popularityData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={popularityData} margin={{ left: -20, bottom: 20 }}>
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#676d8a' }} angle={-25} textAnchor="end" />
                  <YAxis stroke="#64748b" tick={{ fill: '#676d8a' }} allowDecimals={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e1e4ef', borderRadius: 8, color: '#141836' }} />
                  <Bar dataKey="Requests" fill="#2338a8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChartMsg />
            )}
          </div>
        </div>

        {/* Chart 2: State-wise Policy Awareness */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-ink-mute">State-wise Policy Awareness (%)</h3>
          <div className="h-72 w-full text-xs">
            {stateAwarenessData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stateAwarenessData} margin={{ left: -20, bottom: 10 }}>
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#676d8a' }} />
                  <YAxis stroke="#64748b" tick={{ fill: '#676d8a' }} domain={[0, 100]} />
                  <Tooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e1e4ef', borderRadius: 8, color: '#141836' }} />
                  <Bar dataKey="Awareness" fill="#f0a202" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChartMsg />
            )}
          </div>
        </div>

        {/* Chart 3: Application Bottlenecks */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-ink-mute">Application Bottlenecks Distribution</h3>
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
                  <Tooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e1e4ef', borderRadius: 8, color: '#141836' }} />
                  <Legend verticalAlign="bottom" align="center" wrapperStyle={{ fontSize: '11px', color: '#94a3b8', paddingTop: '10px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChartMsg />
            )}
          </div>
        </div>

        {/* Chart 4: Success rate of underserved demographics */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-ink-mute">Demographic Match & Filing Success (%)</h3>
          <div className="h-72 w-full text-xs">
            {demographicsData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart layout="vertical" data={demographicsData} margin={{ left: 10, right: 10 }}>
                  <XAxis type="number" stroke="#64748b" tick={{ fill: '#676d8a' }} domain={[0, 100]} />
                  <YAxis type="category" dataKey="name" stroke="#64748b" tick={{ fill: '#676d8a', fontSize: '11px' }} width={120} />
                  <Tooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e1e4ef', borderRadius: 8, color: '#141836' }} />
                  <Bar dataKey="Success Rate" fill="#0e7a55" radius={[0, 4, 4, 0]} />
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
    <div className="h-full flex flex-col items-center justify-center text-ink-mute text-xs">
      <ShieldAlert className="h-6 w-6 text-ink-mute mb-1" />
      <span>Insufficient survey metrics to construct visualisation.</span>
    </div>
  );
}
