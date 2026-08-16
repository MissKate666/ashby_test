import axios from 'axios';
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '' });
export const analyze = (params) => api.post('/api/analyze', params).then(r => r.data);
export const exportUrl = (type, params) => `/api/export/${type}?${new URLSearchParams(params).toString()}`;
