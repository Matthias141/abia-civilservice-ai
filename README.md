# AbiaCS Assistant — Abia State Civil Service AI Chatbot

An AI-powered chatbot that provides instant, accurate answers about Abia State Civil Service rules, regulations, procedures, and policies using Retrieval-Augmented Generation (RAG).

## What This Project Does

AbiaCS Assistant is a web-based chatbot built for Abia State civil servants and the general public to get instant answers about:

- **Promotions** — eligibility, APER scores, examination requirements, timelines
- **Leave Policies** — annual, sick, maternity, paternity, study, casual leave
- **Pensions & Retirement** — CPS contributions, gratuity calculations, voluntary retirement
- **Salary Structures** — grade levels (GL 01–17), CONPSS, CONHESS, CONTISS scales
- **Disciplinary Procedures** — queries, suspensions, appeals, dismissal processes
- **Recruitment** — entry requirements, probation, confirmation procedures
- **MDA Information** — ministries, departments, agencies, and their functions
- **Financial Regulations** — procurement, budgeting, allowances

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 + React 18 + Tailwind CSS |
| Backend | Python 3.11 + FastAPI |
| AI Model | Claude Sonnet (Anthropic API) |
| Embeddings | HuggingFace all-MiniLM-L6-v2 |
| Vector DB | ChromaDB |
| Deployment | Vercel (frontend) + Railway (backend) |

## Prerequisites

- Node.js v18+ or v20+
- Python 3.11+
- Git 2.x+
- An [Anthropic API key](https://console.anthropic.com)
- Civil service PDF documents

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Edit and add your ANTHROPIC_API_KEY
# Place PDF documents in ./documents/
python ingest.py
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000 in your browser.

### Docker

```bash
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send a message and receive an AI response |
| GET | `/health` | Health check |
| POST | `/api/ingest` | Trigger document re-ingestion |
| GET | `/api/suggested-questions` | Get suggested questions for the UI |

## Project Structure

```
abia-civilservice-ai/
├── backend/
│   ├── main.py              # FastAPI server + RAG pipeline
│   ├── ingest.py            # Document ingestion script
│   ├── config.py            # Configuration and settings
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment variable template
│   ├── documents/           # Place civil service PDFs here
│   └── tests/               # Backend tests
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js app router pages
│   │   ├── components/      # React components
│   │   └── lib/             # API client
│   ├── package.json
│   └── .env.example
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── CLAUDE.md
```

## License

MIT License

---

Built for the people of Abia State.
