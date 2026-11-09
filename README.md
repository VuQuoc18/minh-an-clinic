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

### Xem màn hình Tiếp đón (SCR-001) khi dev

Chưa có đăng nhập thật (FR-TK-04), nên dùng token dev:

```bash
# 1. Trong .env: đặt DEV_STAFF_TOKEN=<chuỗi ngẫu nhiên dài> (chỉ dev, không dùng ở môi trường khác)
docker compose up --build -d
# 2. Tạo bảng và dữ liệu mẫu (dữ liệu giả, chỉ chạy được khi đã đặt DEV_STAFF_TOKEN)
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.dev_seed
# 3. Mở http://localhost:5173/quan-tri/tiep-don
```

Dữ liệu mẫu được tạo theo giờ hiện tại để có đủ các trạng thái: nút "Xác nhận đến" bấm được,
nút bị khóa (quá sớm, quá muộn), đã đến có số thứ tự, tin gửi lỗi, đã hủy. Chạy lại `app.dev_seed`
thì không tạo trùng. Nếu thêm ở gần nửa đêm, một số lịch hẹn rơi sang ngày khác sẽ bị bỏ qua.

Nếu xem màn hình trong khung xem trước dạng iframe sandbox (origin `null`) hoặc qua tunnel, trình
duyệt chặn lời gọi API vì thiếu CORS. Chỉ khi dev, đặt `CORS_ALLOW_ORIGINS=*` trong `.env`
(hoặc liệt kê origin, ngăn cách bằng dấu phẩy) rồi khởi động lại backend. Để trống thì CORS tắt.

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
