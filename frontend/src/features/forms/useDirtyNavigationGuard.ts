import { useEffect, useRef } from 'react'
import { useBlocker } from 'react-router-dom'

let allowNextNavigation = false
export function allowDirtyNavigation() { allowNextNavigation = true }

/** Blocks data-router navigation and provides a single native, focus-managed confirmation dialog. */
export function useDirtyNavigationGuard(isDirty: boolean) {
  const blocker = useBlocker(() => {
    if (allowNextNavigation) { allowNextNavigation = false; return false }
    return isDirty
  })
  const dialogRef = useRef<HTMLDialogElement | null>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    const dialog = document.createElement('dialog')
    dialog.className = 'dirty-navigation-dialog'
    dialog.innerHTML = '<form method="dialog"><h2>Changes without saving</h2><p>If you leave now, unsaved changes will be lost.</p><menu><button value="cancel">Keep editing</button><button value="discard">Discard changes</button></menu></form>'
    const onClose = () => {
      if (dialog.returnValue === 'discard') blocker.proceed?.()
      else blocker.reset?.()
      previousFocusRef.current?.focus()
    }
    const onClick = (event: Event) => {
      const button = (event.target as HTMLElement).closest<HTMLButtonElement>('button[value]')
      if (button) { event.preventDefault(); dialog.close(button.value) }
    }
    const onCancel = (event: Event) => { event.preventDefault(); dialog.close('cancel') }
    dialog.addEventListener('close', onClose); dialog.addEventListener('cancel', onCancel); dialog.addEventListener('click', onClick)
    document.body.append(dialog); dialogRef.current = dialog
    return () => { dialog.removeEventListener('close', onClose); dialog.removeEventListener('cancel', onCancel); dialog.removeEventListener('click', onClick); dialog.remove() }
  }, [blocker])

  useEffect(() => {
    if (blocker.state !== 'blocked') return
    const dialog = dialogRef.current
    if (!dialog || dialog.open) return
    previousFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null
    dialog.showModal()
    dialog.querySelector<HTMLButtonElement>('button[value="cancel"]')?.focus()
  }, [blocker.state])

  useEffect(() => {
    if (!isDirty && blocker.state === 'blocked') blocker.reset()
  }, [blocker, isDirty])

  useEffect(() => {
    if (!isDirty) return
    const beforeUnload = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = '' }
    window.addEventListener('beforeunload', beforeUnload)
    return () => window.removeEventListener('beforeunload', beforeUnload)
  }, [isDirty])
}
