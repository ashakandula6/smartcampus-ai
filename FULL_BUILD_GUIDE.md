# SmartCampus AI — Complete Step-by-Step Build Guide

> Full-stack GenAI study assistant | FastAPI + React + AWS + Claude API

---

## 🗺️ Architecture Overview

```
Browser (React)
    │
    ▼  HTTPS
AWS Cognito ──→ JWT Token ──→ FastAPI (EC2 t2.micro)
                                    │
                        ┌───────────┼───────────┐
                        ▼           ▼           ▼
                    AWS S3       AWS RDS     FAISS Index
                  (PDFs +       (Postgres)   (in S3)
                  Indexes)
                        │
                        ▼
                  Anthropic Claude API
                  (Q&A + Quiz Gen)
```

---

## WEEK 1 — Local Backend Setup

### 1.1 Clone and create virtual environment

```bash
git clone https://github.com/yourusername/smartcampus-ai.git
cd smartcampus-ai/backend

python3.11 -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 1.2 Set up local PostgreSQL

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu
sudo apt install postgresql
sudo systemctl start postgresql

# Create DB
psql -U postgres -c "CREATE DATABASE smartcampus;"
psql -U postgres -c "CREATE USER smartcampus_user WITH PASSWORD 'password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE smartcampus TO smartcampus_user;"
```

### 1.3 Create .env file

```bash
cp .env.example .env
# Edit .env with your keys
```

Fill in:
- `ANTHROPIC_API_KEY` → Get from https://console.anthropic.com
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` → IAM user with S3 access
- `S3_BUCKET_NAME` → unique name like `smartcampus-pdfs-yourname`

### 1.4 Run the backend

```bash
uvicorn main:app --reload --port 8000
```

Visit http://localhost:8000/docs — you should see the Swagger UI!

---

## WEEK 2 — RAG Pipeline

The RAG (Retrieval-Augmented Generation) pipeline works like this:

```
PDF Upload → Parse Text → Split into Chunks → Embed Chunks → FAISS Index → S3
                                                                    ↓
User Question → Embed Question → Search FAISS → Top 5 Chunks → Claude → Answer
```

### Test the pipeline manually

```python
# test_rag.py — run from backend/ with venv activated
import sys
sys.path.insert(0, '.')

from app.services.pdf_service import process_pdf_to_chunks
from app.services.rag_service import build_and_store_index, retrieve_relevant_chunks
from app.services.claude_service import answer_question

# Test with a sample PDF
with open("test.pdf", "rb") as f:
    pdf_bytes = f.read()

chunks = process_pdf_to_chunks(pdf_bytes)
print(f"✅ Got {len(chunks)} chunks")

# Build index (saves to S3)
faiss_key = build_and_store_index("test-doc-123", chunks)
print(f"✅ Index saved to S3: {faiss_key}")

# Query
results = retrieve_relevant_chunks(faiss_key, "What is the main topic?", top_k=3)
answer = answer_question("What is the main topic?", results)
print(f"✅ Answer: {answer[:200]}...")
```

---

## WEEK 3 — Frontend Setup

### 3.1 Install Node dependencies

```bash
cd frontend
cp .env.example .env
# Fill in VITE_API_URL=http://localhost:8000/api/v1 for now

npm install
npm run dev
```

Visit http://localhost:3000

### 3.2 Frontend .env (local dev)

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
VITE_COGNITO_CLIENT_ID=your-client-id
```

---

## WEEK 4 — AWS Deployment

### 4.1 Launch EC2 Instance

1. Go to AWS Console → EC2 → Launch Instance
2. Settings:
   - **Name**: smartcampus-backend
   - **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
   - **Instance type**: t2.micro (Free tier)
   - **Key pair**: Create new → download .pem file (keep this safe!)
   - **Security group**: Allow inbound — SSH (22), HTTP (80), HTTPS (443), Custom TCP 8000
3. Click Launch

### 4.2 Set up IAM Role for EC2 (no hardcoded keys in production!)

1. IAM → Roles → Create Role → EC2
2. Add permissions:
   - `AmazonS3FullAccess`
   - `AmazonRDSFullAccess` (if using RDS)
3. Name it `smartcampus-ec2-role`
4. Attach to your EC2: Instance → Actions → Security → Modify IAM Role

### 4.3 Connect and run setup script

```bash
# From your laptop
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# On EC2 — run setup script
curl -o setup.sh https://raw.githubusercontent.com/yourusername/smartcampus-ai/main/infra/scripts/setup_ec2.sh
chmod +x setup.sh
./setup.sh
```

### 4.4 Set up RDS PostgreSQL (Free Tier)

