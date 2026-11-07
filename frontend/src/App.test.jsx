import { render, screen } from '@testing-library/react'
import App from './App.jsx'

describe('App', () => {
  it('hiển thị tiêu đề phòng khám', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: 'Phòng khám Minh An' }),
    ).toBeInTheDocument()
  })
})
