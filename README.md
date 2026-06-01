# SmartCampus AI 🎓🤖

An AI-powered smart study assistant designed for university students to streamline learning from dense lecture notes. Upload your lecture PDFs, and interact with a multi-turn RAG (Retrieval-Augmented Generation) workspace or dynamically generate customized study materials.

---

## 🚀 Key Features

* **PDF Layout Processing**: Automatically extracts text contents, strips PDF artifacts, and breaks down documents into contextually optimized chunks.
* **FAISS Vector Library Workspace**: Builds and indexes highly localized vector spaces using state-of-the-art embedding models to search for context matches instantly.
* **Context-Driven AI Chat**: Leverages high-performance open-source models via Groq (`llama-3.3-70b-versatile`) to provide accurate, lecture-aligned answers without expensive token overhead.
* **Workspace Chat History Tracking**: Persists multi-turn conversations in an isolated database environment allowing students to pick up right where they left off.
* **Minimalist Premium Interface**: Clean, dual-panel dashboard featuring split-pane sidebar libraries, document status polling indicators, and smooth responsive layout controls.

---

## 🛠️ Tech Stack

### Backend
* **Framework**: FastAPI (Python)
* **Vector Search**: FAISS (Facebook AI Similarity Search)
* **Embedding Model**: SentenceTransformers (`all-MiniLM-L6-v2`)
* **Inference Engine**: Groq SDK (`llama-3.3-70b-versatile`)
* **Database / ORM**: SQLite / SQLAlchemy
* **File Processing**: PyMuPDF (`fitz`)

### Frontend
* **Core**: React (Vite environment)
* **HTTP Client**: Axios
* **Styling**: Modern CSS3 (Variables, Flexbox, CSS Grid)

---

## 📁 Project Structure

```text
smartcampus-ai/
├── backend/                  # FastAPI Application Codebase
│   ├── app/
│   │   ├── api/              # Core Routing Layers (chat, documents, users)
│   │   ├── core/             # Configuration & Database Management setups
│   │   ├── models/           # SQLAlchemy DB Schemas
│   │   └── services/         # PDF processing, FAISS indices, and LLM providers
│   ├── main.py               # Application entry point & startup lifespans
│   └── requirements.txt      # Python dependencies tracker
│
├── frontend/                 # React Application Codebase
│   ├── src/
│   │   ├── api.js            # Unified Axios endpoint client
│   │   ├── App.jsx           # Main Interactive Workspace container UI
│   │   ├── App.css           # Workspace structural styles layout
│   │   └── index.css         # Global core variable tokens & themes
│   └── package.json          # Node dependencies tracker
└── .gitignore                # Pushes protection control rule configurations
