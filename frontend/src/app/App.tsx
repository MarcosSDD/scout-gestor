import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '../app-shell/AppShell'
import { canSeeNavItem, getNavItemById, type ShellNavItemId } from '../app-shell/navigation'
import { LoginPage } from '../features/auth/LoginPage'
import { RequireAuth } from '../features/auth/RequireAuth'
import { useAuth } from '../features/auth/useAuth'
import { DashboardPage } from '../features/dashboard/DashboardPage'
import { ForbiddenPage } from '../features/errors/ForbiddenPage'
import { NotFoundPage } from '../features/errors/NotFoundPage'
import { GrupoDetailPage } from '../features/grupos/GrupoDetailPage'
import { GruposPage } from '../features/grupos/GruposPage'
import { HealthPage } from '../features/health/HealthPage'
import { PersonasLayout } from '../features/personas/PersonasLayout'
import { AdultosPage, ApoderadosPage, BeneficiariosPage, PersonasPage } from '../features/personas/PersonasPages'
import { PlaceholderPage } from '../features/placeholders/PlaceholderPage'
import { ProfilePage } from '../features/placeholders/ProfilePage'
import { UnidadesPage } from '../features/unidades/UnidadesPage'

type AppPageProps = {
  navItemId: ShellNavItemId
  children: ReactNode
}

function AppPage({ navItemId, children }: AppPageProps) {
  const { user } = useAuth()
  const navItem = getNavItemById(navItemId)

  if (!navItem || !canSeeNavItem(user, navItem)) {
    return <ForbiddenPage />
  }

  return <AppShell>{children}</AppShell>
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/sesion-iniciada" element={<Navigate to="/app" replace />} />
      <Route
        path="/app"
        element={(
          <RequireAuth>
            <AppPage navItemId="dashboard">
              <DashboardPage />
            </AppPage>
          </RequireAuth>
        )}
      />
      <Route
        path="/app/grupos"
        element={(
          <RequireAuth>
            <AppPage navItemId="grupos">
              <GruposPage />
            </AppPage>
          </RequireAuth>
        )}
      />
      <Route
        path="/app/grupos/:grupoId"
        element={(
          <RequireAuth>
            <AppPage navItemId="grupos">
              <GrupoDetailPage />
            </AppPage>
          </RequireAuth>
        )}
      />
      <Route
        path="/app/personas"
        element={(
          <RequireAuth>
            <AppPage navItemId="personas">
              <PersonasLayout />
            </AppPage>
          </RequireAuth>
        )}
      >
        <Route index element={<PersonasPage />} />
        <Route path="adultos" element={<AdultosPage />} />
        <Route path="beneficiarios" element={<BeneficiariosPage />} />
        <Route path="apoderados" element={<ApoderadosPage />} />
      </Route>
      <Route
        path="/app/unidades"
        element={(
          <RequireAuth>
            <AppPage navItemId="unidades">
              <UnidadesPage />
            </AppPage>
          </RequireAuth>
        )}
      />
      <Route
        path="/app/formacion"
        element={(
          <RequireAuth>
            <AppPage navItemId="formacion">
              <PlaceholderPage title="Formacion" description="El modulo de formacion estara disponible proximamente." />
            </AppPage>
          </RequireAuth>
        )}
      />
      <Route
        path="/app/perfil"
        element={(
          <RequireAuth>
            <AppPage navItemId="perfil">
              <ProfilePage />
            </AppPage>
          </RequireAuth>
        )}
      />
      <Route path="/403" element={<ForbiddenPage />} />
      <Route path="/health" element={<HealthPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
