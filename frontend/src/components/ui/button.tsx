import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import type { ButtonHTMLAttributes, Ref } from 'react'
import { cn } from '../../lib/cn'

export const buttonVariants = cva('ds-button', {
  variants: {
    variant: {
      default: '',
      secondary: 'ds-button--secondary',
      outline: 'ds-button--outline',
      ghost: 'ds-button--ghost',
      destructive: 'ds-button--destructive',
    },
    size: {
      default: '',
      sm: 'ds-button--sm',
      lg: 'ds-button--lg',
      icon: 'ds-button--icon',
    },
  },
  defaultVariants: { variant: 'default', size: 'default' },
})

export interface ButtonProps
  extends
    ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  ref?: Ref<HTMLButtonElement>
}

/** Mặc định `type="button"` để không vô tình submit form. */
export function Button({
  className,
  variant,
  size,
  asChild = false,
  type = 'button',
  ref,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : 'button'
  return (
    <Comp
      ref={ref}
      type={asChild ? undefined : type}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  )
}
