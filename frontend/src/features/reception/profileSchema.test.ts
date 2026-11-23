import { newProfileSchema, todayIso } from './profileSchema'

const VALID = {
  full_name: 'Nguyễn Văn Khách',
  birth_date: '1992-03-15',
  gender: 'Nam',
  phone: '0977000111',
  email: '',
  address: '',
}

function messages(input: Record<string, unknown>): string[] {
  const result = newProfileSchema.safeParse(input)
  return result.success ? [] : result.error.issues.map((i) => i.message)
}

describe('todayIso', () => {
  it('định dạng ngày theo yyyy-mm-dd có số 0 đứng đầu', () => {
    expect(todayIso(new Date(2026, 0, 5))).toBe('2026-01-05')
  })
})

describe('newProfileSchema', () => {
  it('chấp nhận hồ sơ hợp lệ, email và địa chỉ có thể để trống', () => {
    expect(newProfileSchema.safeParse(VALID).success).toBe(true)
  })

  it('cắt khoảng trắng đầu cuối của họ tên', () => {
    const result = newProfileSchema.parse({
      ...VALID,
      full_name: '  An Bình  ',
    })

    expect(result.full_name).toBe('An Bình')
  })

  it('từ chối họ tên ngắn hơn 2 ký tự và chấp nhận đúng 2 ký tự', () => {
    expect(messages({ ...VALID, full_name: 'A' })).toContain(
      'Họ tên dài từ 2 đến 100 ký tự.',
    )
    expect(messages({ ...VALID, full_name: 'An' })).toEqual([])
  })

  it('từ chối họ tên dài hơn 100 ký tự và chấp nhận đúng 100 ký tự', () => {
    expect(messages({ ...VALID, full_name: 'a'.repeat(101) })).toContain(
      'Họ tên dài từ 2 đến 100 ký tự.',
    )
    expect(messages({ ...VALID, full_name: 'a'.repeat(100) })).toEqual([])
  })

  it('từ chối họ tên có chữ số hoặc ký tự đặc biệt', () => {
    expect(messages({ ...VALID, full_name: 'An 2' })).toContain(
      'Họ tên chỉ gồm chữ cái và khoảng trắng.',
    )
    expect(messages({ ...VALID, full_name: 'An-Bình' })).toContain(
      'Họ tên chỉ gồm chữ cái và khoảng trắng.',
    )
  })

  it('từ chối ngày sinh để trống', () => {
    expect(messages({ ...VALID, birth_date: '' })).toContain('Nhập ngày sinh.')
  })

  it('từ chối ngày sinh trước 01/01/1900 và chấp nhận đúng ngày đó', () => {
    expect(messages({ ...VALID, birth_date: '1899-12-31' })).toContain(
      'Ngày sinh không được trước 01/01/1900.',
    )
    expect(messages({ ...VALID, birth_date: '1900-01-01' })).toEqual([])
  })

  it('từ chối ngày sinh sau hôm nay và chấp nhận đúng hôm nay', () => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)

    expect(messages({ ...VALID, birth_date: todayIso(tomorrow) })).toContain(
      'Ngày sinh không được sau ngày hôm nay.',
    )
    expect(messages({ ...VALID, birth_date: todayIso() })).toEqual([])
  })

  it('từ chối giới tính chưa chọn hoặc ngoài Nam/Nữ', () => {
    expect(messages({ ...VALID, gender: undefined })).toContain(
      'Chọn giới tính.',
    )
    expect(messages({ ...VALID, gender: 'Khác' })).toContain('Chọn giới tính.')
  })

  it.each(['012345678', '01234567890', '1234567890', '09123abc78', ''])(
    'từ chối số điện thoại sai định dạng %j',
    (phone) => {
      expect(messages({ ...VALID, phone })).toContain(
        'Số điện thoại gồm 10 chữ số và bắt đầu bằng 0.',
      )
    },
  )

  it('từ chối email sai định dạng và chấp nhận email đúng', () => {
    expect(messages({ ...VALID, email: 'abc' })).toContain(
      'Email không đúng định dạng.',
    )
    expect(messages({ ...VALID, email: 'a@b.vn' })).toEqual([])
  })

  it('từ chối địa chỉ dài hơn 255 ký tự và chấp nhận đúng 255 ký tự', () => {
    expect(messages({ ...VALID, address: 'a'.repeat(256) })).toContain(
      'Địa chỉ tối đa 255 ký tự.',
    )
    expect(messages({ ...VALID, address: 'a'.repeat(255) })).toEqual([])
  })
})