1. AWS Console → RDS → Create Database
2. Settings:
   - Engine: PostgreSQL 15
   - Template: **Free tier**
   - DB instance: db.t3.micro
   - DB name: `smartcampus`
   - Username: `smartcampus_user`
   - Password: strong password
   - Public access: No (EC2 connects via VPC)
3. After creation, copy the endpoint URL
4. Update `DATABASE_URL` in EC2's `.env`:
   ```
   DATABASE_URL=postgresql://smartcampus_user:password@your-rds-endpoint.rds.amazonaws.com:5432/smartcampus
   ```

### 4.5 Set up Cognito

Follow `infra/COGNITO_SETUP.md` for step-by-step instructions.

### 4.6 Deploy Frontend to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

cd frontend
vercel login
vercel --prod
```

Set environment variables in Vercel Dashboard:
- `VITE_API_URL` = `http://your-ec2-ip/api/v1`
- `VITE_COGNITO_USER_POOL_ID`
- `VITE_COGNITO_CLIENT_ID`

---

## WEEK 5 — CI/CD with GitHub Actions

### 5.1 Add GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|--------|-------|
| `EC2_HOST` | Your EC2 public IP |
| `EC2_SSH_KEY` | Contents of your .pem file |
| `ANTHROPIC_API_KEY` | Your Anthropic key |
| `AWS_ACCESS_KEY_ID` | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret |
| `VITE_API_URL` | `https://your-ec2-ip/api/v1` |
| `VITE_COGNITO_USER_POOL_ID` | Cognito pool ID |
| `VITE_COGNITO_CLIENT_ID` | Cognito client ID |
| `VERCEL_TOKEN` | From vercel.com/account/tokens |
| `VERCEL_ORG_ID` | From Vercel project settings |
| `VERCEL_PROJECT_ID` | From Vercel project settings |

### 5.2 Push to trigger deployment

```bash
git add .
git commit -m "feat: initial deployment"
git push origin main
```

Watch it run: GitHub → Actions tab

---

## WEEK 6 — Polish & Demo

### 6.1 Add HTTPS to EC2 with Let's Encrypt

```bash
# Get a free domain first (try Freenom or use EC2 Elastic IP)
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

### 6.2 Run tests

```bash
cd backend
pytest tests/ -v
```

### 6.3 Record demo video

Suggested flow for demo:
1. Sign up / login (Cognito)
2. Upload a lecture PDF (show it processing)
3. Ask 2-3 questions → show AI answers
4. Generate a quiz → answer questions → see score
5. Show weak topic analysis
6. Show GitHub Actions running

Use Loom (free) to record screen.

---

## 📊 What to Put on Your Resume

```
SmartCampus AI — Full-Stack GenAI Study Assistant
• Built a RAG-powered study assistant using Anthropic Claude API + FAISS vector search,
  enabling students to query lecture PDFs in natural language with ~2s response time
• Architected AWS infrastructure: EC2 (backend), S3 (storage), RDS PostgreSQL (data),
  Cognito (auth) — all within free tier limits
• Implemented automated MCQ quiz generation from lecture notes using LLM prompting,
  with AI-driven weak topic analysis for personalized study recommendations  
• Built React frontend with real-time document processing status and streaming chat UI
• Set up CI/CD pipeline (GitHub Actions) for automated testing and zero-downtime deployment
  to EC2 + Vercel
Tech: Python, FastAPI, React, AWS (EC2/S3/RDS/Cognito), FAISS, Anthropic Claude, PostgreSQL
```

---

## 💰 AWS Free Tier Cost Breakdown

| Service | Free Tier Limit | Expected Usage |
|---------|----------------|----------------|
| EC2 t2.micro | 750 hours/month | ~744 hours (always-on) |
| RDS t3.micro | 750 hours/month + 20GB | < 5GB |
| S3 | 5GB + 20K requests | < 1GB |
| Cognito | 50,000 MAUs | < 100 users |
| Textract | 1,000 pages/month | Optional |
| **Total cost** | **~$0** | Within free tier |

> ⚠️ Set up AWS Billing Alerts at $1 and $5 to avoid surprises!

---

## 🛑 Common Issues & Fixes

**"FAISS not found"**
```bash
pip install faiss-cpu  # not faiss-gpu unless you have a GPU
```

**"Connection refused" on EC2**
```bash
sudo systemctl status smartcampus
sudo journalctl -u smartcampus -n 50  # see error logs
```

**Cognito 401 errors**
- Check User Pool ID and Client ID match exactly
- Ensure no client secret is set on the app client

**CORS errors from frontend**
- Add your Vercel URL to `allow_origins` in `main.py`
- Restart the FastAPI service

**Large PDF timing out**
- Increase Nginx `proxy_read_timeout` to 300s
- Consider Lambda for async processing of very large files
