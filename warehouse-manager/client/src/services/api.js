import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 物料API
export const materialAPI = {
  getList: (params) => api.get('/materials', { params }),
  getById: (id) => api.get(`/materials/${id}`),
  create: (data) => api.post('/materials', data),
  update: (id, data) => api.put(`/materials/${id}`, data),
  delete: (id) => api.delete(`/materials/${id}`)
};

// 入库API
export const inboundAPI = {
  getList: (params) => api.get('/inbounds', { params }),
  create: (data) => api.post('/inbounds', data),
  getById: (id) => api.get(`/inbounds/${id}`),
  update: (id, data) => api.put(`/inbounds/${id}`, data),
  delete: (id) => api.delete(`/inbounds/${id}`)
};

// 出库API
export const outboundAPI = {
  getList: (params) => api.get('/outbounds', { params }),
  create: (data) => api.post('/outbounds', data),
  getById: (id) => api.get(`/outbounds/${id}`),
  update: (id, data) => api.put(`/outbounds/${id}`, data),
  delete: (id) => api.delete(`/outbounds/${id}`)
};

// 工具API
export const toolsAPI = {
  importExcel: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/import/excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  exportMaterials: () => api.get('/export/materials', { responseType: 'blob' }),
  exportInbounds: () => api.get('/export/inbounds', { responseType: 'blob' }),
  syncReport: () => api.post('/sync/report')
};

// AI识别API
export const aiAPI = {
  recognize: async (mode, { text, file }) => {
    const formData = new FormData();
    formData.append('mode', mode);
    if (text) {
      formData.append('text', text);
    }
    if (file) {
      formData.append('file', file);
    }
    // Create a fresh axios instance without global headers that would override FormData
    // Use 360s timeout to match server-side MiniMax API timeout
    const instance = axios.create({
      baseURL: API_BASE,
      timeout: 360000
      // No headers here - let axios set Content-Type automatically for FormData
    });
    return instance.post('/ai/recognize', formData);
  }
};

// 编码库API
export const encodingAPI = {
  getCategories: () => api.get('/encoding/categories'),
  getRules: (params) => api.get('/encoding/rules', { params }),
  getRule: (id) => api.get(`/encoding/rules/${id}`),
  createRule: (data) => api.post('/encoding/rules', data),
  updateRule: (id, data) => api.put(`/encoding/rules/${id}`, data),
  deleteRule: (id) => api.delete(`/encoding/rules/${id}`),
  generateCode: (data) => api.post('/encoding/generate', data),
  matchKeyword: (keyword) => api.get(`/encoding/match/${keyword}`)
};

export default api;