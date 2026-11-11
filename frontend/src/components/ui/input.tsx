import type { InputHTMLAttributes, Ref } from 'react'
import { cn } from '../../lib/cn'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  ref?: Ref<HTMLInputElement>
}

export function Input({ className, ref, ...props }: InputProps) {
  return <input ref={ref} className={cn('ds-input', className)} {...props} />
}
