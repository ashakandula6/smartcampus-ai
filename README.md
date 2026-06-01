# 🎓 SmartCampus AI — Complete Build Guide

A GenAI-powered study assistant for students. Upload lecture PDFs, ask questions, generate quizzes, and track weak topics.

## Tech Stack
- **Frontend**: React + Tailwind CSS (Vercel / S3 static hosting)
- **Backend**: FastAPI (Python) on AWS EC2
- **AI**: Claude API (RAG pipeline with FAISS)
- **Storage**: AWS S3 (PDFs)
- **Database**: AWS RDS PostgreSQL
- **Auth**: AWS Cognito
- **PDF Parsing**: PyMuPDF
- **CI/CD**: GitHub Actions

---

## 📁 Project Structure
```
smartcampus-ai/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers
│   │   ├── core/         # Config, security
│   │   ├── models/       # DB models
│   │   ├── services/     # Business logic (RAG, quiz, S3)
│   │   └── utils/        # Helpers
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── store/
│   └── package.json
├── infra/
│   ├── terraform/        # AWS infra as code
│   └── scripts/          # Setup scripts
└── .github/workflows/    # CI/CD
```

---

## 🚀 Week-by-Week Build Plan

| Week | Goal |
|------|------|
| 1 | Backend setup: FastAPI + PDF upload + S3 |
| 2 | RAG pipeline: embeddings + Claude Q&A |
| 3 | Quiz generation + scoring |
| 4 | AWS deployment: EC2 + RDS + Cognito |
| 5 | Frontend: React UI + dashboard |
| 6 | CI/CD + polish + demo video |

---

## Prerequisites
- Python 3.11+
- Node.js 18+
- AWS CLI configured (`aws configure`)
- Anthropic API key
- PostgreSQL (local dev) or RDS (production)
