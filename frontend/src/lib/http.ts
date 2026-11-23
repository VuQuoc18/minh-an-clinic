// Gọi API theo đường dẫn tương đối với `import.meta.env.BASE_URL` (`<base>api`). Token nhân viên lấy từ tokenStore (đăng nhập thật làm ở FR-TK-04).

import { getToken } from './tokenStore'

export { TOKEN_KEY } from './tokenStore'
const BASE_URL = `${import.meta.env.BASE_URL}api`
const GENERIC_ERROR = 'Không thực hiện được. Vui lòng thử lại.'

export interface FieldError {
  field: string
  message: string
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  /** Lỗi từng trường khi máy chủ trả 422 VALIDATION_ERROR; rỗng với lỗi khác. */
  readonly fieldErrors: FieldError[]

  constructor(
    status: number,
    code: string,
    message: string,
    fieldErrors: FieldError[] = [],
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fieldErrors = fieldErrors
  }
}

type Params = Record<string, string | number | undefined | null>

export function buildQuery(params?: Params): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value))
    }
  }
  const text = search.toString()
  return text ? `?${text}` : ''
}

interface ErrorDetail {
  code?: string
  message?: string
  errors?: FieldError[]
}

function isErrorDetail(value: unknown): value is ErrorDetail {
  return typeof value === 'object' && value !== null && 'message' in value
}

// Máy chủ trả lỗi dạng {"detail": {"code", "message", "errors"?}} (xem backend app/core/errors.py).
async function toApiError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as { detail?: unknown }
    if (isErrorDetail(body.detail)) {
      const { code, message, errors } = body.detail
      return new ApiError(
        response.status,
        code ?? 'UNKNOWN',
        message ?? GENERIC_ERROR,
        Array.isArray(errors) ? errors : [],
      )
    }
  } catch {
    // Thân phản hồi không phải JSON: dùng thông báo chung.
  }
  return new ApiError(response.status, 'UNKNOWN', GENERIC_ERROR)
}

export async function apiRequest<T>(
  method: 'GET' | 'POST',
  path: string,
  options: { params?: Params; body?: unknown } = {},
): Promise<T> {
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'

  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}${buildQuery(options.params)}`, {
      method,
      headers,
      body:
        options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch {
    throw new ApiError(
      0,
      'NETWORK_ERROR',
      'Không kết nối được máy chủ. Vui lòng thử lại.',
    )
  }
  if (!response.ok) throw await toApiError(response)
  return (await response.json()) as T
}
