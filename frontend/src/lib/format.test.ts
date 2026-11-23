import { formatDate, formatTime } from './format'

describe('formatDate', () => {
  it('đổi yyyy-mm-dd sang dd/mm/yyyy', () => {
    expect(formatDate('2026-11-09')).toBe('09/11/2026')
  })

  it('giữ nguyên giá trị sai định dạng', () => {
    expect(formatDate('09/11/2026')).toBe('09/11/2026')
    expect(formatDate('')).toBe('')
  })
})

describe('formatTime', () => {
  it('bỏ phần giây của giờ 24 giờ', () => {
    expect(formatTime('09:15:00')).toBe('09:15')
    expect(formatTime('23:45:30')).toBe('23:45')
  })

  it('giữ giờ HH:mm và giá trị sai định dạng', () => {
    expect(formatTime('08:05')).toBe('08:05')
    expect(formatTime('9h15')).toBe('9h15')
  })
})
