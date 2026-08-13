import type { TextareaHTMLAttributes } from "react";

type FormTextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
  error?: string;
  hint?: string;
};

export function FormTextarea({
  id,
  label,
  error,
  hint,
  ...props
}: FormTextareaProps) {
  const fieldId = id ?? props.name;
  const hintId = hint ? `${fieldId}-hint` : undefined;
  const errorId = error ? `${fieldId}-error` : undefined;
  return (
    <div className="form-control" id={`${fieldId}-field`}>
      <label htmlFor={fieldId}>{label}</label>
      <textarea
        id={fieldId}
        aria-invalid={Boolean(error)}
        aria-describedby={
          [hintId, errorId].filter(Boolean).join(" ") || undefined
        }
        {...props}
      />
      {hint ? <small id={hintId}>{hint}</small> : null}
      {error ? (
        <p className="form-control__error" id={errorId}>
          {error}
        </p>
      ) : null}
    </div>
  );
}
