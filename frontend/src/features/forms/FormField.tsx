import type { InputHTMLAttributes, ReactNode } from "react";

type FormFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
  hint?: ReactNode;
};

export function FormField({
  id,
  label,
  error,
  hint,
  ...inputProps
}: FormFieldProps) {
  const fieldId = id ?? inputProps.name;
  const hintId = hint ? `${fieldId}-hint` : undefined;
  const errorId = error ? `${fieldId}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div className="form-control" id={`${fieldId}-field`}>
      <label htmlFor={fieldId}>{label}</label>
      <input
        id={fieldId}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy}
        {...inputProps}
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
