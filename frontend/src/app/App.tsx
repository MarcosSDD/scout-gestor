import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '../app-shell/AppShell'
import { LoginPage } from '../features/auth/LoginPage'
import { RequireAuth } from '../features/auth/RequireAuth'
import { ForbiddenPage } from '../features/errors/ForbiddenPage'
import { NotFoundPage } from '../features/errors/NotFoundPage'
import { HomePage } from '../features/home/HomePage'
import { HealthPage } from '../features/health/HealthPage'

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
            <AppShell>
              <HomePage />
            </AppShell>
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
