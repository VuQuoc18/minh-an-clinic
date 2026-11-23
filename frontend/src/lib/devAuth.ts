import { setToken } from './tokenStore'

// CHỈ DÙNG KHI DEV: nếu đặt VITE_DEV_STAFF_TOKEN thì dùng làm token nhân viên (tạm thời đến khi
// có đăng nhập thật ở FR-TK-04). Bản build production không có biến này nên không làm gì.
export function installDevToken(
  token: string | undefined,
  isDev: boolean,
  save: (token: string) => void = setToken,
): boolean {
  if (!isDev || !token) return false
  save(token)
  return true
}
