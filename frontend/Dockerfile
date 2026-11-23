# Ba đích build:
#   dev  : Vite dev server có HMR (docker-compose dùng đích này)
#   build: build ra file tĩnh trong /app/dist
#   prod : nginx phục vụ file tĩnh và chuyển /api sang backend (đích mặc định, ở cuối file)
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM deps AS build
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS prod
# Địa chỉ backend mà nginx chuyển /api tới (template được envsubst khi container khởi động).
ENV API_UPSTREAM=http://backend:8000
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
