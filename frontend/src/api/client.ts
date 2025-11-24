import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const apiClient = axios.create({
    baseURL: API_BASE,
    timeout: 5000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Attach token from localStorage to each request if present
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Login used by Login.tsx (email/password)
export const login = async (email: string, password: string) => {
    // backend expects username, accept email as username for now
    const res = await apiClient.post('/auth/login', { username: email, password });
    if (res.data && res.data.access_token) {
        localStorage.setItem('access_token', res.data.access_token);
    }
    return res.data;
};

export const register = async (userData: any) => {
    const res = await apiClient.post('/auth/register', userData);
    return res.data;
};

export const getUserData = async () => {
    const res = await apiClient.get('/users/me');
    return res.data;
};

export const createEvent = async (eventData: any) => {
    const res = await apiClient.post('/events/', eventData);
    return res.data;
};

export const fetchEvents = async () => {
    const res = await apiClient.get('/events/');
    return res.data;
};

export const submitAvailability = async (availabilityData: any) => {
    const res = await apiClient.post('/availability', availabilityData);
    return res.data;
};

export const fetchAvailability = async (userId?: string) => {
    const url = userId ? `/availability/${userId}` : '/availability';
    const res = await apiClient.get(url);
    return res.data;
};

export const getShifts = async () => {
    const res = await apiClient.get('/shifts');
    return res.data;
};

export const logout = () => {
    localStorage.removeItem('access_token');
};