import { useEffect, useId, useRef, type RefObject } from "react";
import { createPortal } from "react-dom";

type UnsavedChangesDialogProps = {
  open: boolean;
  onContinueEditing: () => void;
  onDiscard: () => void;
  restoreFocusRef?: RefObject<HTMLElement | null>;
};

/** The single confirmation UI for abandoning changes, with native dialog semantics. */
export function UnsavedChangesDialog({
  open,
  onContinueEditing,
  onDiscard,
  restoreFocusRef,
}: UnsavedChangesDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const continueEditingRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(false);
  const titleId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open) {
      if (!dialog.open) {
        previousFocusRef.current =
          document.activeElement instanceof HTMLElement
            ? document.activeElement
            : null;
        dialog.showModal();
        continueEditingRef.current?.focus();
      }
      wasOpenRef.current = true;
      return;
    }

    if (dialog.open) dialog.close();
    if (wasOpenRef.current) {
      (restoreFocusRef?.current ?? previousFocusRef.current)?.focus();
      wasOpenRef.current = false;
    }
  }, [open, restoreFocusRef]);

  return createPortal(
    <dialog
      ref={dialogRef}
      className="unsaved-changes-dialog"
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        onContinueEditing();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) onContinueEditing();
      }}
    >
      <div className="unsaved-changes-dialog__panel">
        <h2 id={titleId}>Cambios sin guardar</h2>
        <p>Si sales ahora, se perderán los cambios sin guardar.</p>
        <div className="unsaved-changes-dialog__actions">
          <button
            ref={continueEditingRef}
            className="unsaved-changes-dialog__button unsaved-changes-dialog__button--secondary"
            type="button"
            onClick={onContinueEditing}
          >
            Seguir editando
          </button>
          <button
            className="unsaved-changes-dialog__button unsaved-changes-dialog__button--destructive"
            type="button"
            onClick={onDiscard}
          >
            Descartar cambios
          </button>
        </div>
      </div>
    </dialog>,
    document.body,
  );
}
