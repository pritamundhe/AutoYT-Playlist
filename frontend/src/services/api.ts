/**
 * API client for backend communication
 */
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: `${API_URL}/api`,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Document API
export const documentAPI = {
    upload: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await apiClient.post('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    get: async (documentId: string) => {
        const response = await apiClient.get(`/documents/${documentId}`);
        return response.data;
    },

    list: async () => {
        const response = await apiClient.get('/documents');
        return response.data;
    },

    delete: async (documentId: string) => {
        const response = await apiClient.delete(`/documents/${documentId}`);
        return response.data;
    },
};

// Topic API
export const topicAPI = {
    extract: async (documentId: string, minKeywords = 3, maxDepth = 3) => {
        const response = await apiClient.post(`/extract-topics/${documentId}`, null, {
            params: { min_keywords: minKeywords, max_depth: maxDepth },
        });
        return response.data;
    },

    get: async (documentId: string) => {
        const response = await apiClient.get(`/topics/${documentId}`);
        return response.data;
    },

    getFlat: async (documentId: string) => {
        const response = await apiClient.get(`/topics/${documentId}/flat`);
        return response.data;
    },
};

// Playlist API
export const playlistAPI = {
    generate: async (data: any) => {
        const response = await apiClient.post('/generate-playlist', data);
        return response.data;
    },

    get: async (playlistId: string) => {
        const response = await apiClient.get(`/playlists/${playlistId}`);
        return response.data;
    },

    list: async (documentId?: string) => {
        const params = documentId ? { document_id: documentId } : {};
        const response = await apiClient.get('/playlists', { params });
        return response.data;
    },

    export: async (playlistId: string, format: 'json' | 'csv' | 'youtube') => {
        const response = await apiClient.post('/export-playlist', {
            playlist_id: playlistId,
            format,
        });
        return response.data;
    },
};

// Evaluation API
export const evaluationAPI = {
    evaluate: async (playlistId: string) => {
        const response = await apiClient.post('/evaluate', {
            playlist_id: playlistId,
        });
        return response.data;
    },

    get: async (playlistId: string) => {
        const response = await apiClient.get(`/evaluation/${playlistId}`);
        return response.data;
    },

    submitFeedback: async (data: any) => {
        const response = await apiClient.post('/feedback', data);
        return response.data;
    },
};

export default apiClient;
