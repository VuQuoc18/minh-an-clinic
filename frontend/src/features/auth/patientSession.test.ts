import {
  getPatientToken,
  PATIENT_TOKEN_KEY,
  setPatientToken,
} from './patientSession'

beforeEach(() => {
  sessionStorage.clear()
  setPatientToken(null)
})
afterEach(() => vi.restoreAllMocks())

describe('patientSession', () => {
  it('lưu và đọc token qua sessionStorage', () => {
    setPatientToken('tok-1')

    expect(sessionStorage.getItem(PATIENT_TOKEN_KEY)).toBe('tok-1')
    expect(getPatientToken()).toBe('tok-1')
  })

  it('xóa token khi đặt null', () => {
    setPatientToken('tok-1')
    setPatientToken(null)

    expect(getPatientToken()).toBeNull()
    expect(sessionStorage.getItem(PATIENT_TOKEN_KEY)).toBeNull()
  })

  it('không đụng tới token nhân viên', () => {
    sessionStorage.setItem('staff_token', 'staff')
    setPatientToken('tok-1')

    expect(sessionStorage.getItem('staff_token')).toBe('staff')
  })

  it('vẫn đọc được token khi sessionStorage bị chặn', () => {
    const blocked = () => {
      throw new DOMException('blocked', 'SecurityError')
    }
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(blocked)
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(blocked)
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(blocked)

    setPatientToken('tok-mem')

    expect(getPatientToken()).toBe('tok-mem')
    setPatientToken(null)
    expect(getPatientToken()).toBeNull()
  })
})
