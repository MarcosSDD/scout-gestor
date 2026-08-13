import { useDirtyNavigationGuard } from "./useDirtyNavigationGuard";

export function useUnsavedChanges(isDirty: boolean) {
  return useDirtyNavigationGuard(isDirty);
}
