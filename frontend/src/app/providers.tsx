import { QueryClientProvider } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { createQueryClient } from './queryClient'

/** Các provider dùng chung cho toàn ứng dụng: bắt lỗi màn hình, bộ nhớ đệm truy vấn, định tuyến. */
export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createQueryClient)
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter basename={import.meta.env.BASE_URL}>
          {children}
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
