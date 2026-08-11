import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import type { PropsWithChildren } from 'react'
import { createUnidad, patchUnidad, reassignSubgrupoMiembro } from '../../api/unidadesApi'
import { useUnidadCommand } from './useStructuralQueries'

vi.mock('../../api/unidadesApi', async (importOriginal) => ({ ...(await importOriginal<typeof import('../../api/unidadesApi')>()), createUnidad: vi.fn(), patchUnidad: vi.fn(), reassignSubgrupoMiembro: vi.fn() }))

describe('structural mutations', () => {
  it('invalidates all affected read domains after a command', async () => {
    vi.mocked(createUnidad).mockResolvedValue({ success: true, message: 'OK', data: {} as never })
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } }); const invalidate = vi.spyOn(client, 'invalidateQueries')
    const wrapper = ({ children }: PropsWithChildren) => <QueryClientProvider client={client}>{children}</QueryClientProvider>
    const { result } = renderHook(() => useUnidadCommand(), { wrapper })
    await act(async () => { await result.current.mutateAsync({ values: { grupo: 1, rama: 2, nombre: 'Tropa', tipo_composicion: '', estado: 'ACTIVA', cupo_maximo: null } }) })
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['unidades'] })
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['personas'] })
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['grupos'] })
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['dashboard'] })
  })

  it('removes immutable unit context on patch and reassignment sends only destination', async () => {
    vi.mocked(patchUnidad).mockResolvedValue({ success: true, message: 'OK', data: {} as never })
    vi.mocked(reassignSubgrupoMiembro).mockResolvedValue({ success: true, message: 'OK', data: {} as never })
    const client = new QueryClient(); const wrapper = ({ children }: PropsWithChildren) => <QueryClientProvider client={client}>{children}</QueryClientProvider>
    const { result } = renderHook(() => useUnidadCommand(), { wrapper })
    await act(async () => { await result.current.mutateAsync({ id: 3, values: { grupo: 1, rama: 2, nombre: 'Nueva', tipo_composicion: '', estado: 'ACTIVA', cupo_maximo: null } }) })
    expect(patchUnidad).toHaveBeenCalledWith(3, { nombre: 'Nueva', tipo_composicion: '', estado: 'ACTIVA', cupo_maximo: null })
    await reassignSubgrupoMiembro(8, 9)
    expect(reassignSubgrupoMiembro).toHaveBeenCalledWith(8, 9)
  })
})
