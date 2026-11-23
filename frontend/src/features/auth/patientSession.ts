// Token phiên bệnh nhân (BR-TK-05). Tách khỏi token nhân viên ở lib/tokenStore.
// Ưu tiên sessionStorage; nếu trình duyệt chặn thì giữ trong bộ nhớ của tab.

export const PATIENT_TOKEN_KEY = 'patient_token'

let memoryToken: string | null = null

export function getPatientToken(): string | null {
  try {
    const stored = sessionStorage.getItem(PATIENT_TOKEN_KEY)
    if (stored) return stored
  } catch {
    // Storage bị chặn: dùng bản trong bộ nhớ.
  }
  return memoryToken
}

export function setPatientToken(token: string | null): void {
  memoryToken = token
  try {
    if (token === null) sessionStorage.removeItem(PATIENT_TOKEN_KEY)
    else sessionStorage.setItem(PATIENT_TOKEN_KEY, token)
  } catch {
    // Storage bị chặn: token vẫn nằm trong bộ nhớ cho đến khi tải lại trang.
  }
}
