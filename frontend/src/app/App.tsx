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
import { AdultoDetailPage, ApoderadoDetailPage, BeneficiarioDetailPage, OwnPersonaPage, PersonaDetailPage } from '../features/personas/PersonaDetailPages'
import { AdultosPage, ApoderadosPage, BeneficiariosPage, PersonasPage } from '../features/personas/PersonasPages'
import { AsignacionFormPage, BeneficiarioFormPage, CertificadoFormPage, PersonaFormPage } from '../features/personas/PersonaForms'
import { ProgresionFormPage, ProgresionesPage } from '../features/personas/ProgresionPages'
import { PlaceholderPage } from '../features/placeholders/PlaceholderPage'
import { UnidadDetailPage } from '../features/unidades/UnidadDetailPage'
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
        <Route path="adultos/:adultoId" element={<AdultoDetailPage />} />
        <Route path="adultos/:adultoId/certificado" element={<CertificadoFormPage />} />
        <Route path="beneficiarios" element={<BeneficiariosPage />} />
        <Route path="beneficiarios/:beneficiarioId" element={<BeneficiarioDetailPage />} />
        <Route path="beneficiarios/:beneficiarioId/editar" element={<BeneficiarioFormPage />} />
        <Route path="beneficiarios/:beneficiarioId/asignacion" element={<AsignacionFormPage />} />
        <Route path="beneficiarios/:beneficiarioId/progresiones" element={<ProgresionesPage />} />
        <Route path="beneficiarios/:beneficiarioId/progresiones/nuevo" element={<ProgresionFormPage />} />
        <Route path="beneficiarios/:beneficiarioId/progresiones/:progresionId/editar" element={<ProgresionFormPage />} />
        <Route path="apoderados" element={<ApoderadosPage />} />
        <Route path="apoderados/:apoderadoId" element={<ApoderadoDetailPage />} />
        <Route path=":personaId" element={<PersonaDetailPage />} />
        <Route path=":personaId/editar" element={<PersonaFormPage />} />
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
      <Route path="/app/perfil/editar" element={<RequireAuth><AppPage navItemId="perfil"><PersonaFormPage /></AppPage></RequireAuth>} />
      <Route
        path="/app/unidades/:unidadId"
        element={(
          <RequireAuth>
            <AppPage navItemId="unidades">
              <UnidadDetailPage />
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
              <OwnPersonaPage />
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
