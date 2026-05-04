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
  getById: (id) => api.get(`/inbounds/${id}`)
};

// 出库API
export const outboundAPI = {
  getList: (params) => api.get('/outbounds', { params }),
  create: (data) => api.post('/outbounds', data),
  getById: (id) => api.get(`/outbounds/${id}`)
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

export default api;