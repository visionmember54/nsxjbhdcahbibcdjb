import { createContext, InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes, useContext, useId } from 'react';

const fieldClass =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 transition-colors focus:border-brand-500 focus:outline-none focus:ring-4 focus:ring-brand-100 aria-[invalid=true]:border-red-500';

// FormField provides an id + error id so any Input/Select/Textarea inside it is
// automatically wired to its label and error message.
const FieldContext = createContext<{ id: string; errorId?: string; invalid: boolean } | null>(null);

function useFieldProps(props: { id?: string }) {
  const ctx = useContext(FieldContext);
  return {
    id: props.id ?? ctx?.id,
    'aria-invalid': ctx?.invalid || undefined,
    'aria-describedby': ctx?.invalid ? ctx.errorId : undefined,
  };
}

export function Label({ children, htmlFor }: { children: React.ReactNode; htmlFor?: string }) {
  return <label htmlFor={htmlFor} className="mb-1 block text-xs font-semibold text-slate-600">{children}</label>;
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...useFieldProps(props)} {...props} className={`${fieldClass} ${props.className ?? ''}`} />;
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...useFieldProps(props)} {...props} className={`${fieldClass} ${props.className ?? ''}`} />;
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...useFieldProps(props)} {...props} className={`${fieldClass} ${props.className ?? ''}`} />;
}

export function FormField({
  label,
  children,
  error,
}: {
  label: string;
  children: React.ReactNode;
  error?: string;
}) {
  const id = useId();
  const errorId = `${id}-error`;
  return (
    <FieldContext.Provider value={{ id, errorId, invalid: !!error }}>
      <div className="mb-3">
        <Label htmlFor={id}>{label}</Label>
        {children}
        {error && <p id={errorId} role="alert" className="mt-1 text-xs text-red-600">{error}</p>}
      </div>
    </FieldContext.Provider>
  );
}

export function Checkbox({ label, ...props }: { label: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-700">
      <input type="checkbox" className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500" {...props} />
      {label}
    </label>
  );
}
