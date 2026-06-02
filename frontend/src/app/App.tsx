import { useHealthQuery } from '../features/health/useHealthQuery'

function App() {
  const { data, isLoading, isError, error } = useHealthQuery()

  return (
    <main style={{ padding: '24px' }}>
      <h1>SCOUTS-GESTOR</h1>

      {isLoading && <p role="status">Conectndo con API...</p>}

      {isError && (
        <p role="alert">
          {(error as { error?: { message?: string } })?.error?.message ?? 'No fue posible conectar con la API'}
        </p>
      )}

      {data && (
        <p>
          API {data.data.status} - {data.data.version}
        </p>
      )}
    </main>
  )
}

export default App
