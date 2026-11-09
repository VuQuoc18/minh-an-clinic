import type { Ref, SelectHTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

export interface NativeSelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  ref?: Ref<HTMLSelectElement>
}

/** `<select>` gốc của trình duyệt với style `ds-select`. Tốt cho bàn phím và trình đọc màn hình. */
export function NativeSelect({ className, ref, ...props }: NativeSelectProps) {
  return <select ref={ref} className={cn('ds-select', className)} {...props} />
}
