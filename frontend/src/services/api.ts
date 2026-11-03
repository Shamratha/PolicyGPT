import axios from 'axios';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export const getApi = (token?: string | null) => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return axios.create({
    baseURL: BACKEND_URL,
    headers,
    timeout: 30000, // never leave the UI waiting forever if the server hangs
  });
};

export const getDownloadApi = (token?: string | null) => {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return axios.create({
    baseURL: BACKEND_URL,
    headers,
    timeout: 60000,
    responseType: 'blob' // Required for receiving binary PDF streams
  });
};

/**
 * Turns an API/network error into a readable message.
 * FastAPI returns `detail` either as a string or (for validation errors) a list of
 * `{loc, msg}` objects - both are flattened into plain text here.
 */
export const getErrorMessage = (err: unknown, fallback = 'Something went wrong. Please try again.'): string => {
  const e = err as { response?: { data?: { detail?: unknown } }; message?: string; code?: string };
  const detail = e?.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail
      .map((d: { loc?: (string | number)[]; msg?: string }) => {
        const field = (d.loc || []).filter((p) => p !== 'body' && p !== 'query').join('.');
        const msg = (d.msg || 'Invalid value').replace(/^Value error, /, '');
        return field ? `${field}: ${msg}` : msg;
      })
      .join(' | ');
  }
  if (e?.code === 'ERR_NETWORK') return 'Cannot reach the PolicyGPT server. Make sure the backend is running on port 8000.';
  if (e?.code === 'ECONNABORTED') return 'The server took too long to respond. Please try again.';
  return e?.message || fallback;
};
