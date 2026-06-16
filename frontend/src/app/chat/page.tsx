'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { getApi } from '@/services/api';
import { MessageSquare, Sparkles, Send, Loader, Globe, ArrowRight, ClipboardList, ShieldAlert, Award } from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: Array<{
    scheme_id: string;
    scheme_name: string;
    scheme_title: string;
    state: string;
    category: string;
  }>;
  confidence_score?: number;
}

export default function ChatPage() {
  const { isLoaded, userId, getToken } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMsg, setInputMsg] = useState('');
  const [lang, setLang] = useState('en'); // 'en', 'hi', 'kn'
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<any>(null);
  const [recentQueries, setRecentQueries] = useState<string[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const fetchDashboardDetails = async () => {
    try {
      const token = await getToken();
      const api = getApi(token);
      
      // Sync user first
      await api.post('/api/auth/sync-user');

      // Fetch dashboard metrics (which carries profile state + history)
      const profileRes = await api.get('/api/profiles/me');
      setProfile(profileRes.data);

      const dashRes = await api.get('/api/dashboard');
      if (dashRes.data && dashRes.data.recent_searches) {
        setRecentQueries(dashRes.data.recent_searches.map((q: any) => q.query));
      }
    } catch (e) {
      console.error('Error fetching details:', e);
    }
  };

  useEffect(() => {
    if (isLoaded && !userId) {
      router.push('/');
      return;
    }
    if (userId) {
      fetchDashboardDetails();
    }
  }, [isLoaded, userId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSendMessage = async (e?: React.FormEvent, textOverride?: string) => {
    e?.preventDefault();
    const query = textOverride || inputMsg.trim();
    if (!query || loading) return;

    if (!textOverride) setInputMsg('');
    
    // Add user message
    const newMsg: ChatMessage = { role: 'user', content: query };
    setMessages((prev) => [...prev, newMsg]);
    setLoading(true);

    try {
      const token = await getToken();
      const api = getApi(token);

      // Build chat history payload for RAG API context
      const chatHistory = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await api.post('/api/chat', {
        message: query,
        language: lang,
        history: chatHistory,
      });

      const resData = response.data;
      const botMsg: ChatMessage = {
        role: 'assistant',
        content: resData.response,
        citations: resData.citations,
        confidence_score: resData.confidence_score,
      };

      setMessages((prev) => [...prev, botMsg]);
      
      // Refresh sidebar recent searches list
      fetchDashboardDetails();
    } catch (e) {
      console.error('Error sending chat query:', e);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'I encountered an error verifying scheme guidelines. Please make sure your server is online and try again.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLang(e.target.value);
  };

  const renderConfidence = (score: number) => {
    const color = score > 80 ? 'text-emerald-400 bg-emerald-500/10' : score > 50 ? 'text-amber-400 bg-amber-500/10' : 'text-rose-400 bg-rose-500/10';
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${color}`}>
        Grounded Confidence: {score}%
      </span>
    );
  };

  return (
    <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-140px)] min-h-[500px]">
      {/* 1. Left Sidebar Details */}
      <div className="hidden lg:flex flex-col space-y-6 lg:col-span-1 border-r border-white/5 pr-6 overflow-y-auto">
        {/* User profile summary */}
        <div className="glass-panel p-5 rounded-2xl space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
            <UserIcon />
            <span>Profile Context</span>
          </h3>
          {profile ? (
            <div className="text-xs space-y-2 text-slate-300">
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">Name</span>
                <span className="font-medium text-white truncate max-w-[120px]">{profile.name || 'Unspecified'}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">Age / Gender</span>
                <span className="font-medium text-white">{profile.age ? `${profile.age} yrs` : '—'} / {profile.gender}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">Residency State</span>
                <span className="font-medium text-white">{profile.state}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">Occupation</span>
                <span className="font-medium text-white">{profile.occupation}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">Annual Income</span>
                <span className="font-medium text-white">{profile.income ? `₹${profile.income.toLocaleString()}` : '—'}</span>
              </div>
              <div className="flex justify-between pt-1">
                <span className="text-slate-500">Startup Founder</span>
                <span className="font-medium text-indigo-400">{profile.startup_status ? 'Yes' : 'No'}</span>
              </div>
              <div className="pt-2">
                <button
                  onClick={() => router.push('/profile')}
                  className="cursor-pointer w-full py-1.5 rounded-lg border border-white/10 hover:bg-white/5 text-[10px] font-bold text-center text-slate-300 transition-colors"
                >
                  Edit Profile Fields
                </button>
              </div>
            </div>
          ) : (
            <p className="text-[10px] text-slate-500">Loading profile...</p>
          )}
        </div>

        {/* Recent Searches */}
        <div className="flex-1 flex flex-col space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Recent Inquiries</h3>
          {recentQueries.length > 0 ? (
            <div className="space-y-2 overflow-y-auto max-h-[200px]">
              {recentQueries.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(undefined, q)}
                  className="w-full text-left truncate text-xs text-slate-400 hover:text-indigo-400 hover:bg-white/5 p-2 rounded-xl transition-all border border-transparent hover:border-white/5"
                >
                  {q}
                </button>
              ))}
            </div>
          ) : (
            <p className="text-[10px] text-slate-500">Your recent searches will appear here.</p>
          )}
        </div>
      </div>

      {/* 2. Main Chat Panel */}
      <div className="lg:col-span-3 flex flex-col h-full bg-slate-900/10 border border-white/5 rounded-2xl overflow-hidden glass-panel">
        {/* Top bar controls */}
        <div className="h-14 border-b border-white/5 px-6 flex items-center justify-between bg-slate-950/20">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-bold text-white flex items-center space-x-1.5">
              <span>Policy Assistant Chat</span>
              <Sparkles className="h-3.5 w-3.5 text-indigo-400 animate-pulse" />
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <Globe className="h-4 w-4 text-slate-400" />
            <select
              value={lang}
              onChange={handleLanguageChange}
              className="bg-slate-900 border border-white/10 text-xs font-medium rounded-lg px-2 py-1 text-slate-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="en">English</option>
              <option value="hi">Hindi (हिन्दी)</option>
              <option value="kn">Kannada (ಕನ್ನಡ)</option>
            </select>
          </div>
        </div>

        {/* Chat message history logs */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-4 max-w-md mx-auto">
              <div className="p-4 bg-indigo-500/10 rounded-full text-indigo-400">
                <MessageSquare className="h-10 w-10" />
              </div>
              <h2 className="text-lg font-bold text-white">Ask PolicyGPT</h2>
              <p className="text-xs text-slate-400 leading-relaxed">
                Describe your demographics (e.g., age, gender, occupation, location) and interests. For example:
              </p>
              <button
                onClick={() => handleSendMessage(undefined, "I am a 22-year-old female engineering graduate from Karnataka interested in starting a business.")}
                className="cursor-pointer text-xs text-left p-3 rounded-xl border border-white/10 bg-slate-900/50 hover:bg-slate-900 hover:border-indigo-500/50 transition-all text-slate-300 w-full flex items-center justify-between group"
              >
                <span>"I am a 22-year-old female engineering graduate from Karnataka interested in starting a business."</span>
                <ArrowRight className="h-4 w-4 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-all" />
              </button>
            </div>
          ) : (
            messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl p-4 space-y-3 text-sm leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-none shadow-md'
                      : 'bg-slate-950/60 border border-white/10 text-slate-200 rounded-bl-none'
                  }`}
                >
                  {/* Markdown content */}
                  <div className="whitespace-pre-line text-xs sm:text-sm">{m.content}</div>

                  {m.role === 'assistant' && (
                    <div className="border-t border-white/5 pt-3 space-y-3">
                      {/* Grounded confidence score indicator */}
                      {m.confidence_score !== undefined && renderConfidence(m.confidence_score)}

                      {/* Source attribution citation cards */}
                      {m.citations && m.citations.length > 0 && (
                        <div className="space-y-1.5">
                          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Source Schemes Cited:</span>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {m.citations.map((c, cIdx) => (
                              <div
                                key={cIdx}
                                className="p-2.5 rounded-lg border border-white/5 bg-slate-900/50 hover:border-indigo-500/30 transition-colors flex flex-col text-left space-y-1"
                              >
                                <span className="text-xs font-bold text-white line-clamp-1">{c.scheme_title}</span>
                                <span className="text-[9px] text-slate-500">{c.state} | {c.category}</span>
                                <div className="flex space-x-2 pt-1 border-t border-white/5 mt-1">
                                  <button
                                    onClick={() => router.push(`/explorer?id=${c.scheme_id}`)}
                                    className="cursor-pointer text-[9px] font-bold text-sky-400 hover:text-sky-300 flex items-center space-x-0.5"
                                  >
                                    <span>Explorer Details</span>
                                  </button>
                                  <button
                                    onClick={async () => {
                                      try {
                                        const token = await getToken();
                                        const api = getApi(token);
                                        const startRes = await api.post(`/api/dashboard/applications/${c.scheme_id}/start`);
                                        router.push('/dashboard');
                                      } catch (err) {
                                        console.error('Failed to start application:', err);
                                      }
                                    }}
                                    className="cursor-pointer text-[9px] font-bold text-indigo-400 hover:text-indigo-300 flex items-center space-x-0.5 ml-auto"
                                  >
                                    <span>Apply Scheme</span>
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {/* Loader */}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-950/60 border border-white/10 rounded-2xl rounded-bl-none p-4 flex items-center space-x-3 text-slate-400">
                <Loader className="h-4 w-4 animate-spin text-indigo-400" />
                <span className="text-xs">PolicyGPT is indexing guidelines and matching demographics...</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input box form */}
        <form onSubmit={handleSendMessage} className="p-4 border-t border-white/5 bg-slate-950/20 flex items-center space-x-3">
          <input
            type="text"
            value={inputMsg}
            onChange={(e) => setInputMsg(e.target.value)}
            disabled={loading}
            placeholder="Ask about startup grants, farming subsidies, scholarship programs..."
            className="flex-1 bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-xs sm:text-sm focus:outline-none focus:border-indigo-500 transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !inputMsg.trim()}
            className="cursor-pointer p-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600 text-white shadow transition-all duration-200"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}

function UserIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
      <path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.29-.226.395-.615.223-.932A8.974 8.974 0 0010 10a8.974 8.974 0 00-6.535 4.493z" />
    </svg>
  );
}
