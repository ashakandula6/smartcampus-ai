import axios from 'axios';

// Set up the base URL pointing directly to your local FastAPI backend
const API = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
});

// Interceptor to attach a dev token since your backend uses verify_token
API.interceptors.request.use((config) => {
  // Bypasses Cognito validation gracefully when DEV_MODE=True on your backend
  config.headers.Authorization = `Bearer dev-mock-token`;
  return config;
});

export const apiService = {
  // Upload a fresh PDF document
  uploadDocument: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await API.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Get all documents processed by the current user
  getDocuments: async () => {
    const response = await API.get('/documents/');
    return response.data;
  },

  // Check the status of a specific document background task
  getDocumentStatus: async (documentId) => {
    const response = await API.get(`/documents/${documentId}/status`);
    return response.data;
  },

  // Send a RAG query to your Groq pipeline
  askQuestion: async (documentId, question) => {
    const response = await API.post('/chat/ask', {
      document_id: documentId,
      question: question,
    });
    return response.data;
  },

  // Retrieve chat history for a document
  getChatHistory: async (documentId) => {
    const response = await API.get(`/chat/${documentId}/history`);
    return response.data;
  }
};