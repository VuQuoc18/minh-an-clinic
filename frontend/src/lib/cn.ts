import { clsx, type ClassValue } from 'clsx'

/** Ghép class có điều kiện (theo kiểu shadcn). Không dùng Tailwind nên không cần tailwind-merge. */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs)
}
