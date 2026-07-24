import { render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import App from './App'

import { useHealthQuery } from '../features/health/useHealthQuery'
import { AuthContext, type AuthContextValue } from '../features/auth/AuthContext'
import { renderWithQueryClient } from '../test/renderWithQueryClient'

vi.mock('../features/health/useHealthQuery', () => ({
  useHealthQuery: vi.fn(),
}))

vi.mock('../features/dashboard/DashboardPage', () => ({
  DashboardPage: () => <div>Dashboard inicial mock</div>,
}))

vi.mock('../features/grupos/GruposPage', () => ({
  GruposPage: () => <><h1>Grupos</h1><p>Grupos accesibles mock</p></>,
}))

vi.mock('../features/grupos/GrupoDetailPage', () => ({
  GrupoDetailPage: () => <><h1>Grupo detalle</h1><p>Estructura visible mock</p></>,
}))

const authUser = {
  id: 1,
  username: 'responsable1',
  email: 'resp1@scouts.cl',
  first_name: 'Ana',
  last_name: 'Rojas',
  is_staff: false,
  is_superuser: false,
  persona_id: null,
  responsable_grupo_ids: [],
  unidad_roles: [],
  is_apoderado: false,
}

const adminUser = {
  ...authUser,
  is_staff: true,
  persona_id: 10,
}

function authValue(overrides: Partial<AuthContextValue> = {}): AuthContextValue {
  return {
    status: 'anonymous',
    user: null,
    isAuthenticated: false,
    login: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  }
}

function withAuth(ui: ReactNode, value = authValue()) {
  return <AuthContext.Provider value={value}>{ui}</AuthContext.Provider>
}

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

    render(
      <MemoryRouter initialEntries={['/health']}>
        <App />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: 'SCOUTS-GESTOR' })).toBeInTheDocument()
  })

  it('renders login page by default route', () => {
    renderWithQueryClient(
      withAuth(
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>,
      ),
    )

    expect(screen.getByRole('heading', { name: /ingresa/i })).toBeInTheDocument()
  })

  it('redirects session started route to authenticated app shell', () => {
    render(
      withAuth(
        <MemoryRouter initialEntries={['/sesion-iniciada']}>
          <App />
        </MemoryRouter>,
        authValue({ status: 'authenticated', user: authUser, isAuthenticated: true }),
      ),
    )

    expect(screen.getByRole('link', { name: 'We Lemu inicio' })).toBeInTheDocument()
    expect(screen.getByText('Dashboard inicial mock')).toBeInTheDocument()
  })

  it('renders dashboard route for authenticated users', () => {
    render(
      withAuth(
        <MemoryRouter initialEntries={['/app']}>
          <App />
        </MemoryRouter>,
        authValue({ status: 'authenticated', user: adminUser, isAuthenticated: true }),
      ),
    )

    expect(screen.getByText('Dashboard inicial mock')).toBeInTheDocument()
    expect(screen.getByLabelText('Navegacion principal')).toBeInTheDocument()
  })

  it('redirects anonymous app access to login', () => {
    renderWithQueryClient(
      withAuth(
        <MemoryRouter initialEntries={['/app']}>
          <App />
        </MemoryRouter>,
      ),
    )

    expect(screen.getByRole('heading', { name: /ingresa/i })).toBeInTheDocument()
  })

  it.each([
    ['/app/personas', 'Personas', /listados de personas se conectaran proximamente/i],
    ['/app/unidades', 'Unidades', /estructura de unidades se conectara proximamente/i],
    ['/app/formacion', 'Formacion', /modulo de formacion estara disponible proximamente/i],
    ['/app/perfil', 'Mi perfil', /informacion del usuario autenticado/i],
  ])('renders protected placeholder route %s', (path, heading, text) => {
    render(
      withAuth(
        <MemoryRouter initialEntries={[path]}>
          <App />
        </MemoryRouter>,
        authValue({ status: 'authenticated', user: adminUser, isAuthenticated: true }),
      ),
    )

    expect(screen.getByRole('heading', { name: heading })).toBeInTheDocument()
    expect(screen.getByText(text)).toBeInTheDocument()
    expect(screen.getByLabelText('Navegacion principal')).toBeInTheDocument()
  })

  it('shows forbidden UX for direct access to hidden visual routes', () => {
    render(
      withAuth(
        <MemoryRouter initialEntries={['/app/grupos']}>
          <App />
        </MemoryRouter>,
        authValue({ status: 'authenticated', user: authUser, isAuthenticated: true }),
      ),
    )

    expect(screen.getByRole('heading', { name: '403' })).toBeInTheDocument()
  })

  it('renders forbidden page', () => {
    render(
      withAuth(
        <MemoryRouter initialEntries={['/403']}>
          <App />
        </MemoryRouter>,
      ),
    )

    expect(screen.getByRole('heading', { name: '403' })).toBeInTheDocument()
    expect(screen.getByText(/no tienes permisos/i)).toBeInTheDocument()
  })

  it('renders not found page for unknown routes', () => {
    render(
      withAuth(
        <MemoryRouter initialEntries={['/ruta-inexistente']}>
          <App />
        </MemoryRouter>,
      ),
    )

    expect(screen.getByRole('heading', { name: '404' })).toBeInTheDocument()
    expect(screen.getByText(/no existe o fue movida/i)).toBeInTheDocument()
  })

  it('shows loading state while health query is pending', () => {
    vi.mocked(useHealthQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
    } as unknown as ReturnType<typeof useHealthQuery>)

    render(
      <MemoryRouter initialEntries={['/health']}>
        <App />
      </MemoryRouter>,
    )

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

    render(
      <MemoryRouter initialEntries={['/health']}>
        <App />
      </MemoryRouter>,
    )

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

    render(
      <MemoryRouter initialEntries={['/health']}>
        <App />
      </MemoryRouter>,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('No fue posible completar la solicitud')
  })
})
