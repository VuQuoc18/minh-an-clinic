import { z } from 'zod'

// Quy tắc hồ sơ theo BR-TK-08; máy chủ kiểm tra lại các quy tắc này.
const MIN_BIRTH_DATE = '1900-01-01'

export function todayIso(now: Date = new Date()): string {
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

export const newProfileSchema = z.object({
  full_name: z
    .string()
    .trim()
    .min(2, 'Họ tên dài từ 2 đến 100 ký tự.')
    .max(100, 'Họ tên dài từ 2 đến 100 ký tự.')
    .refine(
      (value) => /^[\p{L} ]+$/u.test(value),
      'Họ tên chỉ gồm chữ cái và khoảng trắng.',
    ),
  birth_date: z
    .string()
    .min(1, 'Nhập ngày sinh.')
    .refine(
      (value) => value >= MIN_BIRTH_DATE,
      'Ngày sinh không được trước 01/01/1900.',
    )
    .refine(
      (value) => value <= todayIso(),
      'Ngày sinh không được sau ngày hôm nay.',
    ),
  gender: z.enum(['Nam', 'Nữ'], { error: 'Chọn giới tính.' }),
  phone: z
    .string()
    .regex(/^0[0-9]{9}$/, 'Số điện thoại gồm 10 chữ số và bắt đầu bằng 0.'),
  email: z
    .string()
    .trim()
    .max(254, 'Email không đúng định dạng.')
    .refine(
      (value) => value === '' || /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value),
      {
        message: 'Email không đúng định dạng.',
      },
    ),
  address: z.string().trim().max(255, 'Địa chỉ tối đa 255 ký tự.'),
})

export type NewProfileForm = z.infer<typeof newProfileSchema>
