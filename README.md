# AI-Powered CV Parser & Formatter

## Quick Start (Docker)
1. Clone the repo
2. Copy .env.example to .env, add your GEMINI_API_KEY
3. Run: `docker-compose up --build`
4. Open: http://localhost:3000
5. Login: admin@cvparser.com / Admin@123

## Default Credentials
| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@cvparser.com | Admin@123 |

## Features
- AI-Powered CV parsing and formatting
- Support for multiple AI providers (Gemini, OpenAI, Ollama)
- User roles (Super Admin, Admin, Recruiter)
- Export to DOCX and PDF
- Custom CV templates with placeholders

## AI Provider Setup
- Gemini: Get API key from aistudio.google.com
- OpenAI: Get key from platform.openai.com  
- Ollama: Install from ollama.ai, run `ollama pull deepseek-r1`

## Template Format
- Placeholders: Use any format like {{name}}, {{candidate_name}}, {{skill1}}
- Or upload without placeholders — AI will mirror the structure

## Architecture Diagram (ASCII)
```
+-----------+      +----------------+      +------------------+
|           |      |                |      |                  |
|  Browser  +----->+ FastAPI Backend+----->+ AI Provider      |
| (React)   |      |                |      | (Gemini/OpenAI)  |
|           +<-----+                +<-----+                  |
+-----------+      +-------+--------+      +------------------+
                           |
                           v
                   +-------+--------+
                   |                |
                   |   PostgreSQL   |
                   |                |
                   +----------------+
```

## API Documentation
Available at http://localhost:8000/docs (Swagger UI)

## Local Development (without Docker)

1. Start PostgreSQL DB and update DATABASE_URL in .env
2. For backend:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
3. For frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```
