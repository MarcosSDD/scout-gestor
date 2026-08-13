import type { PropsWithChildren } from "react";

export function FormActions({
  children,
  isSubmitting = false,
  submitLabel,
}: PropsWithChildren<{ isSubmitting?: boolean; submitLabel?: string }>) {
  return (
    <div className="form-actions" aria-busy={isSubmitting}>
      {children}
      {submitLabel ? (
        <button
          className="primary-button"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Guardando…" : submitLabel}
        </button>
      ) : null}
    </div>
  );
}
