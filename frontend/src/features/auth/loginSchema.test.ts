import { canSubmit, PHONE_ERROR, phoneError } from './loginSchema'

describe('phoneError (BR-TK-08)', () => {
  it('chấp nhận số 10 chữ số bắt đầu bằng 0', () => {
    expect(phoneError('0912345678')).toBeNull()
  })

  it('chưa báo lỗi khi ô còn trống', () => {
    expect(phoneError('')).toBeNull()
  })

  it.each([
    '091234567',
    '09123456789',
    '1912345678',
    '091234567a',
    ' 0912345678',
  ])('báo lỗi với %j', (value) => {
    expect(phoneError(value)).toBe(PHONE_ERROR)
  })
})

describe('canSubmit', () => {
  it('mở nút khi số điện thoại đúng và mật khẩu không trống', () => {
    expect(canSubmit('0912345678', 'a')).toBe(true)
  })

  it('khóa nút khi mật khẩu trống', () => {
    expect(canSubmit('0912345678', '')).toBe(false)
  })

  it('khóa nút khi số điện thoại sai định dạng hoặc trống', () => {
    expect(canSubmit('12345', 'a')).toBe(false)
    expect(canSubmit('', 'a')).toBe(false)
  })

  it('không bắt mật khẩu theo BR-TK-09 khi đăng nhập', () => {
    expect(canSubmit('0912345678', 'a')).toBe(true)
  })
})
