import { Slot } from '@radix-ui/react-slot'
import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

type DivProps = HTMLAttributes<HTMLDivElement>

/** Dùng `asChild` để render thành thẻ khác (section, form...) mà vẫn giữ class của card. */
export function Card({
  className,
  asChild = false,
  ...props
}: DivProps & { asChild?: boolean }) {
  const Comp = asChild ? Slot : 'div'
  return <Comp className={cn('ds-card', className)} {...props} />
}

export function CardHeader({ className, ...props }: DivProps) {
  return <div className={cn('ds-card-header', className)} {...props} />
}

export function CardTitle({
  className,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={cn('ds-card-title', className)} {...props} />
}

export function CardDescription({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('ds-card-description', className)} {...props} />
}

export function CardContent({ className, ...props }: DivProps) {
  return <div className={cn('ds-card-content', className)} {...props} />
}

export function CardFooter({ className, ...props }: DivProps) {
  return <div className={cn('ds-card-footer', className)} {...props} />
}
