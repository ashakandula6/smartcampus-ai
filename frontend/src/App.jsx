import { useState, useEffect, useRef } from 'react';
import { apiService } from './api';
import './App.css';

function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  
  // UI Status Tracking
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const chatEndRef = useRef(null);

  // Fetch initial documents list on mount
  useEffect(() => {
    loadDocuments();
  }, []);

  // Auto-scroll chat window to the latest response
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadDocuments = async () => {
    try {
      const data = await apiService.getDocuments();
      // Sort with newest files at the top
      const sorted = [...data].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      setDocuments(sorted);
    } catch (err) {
      console.error("Failed to load documents:", err);
    }
  };

  // Poll document status if it's processing in the background
  const pollDocumentStatus = (docId) => {
    const interval = setInterval(async () => {
      try {
        const data = await apiService.getDocumentStatus(docId);
        if (data.status === 'ready' || data.status === 'failed') {
          clearInterval(interval);
          loadDocuments(); // Refresh list to catch updated status code
          if (selectedDoc && selectedDoc.id === docId) {
            setSelectedDoc(prev => ({ ...prev, status: data.status }));
          }
        }
      } catch (err) {
        clearInterval(interval);
        console.error("Error polling document status:", err);
      }
    }, 3000);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    try {
      const newDoc = await apiService.uploadDocument(file);
      setDocuments(prev => [newDoc, ...prev]);
      setSelectedDoc(newDoc);
      setMessages([]); // Clear chat for new context
      
      if (newDoc.status === 'processing') {
        pollDocumentStatus(newDoc.id);
      }
    } catch (err) {
      alert(err.response?.data?.detail || "Upload error occurred.");
    } finally {
      setUploading(false);
      e.target.value = ''; // Reset input element
    }
  };

  const handleSelectDocument = async (doc) => {
    setSelectedDoc(doc);
    setMessages([]);
    if (doc.status === 'ready') {
      try {
        const history = await apiService.getChatHistory(doc.id);
        const historicalMessages = [];
        for (let i = history.length - 1; i >= 0; i--) {
          historicalMessages.push({ sender: 'user', text: history[i].question });
          historicalMessages.push({ sender: 'ai', text: history[i].answer });
        }
        setMessages(historicalMessages);
      } catch (err) {
        console.error("Could not fetch chat history:", err);
      }
    }
  };

  // Delete a document handler
  const handleDeleteDoc = async (e, docId) => {
    e.stopPropagation(); // Avoid triggering item select event line wrapper
    if (!window.confirm("Are you sure you want to delete this document?")) return;
    
    try {
      // Connects directly to backend API template route layout row
      await axios.delete(`http://127.0.0.1:8000/api/v1/documents/${docId}`, {
        headers: { Authorization: `Bearer dev-mock-token` }
      });
      if (selectedDoc?.id === docId) setSelectedDoc(null);
      loadDocuments();
    } catch (err) {
      console.error("Failed to delete document:", err);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!query.trim() || !selectedDoc || asking) return;
    if (selectedDoc.status !== 'ready') {
      alert("Please wait until processing finishes!");
      return;
    }

    const userText = query;
    setMessages(prev => [...prev, { sender: 'user', text: userText }]);
    setQuery('');
    setAsking(true);

    try {
      const response = await apiService.askQuestion(selectedDoc.id, userText);
      setMessages(prev => [...prev, { sender: 'ai', text: response.answer }]);
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'system', text: "Error fetching AI response. Check API logs." }]);
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="workspace-layout">
      {/* Sidebar Section */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>SmartCampus AI</h2>
          <span className="subtitle">Study Assistant</span>
        </div>

        <label className="upload-btn">
          {uploading ? 'Uploading PDF...' : '＋ Upload Lecture Note'}
          <input type="file" accept=".pdf" onChange={handleFileUpload} disabled={uploading} hidden />
        </label>

        <div className="document-list">
          <h3>Your Library</h3>
          {documents.length === 0 ? (
            <p className="empty-state">No notes uploaded yet.</p>
          ) : (
            documents.map(doc => (
              <div 
                key={doc.id} 
                className={`document-item ${selectedDoc?.id === doc.id ? 'active' : ''}`}
                onClick={() => handleSelectDocument(doc)}
              >
                <div className="doc-info">
                  <div className="doc-main-row">
                    <span className="doc-name" title={doc.filename}>{doc.filename}</span>
                    <button className="delete-doc-btn" onClick={(e) => handleDeleteDoc(e, doc.id)}>×</button>
                  </div>
                  <span className={`status-badge ${doc.status}`}>
                    {doc.status}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* Main Area Dashboard Section */}
      <main className="chat-container">
        {selectedDoc ? (
          <>
            <header className="chat-header">
              <div>
                <h2>{selectedDoc.filename}</h2>
                <p className="status-meta">
                  Status: <span className={`text-status ${selectedDoc.status}`}>{selectedDoc.status}</span>
                  {selectedDoc.total_chunks > 0 && ` • ${selectedDoc.total_chunks} text chunks indexed`}
                </p>
              </div>
            </header>

            <div className="messages-window">
              {messages.length === 0 && selectedDoc.status === 'ready' && (
                <div className="chat-placeholder">
                  <p>👋 Your index is compiled successfully via FAISS vector memory.</p>
                  <p>Ask anything about this document below!</p>
                </div>
              )}
              {selectedDoc.status === 'processing' && (
                <div className="chat-placeholder">
                  <div className="spinner"></div>
                  <p>Parsing PDF layouts into vector embeddings...</p>
                </div>
              )}
              {messages.map((msg, index) => (
                <div key={index} className={`message-row ${msg.sender}`}>
                  <div className="message-bubble">
                    {msg.text}
                  </div>
                </div>
              ))}
              {asking && (
                <div className="message-row ai processing">
                  <div className="message-bubble typing">Thinking...</div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <form className="chat-input-area" onSubmit={handleSendMessage}>
              <input 
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={selectedDoc.status === 'ready' ? "Ask a question about your notes..." : "Waiting for processing to finish..."}
                disabled={selectedDoc.status !== 'ready' || asking}
              />
              <button type="submit" disabled={!query.trim() || asking || selectedDoc.status !== 'ready'}>
                Send
              </button>
            </form>
          </>
        ) : (
          <div className="no-selection-state">
            <svg className="splash-icon" viewBox="0 0 24 24" width="64" height="64">
              <path fill="currentColor" d="M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3M19,19H5V5H19V19M7,10H17V12H7V10M7,6H17V8H7V6M7,14H13V16H7V14Z" />
            </svg>
            <h2>Welcome to your AI Study Hub</h2>
            <p>Select a lecture note from the library sidebar or upload a new PDF to run interactive multi-turn questions.</p>
          </div>
        )}
      </main>
    </div>
  );
}

import axios from 'axios';
export default App;