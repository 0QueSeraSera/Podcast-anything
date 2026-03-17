# CLAUDE.md - Claude Code Instructions

## Project Overview

Podcast-Anything is a web application that converts GitHub repositories into educational audio explanations. It uses Claude Code CLI for repository analysis and script generation, and Alibaba Cloud DashScope for text-to-speech synthesis.

## Project Structure

```
Podcast-Anything/
├── backend/           # FastAPI Python backend
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/routes/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   └── requirements.txt
├── frontend/          # Next.js PWA frontend
│   ├── app/
│   ├── components/
│   ├── hooks/
│   └── public/
├── ROADMAP.md         # Project roadmap
└── CLAUDE.md          # This file
```

## Development Guidelines

### Code Style
- Python: Follow PEP 8, use type hints
- TypeScript: Use strict mode, prefer functional components
- Comments: Only for non-obvious logic

### API Design
- RESTful endpoints under `/api/v1/`
- Use Pydantic models for request/response validation
- Return proper HTTP status codes

### Error Handling
- Raise HTTPException for API errors
- Log errors with context
- Provide user-friendly error messages

## Environment Variables

Backend requires:
```
ANTHROPIC_API_KEY=your_key
DASHSCOPE_API_KEY=your_key
```

## Running the Application

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Testing

- Backend: pytest with pytest-asyncio
- Frontend: Jest + React Testing Library

## Key Implementation Notes

1. **Claude Code Integration**: Use `claude-agent-sdk` with streaming responses
2. **TTS Chunking**: Split text into ~500 character chunks for optimal synthesis
3. **Chapter Markers**: Use ID3 CHAP frames for MP3 chapters
4. **PWA**: Service worker caches audio for offline playback
