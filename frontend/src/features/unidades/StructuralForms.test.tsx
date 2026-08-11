import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

import { ConfirmingBackLink } from './StructuralForms'

describe('ConfirmingBackLink', () => {
  beforeEach(() => {
    Object.defineProperties(HTMLDialogElement.prototype, {
      showModal: { configurable: true, value: function showModal(this: HTMLDialogElement) { this.setAttribute('open', '') } },
      close: { configurable: true, value: function close(this: HTMLDialogElement) { this.removeAttribute('open') } },
    })
  })

  afterEach(() => {
    delete (HTMLDialogElement.prototype as Partial<HTMLDialogElement>).showModal
    delete (HTMLDialogElement.prototype as Partial<HTMLDialogElement>).close
  })

  async function openDialog() {
    const user = userEvent.setup()
    render(<MemoryRouter><ConfirmingBackLink dirty /></MemoryRouter>)
    const trigger = screen.getByRole('button', { name: /volver/i })
    await user.click(trigger)
    return { trigger, user, dialog: screen.getByRole('dialog') }
  }

  it('restores focus to its trigger when Escape cancels the native dialog', async () => {
    const { trigger, dialog } = await openDialog()

    fireEvent(dialog, new Event('cancel', { cancelable: true }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })

  it('restores focus to its trigger when the backdrop closes the dialog', async () => {
    const { trigger, dialog } = await openDialog()

    fireEvent.click(dialog)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })

  it('restores focus to its trigger when the user keeps editing', async () => {
    const { trigger, user } = await openDialog()

    await user.click(screen.getByRole('button', { name: 'Seguir editando' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })
})
