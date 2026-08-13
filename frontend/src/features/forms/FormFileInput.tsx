import type { InputHTMLAttributes } from "react";
import { FormField } from "./FormField";

type FormFileInputProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type"
> & { label: string; error?: string; hint?: string };

export function FormFileInput({
  id,
  label,
  error,
  hint,
  ...inputProps
}: FormFileInputProps) {
  return (
    <FormField
      id={id}
      label={label}
      error={error}
      hint={hint}
      type="file"
      {...inputProps}
    />
  );
}
