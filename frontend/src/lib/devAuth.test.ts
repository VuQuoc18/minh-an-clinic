import { installDevToken } from './devAuth'
import { TOKEN_KEY } from './http'
import { getToken } from './tokenStore'

beforeEach(() => sessionStorage.clear())

describe('installDevToken', () => {
  it('stores the token in dev mode when one is configured', () => {
    expect(installDevToken('dev-token', true)).toBe(true)
    expect(sessionStorage.getItem(TOKEN_KEY)).toBe('dev-token')
  })

  it('does nothing when the build is not a dev build', () => {
    expect(installDevToken('dev-token', false)).toBe(false)
    expect(sessionStorage.getItem(TOKEN_KEY)).toBeNull()
  })

  it('does nothing when no token is configured', () => {
    expect(installDevToken(undefined, true)).toBe(false)
    expect(installDevToken('', true)).toBe(false)
    expect(sessionStorage.getItem(TOKEN_KEY)).toBeNull()
  })

  it('saves through the saver it is given', () => {
    const save = vi.fn()
    installDevToken('abc', true, save)
    expect(save).toHaveBeenCalledWith('abc')
  })

  it('keeps the token readable when sessionStorage is blocked', () => {
    const blocked = () => {
      throw new DOMException('blocked', 'SecurityError')
    }
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(blocked)
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(blocked)
    expect(installDevToken('dev-token', true)).toBe(true)
    expect(getToken()).toBe('dev-token')
    vi.restoreAllMocks()
  })
})
