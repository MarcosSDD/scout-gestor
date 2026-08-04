import type { InputHTMLAttributes } from 'react'

type FormCheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & { label: string; error?: string }

export function FormCheckbox({ id, label, error, ...inputProps }: FormCheckboxProps) {
  const fieldId = id ?? inputProps.name
  const errorId = error ? `${fieldId}-error` : undefined
  return <div className="form-checkbox" id={`${fieldId}-field`}>
    <input id={fieldId} type="checkbox" aria-invalid={Boolean(error)} aria-describedby={errorId} {...inputProps} />
    <label htmlFor={fieldId}>{label}</label>
    {error ? <p className="form-control__error" id={errorId}>{error}</p> : null}
  </div>
}
