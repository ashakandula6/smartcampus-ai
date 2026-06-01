
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
* **Database / ORM**: SQLite (Local Dev) / PostgreSQL (Production) / SQLAlchemy
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

```

---

## 🔧 Installation & Local Setup

### Prerequisites

* Python 3.10+
* Node.js (v18 or higher)
* A free **Groq API Key** (Get one at [console.groq.com](https://console.groq.com/))

### 1. Backend Server Configuration

Navigate into the backend project folder, set up a virtual workspace, and initiate components:

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

```

Create a **`.env`** file directly in your `backend/` folder:

```env
APP_NAME="SmartCampus AI"
DATABASE_URL="sqlite:///./smartcampus.db"
GROQ_API_KEY="your_free_groq_api_key_here"
DEV_MODE=True

```

Run your local development backend worker:

```bash
uvicorn main:app --reload

```

The interactive Swagger interface documentation will be hosted live on `http://127.0.0.1:8000/docs`.

### 2. Frontend React Configuration

Open a second terminal window, move inside the frontend dashboard workspace, and run:

```bash
cd frontend

# Install package dependencies
npm install

# Launch Vite development preview engine
npm run dev

```

Open up your browser and point it directly to `http://localhost:5173/` to interact with your workspace dashboard!

---

## 🌐 Production Deployment Architecture Guide (AWS & Vercel)

### 1. AWS S3 Storage Provisioning

* Go to AWS Console → **S3** → **Create Bucket**.
* **Name**: `smartcampus-pdfs-ashakandula` *(Must be globally unique)*.
* **Region**: `ap-south-1` *(Mumbai)*.
* **Block all public access**: Keep it ✅ **ON** *(Backend handles transfers securely internal to server identity)*.

### 2. IAM User Security Configuration

* Go to AWS Console → **IAM** → **Users** → **Create User**: `smartcampus-backend`.
* Attach these permissions policies directly:
* `AmazonS3FullAccess`
* `AmazonCognitoPowerUser`


* Navigate to **Security Credentials** → **Create access key** *(Use Case: Application running outside AWS)*.
* Copy keys into your production `.env` variable track configuration space:
```env
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxx
AWS_REGION=ap-south-1
S3_BUCKET_NAME=smartcampus-pdfs-ashakandula

```



### 3. RDS Managed PostgreSQL Production Database Setup

* Go to AWS Console → **RDS** → **Create Database**.
* **Engine**: PostgreSQL *(Free Tier Template)*.
* **Settings**: DB Instance Class `db.t3.micro`, Storage `20GB`.
* **Credentials**: Master username `postgres`, record your chosen strong password safely.
* **Public access**: **Yes** *(Allows local tracking verification migrations)*.
* **VPC security group**: Create new → name it `smartcampus-rds-sg`.
* After instantiation, extract the **Endpoint URL** and modify backend configurations:
```env
DATABASE_URL=postgresql://postgres:yourpassword@smartcampus.xxxxxxxxx.ap-south-1.rds.amazonaws.com:5432/smartcampus

```


* Open inbound networks: Go to EC2 Security Groups → `smartcampus-rds-sg` → **Inbound rules** → Add Rule: **PostgreSQL (Port 5432)**, source `0.0.0.0/0`.
* Install client wrappers in backend path environments:
```bash
pip install psycopg2-binary

```



### 4. EC2 Production Engine Instance Setup

* Launch an EC2 Instance: **Ubuntu 22.04 LTS**, instance type `t2.micro` *(Free tier)*.
* Create and download Key Pair `smartcampus-key.pem`.
* **Inbound Rules Configuration**:
* SSH (Port 22): Source `My IP`
* Custom TCP (Port 8000): Source `0.0.0.0/0`
* HTTP (Port 80): Source `0.0.0.0/0`



#### Deployment Script via SSH Client Terminal (Windows PowerShell):

```powershell
# Move file to your native secure directory configuration 
Move-Item C:\Users\YourName\Downloads\smartcampus-key.pem C:\Users\YourName\.ssh\

# Secure read file permissions
icacls C:\Users\YourName\.ssh\smartcampus-key.pem /inheritance:r /grant:r "$($env:USERNAME):(R)"

# Authenticate server connection
ssh -i C:\Users\YourName\.ssh\smartcampus-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

```

#### Inside Linux Server CLI Terminal Environment:

```bash
# System dependency compilation setup
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y

# Clone repo tracking structures
git clone [https://github.com/ashakandula6/smartcampus-ai.git](https://github.com/ashakandula6/smartcampus-ai.git)
cd smartcampus-ai/backend

# Virtual execution isolation environment initialization
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create live server tracking variables configuration
nano .env
# [Paste full environment records keys profile tracking parameters. Set DEV_MODE=False]

```

#### Keep Backend Alive continuously via Supervisor Daemon Control:

```bash
sudo apt install supervisor -y
sudo nano /etc/supervisor/conf.d/smartcampus.conf

```

*Paste this execution declaration framework alignment template inside*:

```ini
[program:smartcampus]
command=/home/ubuntu/smartcampus-ai/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
directory=/home/ubuntu/smartcampus-ai/backend
user=ubuntu
autostart=true
autorestart=true
environment=HOME="/home/ubuntu",USER="ubuntu"

```

*Reload processes to run permanently background systems*:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status

```

### 5. Deploy Frontend Client Workspace on Vercel

* Move inside your local workspace path: `cd frontend`.
* Create `frontend/.env.production` tracking target pointing to EC2 address:
```env
VITE_API_URL=http://YOUR_EC2_PUBLIC_IP:8000

```


* Global configuration installation deployment run execution lines:
```bash
npm install -g vercel
vercel

```


* Follow command CLI prompts. Vercel generates a secure cloud endpoint (e.g., `https://smartcampus-ai.vercel.app`).
* Final Step: Update backend `main.py` CORS setup with your new Vercel production URL domain to authorize request streams cleanly!

---

## 🔒 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👨‍💻 Contributing

Feel free to open issues or fork this repository to implement additional features like custom multiple-choice quiz evaluation panels or automatic semantic summary tables!

```

***

### Save and Push Code Upwards:
Run these commands in your root path to update your GitHub timeline dashboard directly:
```bash
git add README.md
git commit -m "docs: integrate comprehensive production cloud deployment guide architectures"
git push

```

---
<img width="1920" height="973" alt="image" src="https://github.com/user-attachments/assets/8aced703-302c-4e9e-8a99-8720845fa651" />



