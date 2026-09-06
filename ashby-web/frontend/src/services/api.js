import axios from 'axios';
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '' });
export const analyze = (params) => api.post('/api/analyze', params).then(r => r.data);
export const getGroups = () => api.get('/api/groups').then(r => r.data);
// Goes through the same configured `api` instance (VITE_API_URL) as analyze()/
// getGroups() above, instead of a hardcoded root-relative path -- otherwise
// export requests would 404 (or hit the wrong host) in any deployment where
// the frontend and backend are served from different origins.
const EXPORT_FILENAMES = { csv: 'ashby_materials.csv', excel: 'ashby_materials.xlsx' };
export const exportFile = (type, params) => api
  .get(`/api/export/${type}`, { params, responseType: 'blob' })
  .then(r => {
    const match = /filename="?([^";]+)"?/i.exec(r.headers['content-disposition'] || '');
    return { blob: r.data, filename: match?.[1] || EXPORT_FILENAMES[type] || 'export' };
  });
