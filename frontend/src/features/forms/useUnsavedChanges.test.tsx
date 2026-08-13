import { render } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { useUnsavedChanges } from './useUnsavedChanges'

function Probe({ dirty }: { dirty: boolean }) { return useUnsavedChanges(dirty) }
describe('useUnsavedChanges', () => {
  it('registra y limpia la protección beforeunload', () => {
    const add = vi.spyOn(window, 'addEventListener'); const remove = vi.spyOn(window, 'removeEventListener')
    const router = createMemoryRouter([{ path: '*', element: <Probe dirty /> }], { initialEntries: ['/formulario'] })
    const { unmount } = render(<RouterProvider router={router} />)
    expect(add).toHaveBeenCalledWith('beforeunload', expect.any(Function))
    unmount(); expect(remove).toHaveBeenCalledWith('beforeunload', expect.any(Function)); add.mockRestore(); remove.mockRestore()
  })
})
