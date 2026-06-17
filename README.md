# 🃏 LevelUp Poker Lab

A non-gambling, educational poker trainer for ages 13–25. Practice Hold'em vs AI bots, train with GTO-inspired drills, and get AI-style coaching.

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173, backend at http://localhost:8000.
