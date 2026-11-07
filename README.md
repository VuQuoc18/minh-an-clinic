# minh-an-clinic

Hệ thống đặt lịch khám Phòng khám Minh An.

## Cấu trúc

- `backend/`: FastAPI (Python)
- `frontend/`: React + Vite + Vitest

## Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload   # http://localhost:8000/health
pytest
```

## Frontend

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173, proxy /api -> http://localhost:8000
npm test
npm run build
```
