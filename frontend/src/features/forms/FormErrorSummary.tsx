import { useEffect, useRef } from 'react'

export type FormSummaryError = { name?: string; message?: string }

export function FormErrorSummary({ errors }: { errors: FormSummaryError[] }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => { if (errors.length) ref.current?.focus() }, [errors.length])
  if (!errors.length) return null
  return <div ref={ref} className="form-error-summary" role="alert" tabIndex={-1}>
    <strong>Revisa los campos indicados</strong>
    <ul>{errors.map((error, index) => <li key={error.name ?? `global-${index}`}>{error.name ? <a href={`#${error.name}-field`}>{error.message ?? 'Este campo requiere atención.'}</a> : error.message ?? 'Este campo requiere atención.'}</li>)}</ul>
  </div>
}
