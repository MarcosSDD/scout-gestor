import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, Link, RouterProvider } from 'react-router-dom'
import { useDirtyNavigationGuard } from './useDirtyNavigationGuard'

function DirtyPage() { useDirtyNavigationGuard(true); return <><h1>Formulario</h1><Link to="/destino">Salir</Link></> }

describe('useDirtyNavigationGuard', () => {
  beforeEach(() => {
    HTMLDialogElement.prototype.showModal = function showModal() { this.setAttribute('open', '') }
    HTMLDialogElement.prototype.close = function close(value = '') { this.returnValue = value; this.removeAttribute('open'); this.dispatchEvent(new Event('close')) }
  })

  it('blocks navigation, restores the form on cancel and proceeds on discard', async () => {
    const user = userEvent.setup(); const router = createMemoryRouter([{ path: '/', element: <DirtyPage /> }, { path: '/destino', element: <h1>Destino</h1> }], { initialEntries: ['/'] })
    render(<RouterProvider router={router} />)
    await user.click(screen.getByRole('link', { name: 'Salir' }))
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('open'); expect(screen.getByRole('button', { name: 'Keep editing' })).toHaveFocus()
    await user.click(screen.getByRole('button', { name: 'Keep editing' }))
    expect(screen.getByRole('heading', { name: 'Formulario' })).toBeInTheDocument()
    await user.click(screen.getByRole('link', { name: 'Salir' }))
    await user.click(screen.getByRole('button', { name: 'Discard changes' }))
    expect(await screen.findByRole('heading', { name: 'Destino' })).toBeInTheDocument()
  })
})
