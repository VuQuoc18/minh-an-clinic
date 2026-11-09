import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Field, FieldError, Fieldset } from '../../components/ui/field'
import { Input } from '../../components/ui/input'
import { Label, LabelOptional, LabelRequired } from '../../components/ui/label'
import { Radio, RadioGroup } from '../../components/ui/radio'
import {
  newProfileSchema,
  type NewProfileForm as FormValues,
} from './profileSchema'
import type { NewProfile } from './types'

interface Props {
  initialPhone: string
  onChange: (profile: NewProfile | null) => void
}

type FieldName = keyof FormValues

const REQUIRED: Record<FieldName, boolean> = {
  full_name: true,
  birth_date: true,
  gender: true,
  phone: true,
  email: false,
  address: false,
}

export function toNewProfile(values: FormValues): NewProfile {
  return {
    full_name: values.full_name,
    birth_date: values.birth_date,
    gender: values.gender,
    phone: values.phone,
    ...(values.email ? { email: values.email } : {}),
    ...(values.address ? { address: values.address } : {}),
  }
}

/** Form hồ sơ mới của khách vãng lai. Báo hồ sơ hợp lệ lên cha mỗi khi nhập thay đổi. */
export function NewProfileForm({ initialPhone, onChange }: Props) {
  const {
    register,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(newProfileSchema),
    mode: 'onBlur',
    defaultValues: { phone: initialPhone, email: '', address: '' },
  })

  const sync = (form: HTMLFormElement) => {
    const data = Object.fromEntries(new FormData(form).entries()) as Record<
      string,
      string
    >
    const parsed = newProfileSchema.safeParse(data)
    onChange(parsed.success ? toNewProfile(parsed.data) : null)
  }

  const field = (
    name: FieldName,
    label: string,
    input: 'text' | 'date' | 'tel' | 'email',
  ) => {
    const error = errors[name]?.message
    const errorId = `${name}-error`
    return (
      <Field key={name}>
        <Label htmlFor={`np-${name}`}>
          {label} {REQUIRED[name] ? <LabelRequired /> : <LabelOptional />}
        </Label>
        <Input
          id={`np-${name}`}
          type={input}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error ? errorId : undefined}
          {...register(name)}
        />
        {error && <FieldError id={errorId}>{error}</FieldError>}
      </Field>
    )
  }

  const genderError = errors.gender?.message
  return (
    <form
      className="flex flex-col gap-4"
      aria-label="Hồ sơ khách mới"
      noValidate
      onChange={(event) => sync(event.currentTarget)}
      onSubmit={(event) => event.preventDefault()}
    >
      {field('full_name', 'Họ tên', 'text')}
      {field('birth_date', 'Ngày sinh', 'date')}
      <Fieldset>
        <legend className="ds-label">
          Giới tính <LabelRequired />
        </legend>
        <RadioGroup inline>
          <Radio value="Nam" {...register('gender')}>
            Nam
          </Radio>
          <Radio value="Nữ" {...register('gender')}>
            Nữ
          </Radio>
        </RadioGroup>
        {genderError && (
          <FieldError id="gender-error">{genderError}</FieldError>
        )}
      </Fieldset>
      {field('phone', 'Số điện thoại', 'tel')}
      {field('email', 'Email', 'email')}
      {field('address', 'Địa chỉ', 'text')}
    </form>
  )
}
