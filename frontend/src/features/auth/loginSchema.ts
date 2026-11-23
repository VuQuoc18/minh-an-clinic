// BR-TK-08: đúng 10 chữ số, bắt đầu bằng 0. Máy chủ kiểm tra lại.
const PHONE_RE = /^0[0-9]{9}$/

export const PHONE_ERROR = 'Số điện thoại gồm 10 chữ số và bắt đầu bằng 0.'

/** Trả thông báo lỗi dưới ô Số điện thoại, hoặc null nếu hợp lệ. Ô trống chưa báo lỗi. */
export function phoneError(phone: string): string | null {
  if (phone === '') return null
  return PHONE_RE.test(phone) ? null : PHONE_ERROR
}

/** Nút "Đăng nhập" chỉ mở khi số điện thoại đúng định dạng và mật khẩu không trống. */
export function canSubmit(phone: string, password: string): boolean {
  return PHONE_RE.test(phone) && password !== ''
}
