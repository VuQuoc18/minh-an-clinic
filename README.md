# minh-an-clinic

Hệ thống đặt lịch khám Phòng khám Minh An.

## Cấu trúc

- `backend/`: FastAPI (Python)
- `frontend/`: React + Vite + TypeScript + Vitest
- `docker-compose.yml`: PostgreSQL 16 + backend + frontend (môi trường dev)

## Chạy bằng Docker

```bash
cp .env.example .env   # đặt POSTGRES_PASSWORD
docker compose up --build
```

Backend: http://localhost:8000/health · Frontend: http://localhost:5173

## Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload   # http://localhost:8000/health
pytest
ruff check . && ruff format --check .
export DATABASE_URL=...   # xem .env.example
alembic upgrade head
```

## Frontend

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173, proxy /api -> http://localhost:8000
npm test
npm run typecheck
npm run lint
npm run format:check
npm run build
```
