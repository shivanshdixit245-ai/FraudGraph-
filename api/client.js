import axios from 'axios';

const getBaseURL = () => {
  const envURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  // Hard correction for stale environment variables in deployment
  if (envURL.includes('fraudgraph-api.onrender.com')) {
    return 'https://fraudgraph-mxz6.onrender.com';
  }
  return envURL;
};

const client = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000,
});

// Request interceptor for logging
client.interceptors.request.use((config) => {
  if (import.meta.env.DEV) {
    console.log(`[API Request] ${config.method.toUpperCase()} ${config.url}`, config.data || '');
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Response interceptor for graceful fallbacks
client.interceptors.response.use((response) => {
  return response;
}, (error) => {
  const is5xx = error.response && error.response.status >= 500;
  const isNetworkError = !error.response;

  if (is5xx || isNetworkError) {
    console.warn(`[API Error] ${error.config?.url}:`, error.message);
    // Return null instead of throwing for 5xx/Network errors to allow mock fallbacks
    return { data: null };
  }

  return Promise.reject(error);
});

export default client;
