import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from '@/app/App'
import { AppProviders } from '@/app/providers'
import { installDevToken } from '@/lib/devAuth'
import '@/styles/design-system.css'

installDevToken(import.meta.env.VITE_DEV_STAFF_TOKEN, import.meta.env.DEV)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </StrictMode>,
)
