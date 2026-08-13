import { useEffect } from 'react'
import { useBlocker } from 'react-router-dom'
import { UnsavedChangesDialog } from './UnsavedChangesDialog'

let allowNextNavigation = false
export function allowDirtyNavigation() { allowNextNavigation = true }

/** Blocks data-router navigation and returns its declarative confirmation dialog. */
export function useDirtyNavigationGuard(isDirty: boolean) {
  const blocker = useBlocker(() => {
    if (allowNextNavigation) { allowNextNavigation = false; return false }
    return isDirty
  })
  useEffect(() => {
    if (!isDirty && blocker.state === 'blocked') blocker.reset()
  }, [blocker, isDirty])

  useEffect(() => {
    if (!isDirty) return
    const beforeUnload = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = '' }
    window.addEventListener('beforeunload', beforeUnload)
    return () => window.removeEventListener('beforeunload', beforeUnload)
  }, [isDirty])

  return <UnsavedChangesDialog open={blocker.state === 'blocked'} onContinueEditing={() => blocker.reset?.()} onDiscard={() => blocker.proceed?.()} />
}
