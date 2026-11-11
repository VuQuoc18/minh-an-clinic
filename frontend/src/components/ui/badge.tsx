import { cva, type VariantProps } from 'class-variance-authority'
import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

export const badgeVariants = cva('ds-badge', {
  variants: {
    variant: {
      default: '',
      secondary: 'ds-badge--secondary',
      outline: 'ds-badge--outline',
      success: 'ds-badge--success',
      warning: 'ds-badge--warning',
      destructive: 'ds-badge--destructive',
      info: 'ds-badge--info',
    },
  },
  defaultVariants: { variant: 'default' },
})

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}
