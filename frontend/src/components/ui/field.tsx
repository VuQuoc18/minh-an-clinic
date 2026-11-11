import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

type DivProps = HTMLAttributes<HTMLDivElement>

export function Field({ className, ...props }: DivProps) {
  return <div className={cn('ds-field', className)} {...props} />
}

export function FieldHint({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('ds-field-hint', className)} {...props} />
}

export function FieldError({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('ds-field-error', className)} {...props} />
}

export function Fieldset({
  className,
  ...props
}: HTMLAttributes<HTMLFieldSetElement>) {
  return <fieldset className={cn('ds-fieldset', className)} {...props} />
}
