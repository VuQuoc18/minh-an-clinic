/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** CHỈ DEV: token nhân viên tự gắn vào lời gọi API khi chưa có đăng nhập thật (FR-TK-04). */
  readonly VITE_DEV_STAFF_TOKEN?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
