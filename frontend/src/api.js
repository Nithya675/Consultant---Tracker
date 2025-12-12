import axios from 'axios';
import { API_CONFIG, AUTH_CONFIG } from './config';

const api = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(AUTH_CONFIG.TOKEN_STORAGE_KEY);
    if (token) {
      config.headers.Authorization = `${AUTH_CONFIG.TOKEN_HEADER_PREFIX} ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      const token = localStorage.getItem(AUTH_CONFIG.TOKEN_STORAGE_KEY);
      if (token) {
        localStorage.removeItem(AUTH_CONFIG.TOKEN_STORAGE_KEY);
        if (!window.location.pathname.includes('/login') &&
          !window.location.pathname.includes('/register')) {
          window.location.href = '/login';
        }
      }
    }
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);


export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (userData) => api.post('/auth/register', userData),
  getCurrentUser: () => api.get('/auth/me'),
  refreshToken: () => api.post('/auth/refresh'),
};

export const jobAPI = {
  getAll: () => api.get('/jobs/'),
  create: (jobData) => api.post('/jobs/', jobData),
  getOne: (id) => api.get(`/jobs/${id}`),
  update: (id, jobData) => api.put(`/jobs/${id}`, jobData),
  classifyJD: (jdText) => api.post('/jobs/classify', { text: jdText }),
  uploadJDFile: (jobId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/jobs/${jobId}/upload-jd-file`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  downloadJDFile: (jobId) => api.get(`/jobs/${jobId}/download-jd-file`, { responseType: 'blob' }),
};

export const submissionAPI = {
  getAll: () => api.get('/submissions/'),
  create: (data) => api.post('/submissions/', data),
  updateStatus: (id, status) => api.put(`/submissions/${id}`, { status }),
};

export const consultantAPI = {
  getAll: () => api.get('/consultants/'),
  getProfile: () => api.get('/consultants/me'),
  updateProfile: (data) => api.put('/consultants/me', data),
  uploadResume: (file) => {
    const formData = new FormData();
    formData.append('resume', file);
    return api.post('/consultants/me/resume', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  downloadResume: () => api.get('/consultants/me/resume', { responseType: 'blob' }),
  getStats: () => api.get('/consultants/me/stats'),
};

export const recruiterAPI = {
  getProfile: () => api.get('/recruiters/me'),
  updateProfile: (data) => api.put('/recruiters/me', data),
};

export default api;
