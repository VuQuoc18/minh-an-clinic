import type { HTMLAttributes, LabelHTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

export function Label({
  className,
  ...props
}: LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className={cn('ds-label', className)} {...props} />
}

/** Chú thích "Bắt buộc" cạnh nhãn. */
export function LabelRequired({
  className,
  children = 'Bắt buộc',
  ...props
}: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span className={cn('ds-label-required', className)} {...props}>
      {children}
    </span>
  )
}

export function LabelOptional({
  className,
  children = '(Không bắt buộc)',
  ...props
}: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span className={cn('ds-label-optional', className)} {...props}>
      {children}
    </span>
  )
}
