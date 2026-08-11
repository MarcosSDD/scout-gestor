import userEvent from '@testing-library/user-event'
import { screen } from '@testing-library/react'
import { render } from '@testing-library/react'
import { PaginatedOptionPicker } from './PaginatedOptionPicker'

describe('PaginatedOptionPicker', () => {
  it('announces options, selects an option and pages accessibly', async () => {
    const user = userEvent.setup(); const onChange = vi.fn(); const onPageChange = vi.fn()
    render(<PaginatedOptionPicker label="Beneficiario" value={null} onChange={onChange} onPageChange={onPageChange} query={{ isLoading: false, isError: false, data: { data: [{ id: 2, nombre: 'Ana Scout' }], meta: { count: 2, previous: null, next: '?page=2' } } }} />)
    expect(screen.getByText('2 opciones disponibles.')).toHaveAttribute('aria-live', 'polite')
    await user.click(screen.getByRole('radio', { name: 'Ana Scout' })); await user.click(screen.getByRole('button', { name: 'Siguiente' }))
    expect(onChange).toHaveBeenCalledWith(2); expect(onPageChange).toHaveBeenCalledWith(1)
  })
})
