import { useDirtyNavigationGuard } from './useDirtyNavigationGuard'

export function useUnsavedChanges(isDirty: boolean) {
  useDirtyNavigationGuard(isDirty)
}
