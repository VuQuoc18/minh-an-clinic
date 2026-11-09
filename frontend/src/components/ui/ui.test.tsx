import { render, screen } from '@testing-library/react'
import { createRef } from 'react'
import { describe, expect, it } from 'vitest'
import { cn } from '../../lib/cn'
import { Alert, AlertDescription, AlertTitle } from './alert'
import { Badge } from './badge'
import { Button } from './button'
import { Card, CardContent, CardTitle } from './card'
import { Field, FieldError, FieldHint, Fieldset } from './field'
import { Input } from './input'
import { Label, LabelOptional, LabelRequired } from './label'
import { NativeSelect } from './native-select'
import { Radio, RadioGroup } from './radio'

describe('cn', () => {
  it('ghép class và bỏ giá trị falsy', () => {
    expect(cn('a', false, undefined, null, 'b')).toBe('a b')
  })
})

describe('Button', () => {
  it('có class ds-button và type=button mặc định', () => {
    render(<Button>Lưu</Button>)
    const button = screen.getByRole('button', { name: 'Lưu' })
    expect(button).toHaveClass('ds-button')
    expect(button).toHaveAttribute('type', 'button')
  })

  it('áp class theo variant và size', () => {
    render(
      <Button variant="outline" size="sm">
        Hủy
      </Button>,
    )
    expect(screen.getByRole('button', { name: 'Hủy' })).toHaveClass(
      'ds-button',
      'ds-button--outline',
      'ds-button--sm',
    )
  })

  it('cho phép đổi type và giữ className truyền vào', () => {
    render(
      <Button type="submit" className="extra">
        Gửi
      </Button>,
    )
    const button = screen.getByRole('button', { name: 'Gửi' })
    expect(button).toHaveAttribute('type', 'submit')
    expect(button).toHaveClass('extra')
  })

  it('asChild render thành thẻ con, không thêm type', () => {
    render(
      <Button asChild>
        <a href="/x">Đi</a>
      </Button>,
    )
    const link = screen.getByRole('link', { name: 'Đi' })
    expect(link).toHaveClass('ds-button')
    expect(link).not.toHaveAttribute('type')
  })

  it('nút disabled không bấm được', () => {
    render(<Button disabled>Khóa</Button>)
    expect(screen.getByRole('button', { name: 'Khóa' })).toBeDisabled()
  })
})

describe('Card', () => {
  it('render div ds-card mặc định cùng các phần con', () => {
    render(
      <Card data-testid="card">
        <CardTitle>Tiêu đề</CardTitle>
        <CardContent>Nội dung</CardContent>
      </Card>,
    )
    expect(screen.getByTestId('card').tagName).toBe('DIV')
    expect(screen.getByTestId('card')).toHaveClass('ds-card')
    expect(screen.getByRole('heading', { name: 'Tiêu đề' })).toHaveClass(
      'ds-card-title',
    )
    expect(screen.getByText('Nội dung')).toHaveClass('ds-card-content')
  })

  it('asChild render thành section nhưng vẫn có class ds-card', () => {
    render(
      <Card asChild>
        <section aria-label="Vùng">x</section>
      </Card>,
    )
    const section = screen.getByRole('region', { name: 'Vùng' })
    expect(section).toHaveClass('ds-card')
  })
})

describe('Alert và Badge', () => {
  it('Alert áp variant và giữ role', () => {
    render(
      <Alert variant="destructive" role="alert">
        <AlertTitle>Lỗi</AlertTitle>
        <AlertDescription>Chi tiết</AlertDescription>
      </Alert>,
    )
    expect(screen.getByRole('alert')).toHaveClass(
      'ds-alert',
      'ds-alert--destructive',
    )
    expect(screen.getByText('Lỗi')).toHaveClass('ds-alert-title')
    expect(screen.getByText('Chi tiết')).toBeInTheDocument()
  })

  it('Alert mặc định không có hậu tố variant', () => {
    render(<Alert role="status">Tin</Alert>)
    expect(screen.getByRole('status').className).toBe('ds-alert')
  })

  it('Badge áp variant', () => {
    render(<Badge variant="warning">Chờ</Badge>)
    expect(screen.getByText('Chờ')).toHaveClass('ds-badge', 'ds-badge--warning')
  })
})

describe('Form controls', () => {
  it('Input chuyển ref và áp ds-input', () => {
    const ref = createRef<HTMLInputElement>()
    render(<Input ref={ref} aria-label="Tên" />)
    expect(screen.getByLabelText('Tên')).toHaveClass('ds-input')
    expect(ref.current).toBe(screen.getByLabelText('Tên'))
  })

  it('NativeSelect áp ds-select', () => {
    render(
      <NativeSelect aria-label="Chọn">
        <option value="">-</option>
      </NativeSelect>,
    )
    expect(screen.getByRole('combobox', { name: 'Chọn' })).toHaveClass(
      'ds-select',
    )
  })

  it('Label kèm chú thích bắt buộc và không bắt buộc mặc định', () => {
    render(
      <>
        <Label htmlFor="a">
          A <LabelRequired />
        </Label>
        <Label htmlFor="b">
          B <LabelOptional />
        </Label>
      </>,
    )
    expect(screen.getByText('Bắt buộc')).toHaveClass('ds-label-required')
    expect(screen.getByText('(Không bắt buộc)')).toHaveClass(
      'ds-label-optional',
    )
  })

  it('Field, FieldHint, FieldError, Fieldset áp đúng class', () => {
    render(
      <Field data-testid="f">
        <FieldHint>Gợi ý</FieldHint>
        <FieldError>Sai</FieldError>
        <Fieldset aria-label="Nhóm" />
      </Field>,
    )
    expect(screen.getByTestId('f')).toHaveClass('ds-field')
    expect(screen.getByText('Gợi ý')).toHaveClass('ds-field-hint')
    expect(screen.getByText('Sai')).toHaveClass('ds-field-error')
    expect(screen.getByRole('group', { name: 'Nhóm' })).toHaveClass(
      'ds-fieldset',
    )
  })

  it('Radio bọc nhãn và RadioGroup inline có class phụ', () => {
    render(
      <RadioGroup inline aria-label="Giới tính">
        <Radio name="g" value="Nam">
          Nam
        </Radio>
      </RadioGroup>,
    )
    expect(screen.getByRole('radiogroup', { name: 'Giới tính' })).toHaveClass(
      'ds-radio-group',
      'ds-radio-group--inline',
    )
    expect(screen.getByRole('radio', { name: 'Nam' })).toBeInTheDocument()
  })

  it('RadioGroup không inline thì không có class phụ', () => {
    render(<RadioGroup aria-label="Nhóm" />)
    expect(screen.getByRole('radiogroup')).not.toHaveClass(
      'ds-radio-group--inline',
    )
  })
})
