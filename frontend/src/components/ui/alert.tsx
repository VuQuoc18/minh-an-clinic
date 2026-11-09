import { cva, type VariantProps } from 'class-variance-authority'
import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

export const alertVariants = cva('ds-alert', {
  variants: {
    variant: {
      default: '',
      info: 'ds-alert--info',
      success: 'ds-alert--success',
      warning: 'ds-alert--warning',
      destructive: 'ds-alert--destructive',
    },
  },
  defaultVariants: { variant: 'default' },
})

export interface AlertProps
  extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof alertVariants> {}

export function Alert({ className, variant, ...props }: AlertProps) {
  return (
    <div className={cn(alertVariants({ variant }), className)} {...props} />
  )
}

export function AlertTitle({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('ds-alert-title', className)} {...props} />
}

export function AlertDescription({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={className} {...props} />
}
