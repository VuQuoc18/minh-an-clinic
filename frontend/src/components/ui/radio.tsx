import type { HTMLAttributes, InputHTMLAttributes, Ref } from 'react'
import { cn } from '../../lib/cn'

export function RadioGroup({
  className,
  inline = false,
  ...props
}: HTMLAttributes<HTMLDivElement> & { inline?: boolean }) {
  return (
    <div
      role="radiogroup"
      className={cn(
        'ds-radio-group',
        inline && 'ds-radio-group--inline',
        className,
      )}
      {...props}
    />
  )
}

export interface RadioProps extends Omit<
  InputHTMLAttributes<HTMLInputElement>,
  'type'
> {
  ref?: Ref<HTMLInputElement>
}

/** Radio gốc có nhãn bao ngoài. Gắn `{...register('field')}` của react-hook-form trực tiếp được. */
export function Radio({ className, children, ref, ...props }: RadioProps) {
  return (
    <label className={cn('ds-radio', className)}>
      <input ref={ref} type="radio" {...props} /> {children}
    </label>
  )
}
