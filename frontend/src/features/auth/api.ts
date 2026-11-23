import { apiRequest } from '@/lib/http'
import type { LoginBody, LoginResult } from './types'

export const loginPatient = (body: LoginBody) =>
  apiRequest<LoginResult>('POST', '/auth/patient/login', { body })
