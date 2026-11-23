import { useMutation } from '@tanstack/react-query'
import { useState, type SyntheticEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Field, FieldError } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Label, LabelRequired } from '@/components/ui/label'
import { ApiError } from '@/lib/http'
import { loginPatient } from './api'
import { canSubmit, phoneError } from './loginSchema'
import { setPatientToken } from './patientSession'
import {
  CREATE_PROFILE_PATH,
  MY_APPOINTMENTS_PATH,
  SET_PASSWORD_PATH,
} from './routes'
import type { LoginResult } from './types'

const GENERIC_ERROR = 'Không đăng nhập được. Vui lòng thử lại.'

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : GENERIC_ERROR
}

/** MH-TK-01 Đăng nhập bệnh nhân (SCR-005). */
export function LoginPage() {
  const navigate = useNavigate()
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const login = useMutation({
    mutationFn: loginPatient,
    onSuccess: (result: LoginResult) => {
      if (result.ket_qua === 'CHUA_CO_MAT_KHAU') {
        navigate(SET_PASSWORD_PATH, { state: { phone: result.so_dien_thoai } })
        return
      }
      setPatientToken(result.token)
      if (result.can_tao_ho_so) {
        navigate(CREATE_PROFILE_PATH, {
          state: { phone: result.so_dien_thoai },
        })
      } else {
        navigate(MY_APPOINTMENTS_PATH)
      }
    },
  })

  const phoneMessage = phoneError(phone)
  const submit = (event: SyntheticEvent) => {
    event.preventDefault()
    if (!canSubmit(phone, password) || login.isPending) return
    login.mutate({ so_dien_thoai: phone, mat_khau: password })
  }

  return (
    <main className="ds-kit-content">
      <header className="ds-kit-page-header">
        <h1 className="ds-text-title">Đăng nhập</h1>
      </header>

      <Card asChild>
        <form aria-label="Đăng nhập bệnh nhân" noValidate onSubmit={submit}>
          <CardContent className="flex flex-col gap-4">
            <Field>
              <Label htmlFor="lg-phone">
                Số điện thoại <LabelRequired />
              </Label>
              <Input
                id="lg-phone"
                type="tel"
                inputMode="numeric"
                autoComplete="username"
                maxLength={20}
                value={phone}
                aria-invalid={phoneMessage ? 'true' : undefined}
                aria-describedby={phoneMessage ? 'lg-phone-error' : undefined}
                onChange={(event) => setPhone(event.target.value)}
              />
              {phoneMessage && (
                <FieldError id="lg-phone-error">{phoneMessage}</FieldError>
              )}
            </Field>
            <Field>
              <Label htmlFor="lg-password">
                Mật khẩu <LabelRequired />
              </Label>
              <Input
                id="lg-password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
              <Button
                variant="ghost"
                size="sm"
                aria-pressed={showPassword}
                onClick={() => setShowPassword((shown) => !shown)}
              >
                {showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
              </Button>
            </Field>

            {login.isError && (
              <Alert variant="destructive" role="alert">
                <AlertDescription>{errorMessage(login.error)}</AlertDescription>
              </Alert>
            )}
          </CardContent>
          <CardFooter>
            <Link to={SET_PASSWORD_PATH} state={{ reset: true, phone }}>
              Quên mật khẩu
            </Link>
            <Button
              type="submit"
              disabled={!canSubmit(phone, password) || login.isPending}
            >
              Đăng nhập
            </Button>
          </CardFooter>
        </form>
      </Card>
    </main>
  )
}
