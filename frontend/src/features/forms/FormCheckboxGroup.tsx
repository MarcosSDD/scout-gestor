import type { ReactNode } from "react";

type Option = {
  value: string;
  label: ReactNode;
  checked: boolean;
  onChange: () => void;
};
export function FormCheckboxGroup({
  legend,
  options,
  error,
}: {
  legend: string;
  options: Option[];
  error?: string;
}) {
  const errorId = error
    ? `${legend.replaceAll(/\s+/g, "-").toLowerCase()}-error`
    : undefined;
  return (
    <fieldset className="form-checkbox-group" aria-describedby={errorId}>
      <legend>{legend}</legend>
      {options.map((option) => (
        <label key={option.value}>
          <input
            type="checkbox"
            checked={option.checked}
            onChange={option.onChange}
          />
          {option.label}
        </label>
      ))}
      {error ? (
        <p id={errorId} className="form-control__error">
          {error}
        </p>
      ) : null}
    </fieldset>
  );
}
