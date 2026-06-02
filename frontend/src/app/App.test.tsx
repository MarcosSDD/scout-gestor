import { render, screen } from '@testing-library/react'
import App from './App'

import { useHealthQuery } from '../features/health/useHealthQuery'

vi.mock('../features/health/useHealthQuery', () => ({
  useHealthQuery: vi.fn(),
}))

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders app heading', () => {
    vi.mocked(useHealthQuery).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
      error: null,
    } as unknown as ReturnType<typeof useHealthQuery>)

    render(<App />)

    expect(screen.getByRole('heading', { name: 'SCOUTS-GESTOR' })).toBeInTheDocument()
  })

  it('shows loading state while health query is pending', () => {
    vi.mocked(useHealthQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
    } as unknown as ReturnType<typeof useHealthQuery>)

    render(<App />)

    expect(screen.getByRole('status')).toHaveTextContent('Conectando con API...')
  })

  it('shows success data when health query resolves', () => {
    vi.mocked(useHealthQuery).mockReturnValue({
      data: {
        success: true,
        message: 'API healthy',
        data: { status: 'ok', version: 'v1' },
      },
      isLoading: false,
      isError: false,
      error: null,
    } as unknown as ReturnType<typeof useHealthQuery>)

    render(<App />)

    expect(screen.getByText('API ok - v1')).toBeInTheDocument()
  })

  it('shows normalized error message when health query fails', () => {
    vi.mocked(useHealthQuery).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: {
        error: {
          message: 'No fue posible completar la solicitud',
        },
      },
    } as unknown as ReturnType<typeof useHealthQuery>)

    render(<App />)

    expect(screen.getByRole('alert')).toHaveTextContent('No fue posible completar la solicitud')
  })
})
