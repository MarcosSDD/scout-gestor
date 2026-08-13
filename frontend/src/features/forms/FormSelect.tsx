import type { SelectHTMLAttributes } from "react";

type FormSelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  error?: string;
  hint?: string;
  options: ReadonlyArray<{ value: string; label: string }>;
};

export function FormSelect({
  id,
  label,
  error,
  hint,
  options,
  children,
  ...selectProps
}: FormSelectProps) {
  const fieldId = id ?? selectProps.name;
  const hintId = hint ? `${fieldId}-hint` : undefined;
  const errorId = error ? `${fieldId}-error` : undefined;
  return (
    <div className="form-control" id={`${fieldId}-field`}>
      <label htmlFor={fieldId}>{label}</label>
      <select
        id={fieldId}
        aria-invalid={Boolean(error)}
        aria-describedby={
          [hintId, errorId].filter(Boolean).join(" ") || undefined
        }
        {...selectProps}
      >
        {children}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {hint ? <small id={hintId}>{hint}</small> : null}
      {error ? (
        <p className="form-control__error" id={errorId}>
          {error}
        </p>
      ) : null}
    </div>
  );
}
