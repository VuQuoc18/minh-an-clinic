# minh-an-clinic

Hệ thống đặt lịch khám Phòng khám Minh An.

## Cấu trúc

```
backend/                     FastAPI + SQLAlchemy 2 + Alembic (Python 3.11+)
  app/
    main.py                  tạo ứng dụng: cấu hình, CORS, xử lý lỗi, gắn router
    api.py                   gom router các phân hệ dưới tiền tố /api, có /api/health
    core/                    phần dùng chung: config, db, security (xác thực), clock, errors, logging
    models/                  bảng dữ liệu dùng chung (danh mục, bệnh nhân, lịch hẹn)
    modules/<phân hệ>/       mỗi phân hệ một thư mục: router.py, service.py, schemas.py
    dev_seed.py              dữ liệu mẫu cho dev
  migrations/                Alembic
  tests/                     theo cùng cấu trúc với app/
  pyproject.toml             thư viện, cấu hình pytest và ruff
frontend/                    React 19 + Vite + TypeScript + TanStack Query + Vitest
  src/
    main.tsx                 điểm vào
    app/                     App (định tuyến), providers, QueryClient
    components/              ErrorBoundary và bộ thành phần giao diện (ui/)
    features/<phân hệ>/      màn hình, gọi API, khoá truy vấn (queryKeys.ts), kiểu dữ liệu
    lib/                     gọi HTTP, token, định dạng
    styles/                  design system
  nginx.conf.template        dùng cho bản chạy thật (đích `prod` trong Dockerfile)
.specforge/run.yml           cấu hình chạy cả hệ thống trong SpecForge sandbox
docker-compose.yml           Postgres + backend + frontend cho dev
```

Quy ước chính:

- Mọi API nằm dưới `/api` (ví dụ `/api/reception/appointments`, tài liệu API ở `/api/docs`).
  Frontend gọi `/api/...` cùng origin; Vite (dev), nginx (Docker) và SpecForge đều chuyển nguyên
  đường dẫn sang backend.
- Lỗi luôn có dạng `{"detail": {"code", "message"}}`; lỗi nhập sai dữ liệu (422) có thêm `errors`
  là danh sách `{field, message}`. Lỗi nghiệp vụ ném `AppError` (`app/core/errors.py`).
- Thêm phân hệ mới: tạo `backend/app/modules/<tên>/` rồi gắn router trong `app/api.py`; ở frontend
  tạo `src/features/<tên>/` và thêm route trong `src/app/App.tsx` (tải theo nhu cầu bằng `lazy`).
- Frontend import bằng đường dẫn `@/` (ví dụ `@/components/ui/button`).

## Chạy bằng Docker

```bash
cp .env.example .env   # đặt POSTGRES_PASSWORD, và DEV_STAFF_TOKEN nếu muốn xem màn hình Tiếp đón
docker compose up --build
```

Backend tự chạy migration khi khởi động. Backend: http://localhost:8000/api/health · Frontend:
http://localhost:5173

### Xem màn hình Tiếp đón (SCR-001) khi dev

Chưa có đăng nhập thật (FR-TK-04), nên dùng token dev:

```bash
# 1. Trong .env: đặt DEV_STAFF_TOKEN=<chuỗi ngẫu nhiên dài> (chỉ dev, không dùng ở môi trường khác)
docker compose up --build -d
# 2. Tạo dữ liệu mẫu (dữ liệu giả, chỉ chạy được khi đã đặt DEV_STAFF_TOKEN)
docker compose exec backend python -m app.dev_seed
# 3. Mở http://localhost:5173/quan-tri/tiep-don
```

Dữ liệu mẫu được tạo theo giờ hiện tại để có đủ các trạng thái: nút "Xác nhận đến" bấm được,
nút bị khóa (quá sớm, quá muộn), đã đến có số thứ tự, tin gửi lỗi, đã hủy. Chạy lại `app.dev_seed`
thì không tạo trùng. Nếu thêm ở gần nửa đêm, một số lịch hẹn rơi sang ngày khác sẽ bị bỏ qua.

### Bản chạy thật

`backend/Dockerfile` chạy bằng người dùng thường và có kiểm tra sức khoẻ ở `/api/health`.
`frontend/Dockerfile` mặc định build ra file tĩnh và phục vụ bằng nginx (đặt `API_UPSTREAM` là địa
chỉ backend, mặc định `http://backend:8000`). Migration chạy riêng bằng `alembic upgrade head`.

## Chạy trong SpecForge sandbox

`.specforge/run.yml` khai báo Postgres, các bước cài đặt (thư viện, migration, dữ liệu mẫu) và hai
dịch vụ: `backend` nhận `/api`, `frontend` nhận phần còn lại. Bản xem trước có địa chỉ riêng nên
ứng dụng chạy ở `/`, không cần cấu hình Vite hay đường dẫn tạm thời nào khác. Token dev trong file
này chỉ dùng cho dữ liệu giả trong sandbox.

## Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=...        # xem .env.example; chấp nhận cả dạng postgresql://
alembic upgrade head
uvicorn app.main:app --reload  # http://localhost:8000/api/health
pytest
ruff check . && ruff format --check .
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
