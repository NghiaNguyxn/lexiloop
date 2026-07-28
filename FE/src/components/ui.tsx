import * as Dialog from "@radix-ui/react-dialog";
import {
  CheckCircle,
  Info,
  SpinnerGap,
  WarningCircle,
  X,
} from "@phosphor-icons/react";
import {
  forwardRef,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type TextareaHTMLAttributes,
} from "react";
import { Link, type LinkProps } from "react-router-dom";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  isLoading?: boolean;
}

export function Button({
  variant = "primary",
  isLoading,
  children,
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`button button--${variant} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? <SpinnerGap aria-hidden className="spin" size={18} /> : null}
      {children}
    </button>
  );
}

export function ButtonLink({
  variant = "primary",
  className = "",
  children,
  ...props
}: LinkProps & { variant?: ButtonVariant }) {
  return (
    <Link className={`button button--${variant} ${className}`} {...props}>
      {children}
    </Link>
  );
}

interface FieldProps {
  label: string;
  error?: string;
  hint?: string;
  optional?: boolean;
}

export const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement> & FieldProps
>(function Input(
  { label, error, hint, optional, id, className = "", ...props },
  ref,
) {
  const inputId = id ?? props.name;
  const descriptionId = `${inputId}-description`;
  return (
    <div className="field">
      <label className="field__label" htmlFor={inputId}>
        <span>{label}</span>
        {optional ? <span className="field__optional">Optional</span> : null}
      </label>
      <input
        ref={ref}
        id={inputId}
        className={`input ${error ? "input--error" : ""} ${className}`}
        aria-invalid={Boolean(error)}
        aria-describedby={error || hint ? descriptionId : undefined}
        {...props}
      />
      {error ? (
        <span id={descriptionId} className="field__error">
          <WarningCircle aria-hidden size={15} />
          {error}
        </span>
      ) : hint ? (
        <span id={descriptionId} className="field__hint">
          {hint}
        </span>
      ) : null}
    </div>
  );
});

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement> & FieldProps
>(function Textarea(
  { label, error, hint, optional, id, className = "", ...props },
  ref,
) {
  const inputId = id ?? props.name;
  const descriptionId = `${inputId}-description`;
  return (
    <div className="field">
      <label className="field__label" htmlFor={inputId}>
        <span>{label}</span>
        {optional ? <span className="field__optional">Optional</span> : null}
      </label>
      <textarea
        ref={ref}
        id={inputId}
        className={`input textarea ${error ? "input--error" : ""} ${className}`}
        aria-invalid={Boolean(error)}
        aria-describedby={error || hint ? descriptionId : undefined}
        {...props}
      />
      {error ? (
        <span id={descriptionId} className="field__error">
          <WarningCircle aria-hidden size={15} />
          {error}
        </span>
      ) : hint ? (
        <span id={descriptionId} className="field__hint">
          {hint}
        </span>
      ) : null}
    </div>
  );
});

export function SelectField({
  label,
  error,
  children,
  id,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & FieldProps) {
  return (
    <div className="field">
      <label className="field__label" htmlFor={id ?? props.name}>{label}</label>
      <select
        id={id ?? props.name}
        className={`input select ${error ? "input--error" : ""}`}
        aria-invalid={Boolean(error)}
        {...props}
      >
        {children}
      </select>
      {error ? <span className="field__error">{error}</span> : null}
    </div>
  );
}

export function StatusMessage({
  tone = "info",
  children,
}: {
  tone?: "success" | "error" | "info";
  children: ReactNode;
}) {
  const Icon =
    tone === "success" ? CheckCircle : tone === "error" ? WarningCircle : Info;
  return (
    <div className={`status-message status-message--${tone}`} role="status">
      <Icon aria-hidden size={20} />
      <span>{children}</span>
    </div>
  );
}

export function PageLoader({ label = "Loading" }: { label?: string }) {
  return (
    <div className="page-loader" role="status">
      <SpinnerGap aria-hidden className="spin" size={30} />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <div className="empty-state__icon">{icon}</div>
      <h2>{title}</h2>
      <p>{description}</p>
      {action}
    </div>
  );
}

export function ConfirmDialog({
  trigger,
  title,
  description,
  confirmLabel = "Delete",
  onConfirm,
  isLoading,
}: {
  trigger: ReactNode;
  title: string;
  description: string;
  confirmLabel?: string;
  onConfirm: () => void;
  isLoading?: boolean;
}) {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>{trigger}</Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog">
          <div className="dialog__header">
            <Dialog.Title>{title}</Dialog.Title>
            <Dialog.Close className="icon-button" aria-label="Close dialog">
              <X aria-hidden size={20} />
            </Dialog.Close>
          </div>
          <Dialog.Description>{description}</Dialog.Description>
          <div className="dialog__actions">
            <Dialog.Close asChild>
              <Button variant="secondary">Cancel</Button>
            </Dialog.Close>
            <Button
              variant="danger"
              isLoading={isLoading}
              onClick={onConfirm}
            >
              {confirmLabel}
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {description ? <p>{description}</p> : null}
      </div>
      {actions ? <div className="page-header__actions">{actions}</div> : null}
    </header>
  );
}
