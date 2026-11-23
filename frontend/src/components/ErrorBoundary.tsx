import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Alert, AlertDescription, AlertTitle } from './ui/alert'
import { Button } from './ui/button'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/** Bắt lỗi khi vẽ giao diện để không hiện trang trắng; cho người dùng tải lại trang. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Lỗi giao diện', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <main className="ds-kit-content">
        <Alert variant="destructive">
          <AlertTitle>Đã có lỗi xảy ra</AlertTitle>
          <AlertDescription>
            Màn hình gặp sự cố ngoài ý muốn. Vui lòng tải lại trang.
          </AlertDescription>
        </Alert>
        <Button onClick={() => window.location.reload()}>Tải lại trang</Button>
      </main>
    )
  }
}
