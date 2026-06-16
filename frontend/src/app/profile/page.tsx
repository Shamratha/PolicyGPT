'use client';

import { useState, useEffect } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { getApi } from '@/services/api';
import { Save, User, UserPlus, MapPin, GraduationCap, Coins, Briefcase, Sparkles, Loader } from 'lucide-react';

const INDIAN_STATES = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
  'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
  'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
  'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
  'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Delhi', 'Central'
];

const OCCUPATIONS = [
  'Student', 'Farmer', 'Entrepreneur', 'Unemployed', 'Government Employee', 'Private Sector', 'Self-Employed'
];

const EDUCATION_LEVELS = [
  'Below 10th', '10th Pass', '12th Pass', 'Graduate', 'Post Graduate', 'Doctorate'
];

export default function ProfilePage() {
  const { isLoaded, userId, getToken } = useAuth();
  const { user } = useUser();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Form State
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: 'Female',
    state: 'Karnataka',
    education: 'Graduate',
    occupation: 'Unemployed',
    income: '',
    startup_status: false,
    student_status: false,
  });

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      
      // First sync the user to ensure SQL record exists
      const api = getApi(token);
      await api.post('/api/auth/sync-user');
      
      const response = await api.get('/api/profiles/me');
      if (response.data) {
        const p = response.data;
        setFormData({
          name: p.name || user?.fullName || '',
          age: p.age ? String(p.age) : '',
          gender: p.gender || 'Female',
          state: p.state || 'Karnataka',
          education: p.education || 'Graduate',
          occupation: p.occupation || 'Unemployed',
          income: p.income ? String(p.income) : '',
          startup_status: !!p.startup_status,
          student_status: !!p.student_status,
        });
      }
    } catch (e: any) {
      console.error('Error fetching profile:', e);
      setErrorMsg('Failed to load profile details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isLoaded && !userId) {
      // If not logged in, redirect to clerk authentication
      router.push('/');
      return;
    }

    if (userId) {
      fetchProfile();
    }
  }, [isLoaded, userId]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData((prev) => ({ ...prev, [name]: checked }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      const token = await getToken();
      const api = getApi(token);
      
      const payload = {
        ...formData,
        age: formData.age ? parseInt(formData.age, 10) : null,
        income: formData.income ? parseFloat(formData.income) : null,
      };

      await api.post('/api/profiles/me', payload);
      setSuccessMsg('Profile saved successfully! Redirecting to Chat...');
      
      setTimeout(() => {
        router.push('/chat');
      }, 1500);
    } catch (e: any) {
      console.error('Error saving profile:', e);
      setErrorMsg('Failed to save profile. Please verify your inputs.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[50vh]">
        <Loader className="h-10 w-10 text-indigo-400 animate-spin" />
        <p className="mt-4 text-xs text-slate-400">Loading your profile preferences...</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto py-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-sky-400 bg-clip-text text-transparent">
          Personalize Eligibility Profile
        </h1>
        <p className="text-xs text-slate-400">
          This data is used directly by the PolicyGPT AI agent and eligibility checker to matching government opportunities.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="glass-panel p-8 rounded-2xl space-y-6">
        {successMsg && (
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs rounded-xl flex items-center space-x-2">
            <Sparkles className="h-4 w-4" />
            <span>{successMsg}</span>
          </div>
        )}
        {errorMsg && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl">
            {errorMsg}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {/* Name */}
          <div className="flex flex-col space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1">
              <User className="h-3 w-3" />
              <span>Full Name</span>
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="Aishwarya R"
              className="bg-slate-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          {/* Age */}
          <div className="flex flex-col space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1">
              <UserPlus className="h-3 w-3" />
              <span>Age</span>
            </label>
            <input
              type="number"
              name="age"
              value={formData.age}
              onChange={handleInputChange}
              placeholder="22"
              required
              className="bg-slate-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          {/* Gender */}
          <div className="flex flex-col space-y-2">
            <label className="text-xs font-semibold text-slate-300">Gender</label>
            <select
              name="gender"
              value={formData.gender}
              onChange={handleInputChange}
              className="bg-slate-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="Female">Female</option>
              <option value="Male">Male</option>
              <option value="Other">Other</option>
            </select>
          </div>

          {/* State */}
          <div className="flex flex-col space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1">
              <MapPin className="h-3 w-3" />
              <span>Residency State</span>
            </label>
            <select
              name="state"
              value={formData.state}
              onChange={handleInputChange}
              className="bg-slate-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
            >
              {INDIAN_STATES.map((st) => (
                <option key={st} value={st}>{st}</option>
              ))}
            </select>
          </div>

          {/* Education */}
          <div className="flex flex-col space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1">
              <GraduationCap className="h-3 w-3" />
              <span>Highest Education</span>
            </label>
            <select
              name="education"
              value={formData.education}
              onChange={handleInputChange}
              className="bg-slate-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
            >
              {EDUCATION_LEVELS.map((el) => (
                <option key={el} value={el}>{el}</option>
              ))}
            </select>
          </div>

          {/* Occupation */}
          <div className="flex flex-col space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1">
              <Briefcase className="h-3 w-3" />
              <span>Occupation</span>
            </label>
            <select
              name="occupation"
              value={formData.occupation}
              onChange={handleInputChange}
              className="bg-slate-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
            >
              {OCCUPATIONS.map((oc) => (
                <option key={oc} value={oc}>{oc}</option>
              ))}
            </select>
          </div>

          {/* Income */}
          <div className="flex flex-col space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1">
              <Coins className="h-3 w-3" />
              <span>Family Annual Income (₹)</span>
            </label>
            <input
              type="number"
              name="income"
              value={formData.income}
              onChange={handleInputChange}
              placeholder="120000"
              required
              className="bg-slate-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>
        </div>

        {/* Checkboxes */}
        <div className="border-t border-white/5 pt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label className="flex items-center space-x-3 cursor-pointer p-4 rounded-xl border border-white/5 bg-slate-900/30 hover:bg-slate-900/50 transition-colors">
            <input
              type="checkbox"
              name="startup_status"
              checked={formData.startup_status}
              onChange={handleCheckboxChange}
              className="h-4 w-4 accent-indigo-500 rounded border-white/10"
            />
            <div className="flex flex-col text-left">
              <span className="text-xs font-bold text-white">Founder / Starting Business</span>
              <span className="text-[10px] text-slate-400">Mark if you plan to launch a business.</span>
            </div>
          </label>

          <label className="flex items-center space-x-3 cursor-pointer p-4 rounded-xl border border-white/5 bg-slate-900/30 hover:bg-slate-900/50 transition-colors">
            <input
              type="checkbox"
              name="student_status"
              checked={formData.student_status}
              onChange={handleCheckboxChange}
              className="h-4 w-4 accent-indigo-500 rounded border-white/10"
            />
            <div className="flex flex-col text-left">
              <span className="text-xs font-bold text-white">Active Student</span>
              <span className="text-[10px] text-slate-400">Mark if currently enrolled in academic courses.</span>
            </div>
          </label>
        </div>

        <div className="border-t border-white/5 pt-6 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="cursor-pointer flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-md transition-colors"
          >
            {saving ? (
              <>
                <Loader className="h-4 w-4 animate-spin" />
                <span>Saving Preferences...</span>
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                <span>Save Profile</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
