// Lưu token nhân viên. Ưu tiên sessionStorage; nếu trình duyệt chặn truy cập (ví dụ iframe có
// `sandbox` nhưng thiếu `allow-same-origin` sẽ ném SecurityError) thì dùng bộ nhớ trong tab.
// Đăng nhập thật làm ở FR-TK-04.

export const TOKEN_KEY = 'staff_token'

let memoryToken: string | null = null

export function getToken(): string | null {
  try {
    const stored = sessionStorage.getItem(TOKEN_KEY)
    if (stored) return stored
  } catch {
    // Storage bị chặn: dùng bản trong bộ nhớ.
  }
  return memoryToken
}

export function setToken(token: string | null): void {
  memoryToken = token
  try {
    if (token === null) sessionStorage.removeItem(TOKEN_KEY)
    else sessionStorage.setItem(TOKEN_KEY, token)
  } catch {
    // Storage bị chặn: token vẫn nằm trong bộ nhớ cho đến khi tải lại trang.
  }
}
