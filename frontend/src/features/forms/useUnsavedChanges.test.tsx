import { render } from '@testing-library/react'
import { useUnsavedChanges } from './useUnsavedChanges'

function Probe({ dirty }: { dirty: boolean }) { useUnsavedChanges(dirty); return null }
describe('useUnsavedChanges', () => {
  it('registra y limpia la protección beforeunload', () => {
    const add = vi.spyOn(window, 'addEventListener'); const remove = vi.spyOn(window, 'removeEventListener')
    const { rerender, unmount } = render(<Probe dirty />)
    expect(add).toHaveBeenCalledWith('beforeunload', expect.any(Function))
    rerender(<Probe dirty={false} />); expect(remove).toHaveBeenCalledWith('beforeunload', expect.any(Function))
    unmount(); add.mockRestore(); remove.mockRestore()
  })
})
