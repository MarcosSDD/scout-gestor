import { useHealthQuery } from './useHealthQuery'

export function HealthPage() {
  const { data, isLoading, isError, error } = useHealthQuery()

  return (
    <main className="health-page">
      <section className="session-card">
        <p className="eyebrow">Diagnostico</p>
        <h1>SCOUTS-GESTOR</h1>

        {isLoading && <p role="status">Conectando con API...</p>}

        {isError && (
          <p role="alert" className="form-error">
            {(error as { error?: { message?: string } })?.error?.message ?? 'No fue posible conectar con la API'}
          </p>
        )}

        {data && (
          <p>
            API {data.data.status} - {data.data.version}
          </p>
        )}
      </section>
    </main>
  )
}
