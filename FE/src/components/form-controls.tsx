import * as PopoverPrimitive from "@radix-ui/react-popover";
import * as SelectPrimitive from "@radix-ui/react-select";
import {
  CaretDown,
  CaretUp,
  CaretUpDown,
  Check,
  MagnifyingGlass,
  WarningCircle,
} from "@phosphor-icons/react";
import { Command } from "cmdk";
import {
  forwardRef,
  useId,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

const EMPTY_VALUE = "__lexiloop_empty_value__";

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface FieldChromeProps {
  label: string;
  error?: string;
  hint?: string;
  optional?: boolean;
}

interface SelectFieldProps extends FieldChromeProps {
  value: string;
  onValueChange: (value: string) => void;
  options: SelectOption[];
  name?: string;
  id?: string;
  placeholder?: string;
  disabled?: boolean;
  onBlur?: () => void;
}

interface ComboboxFieldProps extends FieldChromeProps {
  value: string;
  onValueChange: (value: string) => void;
  options: SelectOption[];
  name?: string;
  id?: string;
  placeholder?: string;
  searchPlaceholder?: string;
  emptyMessage?: string;
  disabled?: boolean;
  onBlur?: () => void;
}

function getFieldMetadata({
  id,
  name,
  generatedId,
  error,
  hint,
}: {
  id?: string;
  name?: string;
  generatedId: string;
  error?: string;
  hint?: string;
}) {
  const inputId = id ?? name ?? generatedId;
  const errorId = `${inputId}-error`;
  const hintId = `${inputId}-hint`;
  const describedBy = [error ? errorId : null, hint ? hintId : null]
    .filter(Boolean)
    .join(" ");

  return {
    inputId,
    errorId,
    hintId,
    describedBy: describedBy || undefined,
  };
}

function FieldLabel({
  htmlFor,
  label,
  optional,
}: {
  htmlFor: string;
  label: string;
  optional?: boolean;
}) {
  return (
    <label className="field__label" htmlFor={htmlFor}>
      <span>{label}</span>
      {optional ? <span className="field__optional">Optional</span> : null}
    </label>
  );
}

function FieldFeedback({
  error,
  errorId,
  hint,
  hintId,
}: {
  error?: string;
  errorId: string;
  hint?: string;
  hintId: string;
}) {
  return (
    <>
      {error ? (
        <span id={errorId} className="field__error" aria-live="polite">
          <WarningCircle aria-hidden size={15} />
          {error}
        </span>
      ) : null}
      {hint ? (
        <span id={hintId} className="field__hint">
          {hint}
        </span>
      ) : null}
    </>
  );
}

export const SelectField = forwardRef<HTMLButtonElement, SelectFieldProps>(
  function SelectField(
    {
      label,
      error,
      hint,
      optional,
      value,
      onValueChange,
      options,
      name,
      id,
      placeholder = "Select an option",
      disabled,
      onBlur,
    },
    ref,
  ) {
    const generatedId = useId();
    const metadata = getFieldMetadata({
      id,
      name,
      generatedId,
      error,
      hint,
    });
    const radixValue = value === "" ? EMPTY_VALUE : value;

    return (
      <div className="field">
        <FieldLabel
          htmlFor={metadata.inputId}
          label={label}
          optional={optional}
        />
        <SelectPrimitive.Root
          value={radixValue}
          onValueChange={(nextValue) =>
            onValueChange(nextValue === EMPTY_VALUE ? "" : nextValue)
          }
          name={name}
          disabled={disabled}
        >
          <SelectPrimitive.Trigger
            ref={ref}
            id={metadata.inputId}
            className={`input select-trigger ${error ? "input--error" : ""}`}
            aria-invalid={Boolean(error)}
            aria-describedby={metadata.describedBy}
            onBlur={onBlur}
          >
            <SelectPrimitive.Value placeholder={placeholder} />
            <SelectPrimitive.Icon asChild>
              <CaretDown aria-hidden size={18} />
            </SelectPrimitive.Icon>
          </SelectPrimitive.Trigger>
          <SelectPrimitive.Portal>
            <SelectPrimitive.Content
              className="select-content"
              position="popper"
              sideOffset={6}
              collisionPadding={12}
            >
              <SelectPrimitive.ScrollUpButton className="select-scroll-button">
                <CaretUp aria-hidden size={16} />
              </SelectPrimitive.ScrollUpButton>
              <SelectPrimitive.Viewport className="select-viewport">
                {options.map((option) => {
                  const optionValue =
                    option.value === "" ? EMPTY_VALUE : option.value;

                  return (
                    <SelectPrimitive.Item
                      key={optionValue}
                      value={optionValue}
                      disabled={option.disabled}
                      className="select-item"
                    >
                      <SelectPrimitive.ItemText>
                        {option.label}
                      </SelectPrimitive.ItemText>
                      <SelectPrimitive.ItemIndicator className="select-item__indicator">
                        <Check aria-hidden size={16} weight="bold" />
                      </SelectPrimitive.ItemIndicator>
                    </SelectPrimitive.Item>
                  );
                })}
              </SelectPrimitive.Viewport>
              <SelectPrimitive.ScrollDownButton className="select-scroll-button">
                <CaretDown aria-hidden size={16} />
              </SelectPrimitive.ScrollDownButton>
            </SelectPrimitive.Content>
          </SelectPrimitive.Portal>
        </SelectPrimitive.Root>
        <FieldFeedback
          error={error}
          errorId={metadata.errorId}
          hint={hint}
          hintId={metadata.hintId}
        />
      </div>
    );
  },
);

export const ComboboxField = forwardRef<HTMLButtonElement, ComboboxFieldProps>(
  function ComboboxField(
    {
      label,
      error,
      hint,
      optional,
      value,
      onValueChange,
      options,
      name,
      id,
      placeholder = "Select an option",
      searchPlaceholder = "Search...",
      emptyMessage = "No results found.",
      disabled,
      onBlur,
    },
    forwardedRef,
  ) {
    const generatedId = useId();
    const metadata = getFieldMetadata({
      id,
      name,
      generatedId,
      error,
      hint,
    });
    const triggerRef = useRef<HTMLButtonElement>(null);
    const [open, setOpen] = useState(false);
    const [search, setSearch] = useState("");
    const selectedOption = options.find((option) => option.value === value);

    useImperativeHandle(
      forwardedRef,
      () => triggerRef.current as HTMLButtonElement,
    );

    function handleOpenChange(nextOpen: boolean) {
      setOpen(nextOpen);
      if (!nextOpen) {
        setSearch("");
      }
    }

    function selectOption(nextValue: string) {
      onValueChange(nextValue);
      handleOpenChange(false);
      requestAnimationFrame(() => triggerRef.current?.focus());
    }

    return (
      <div className="field">
        <FieldLabel
          htmlFor={metadata.inputId}
          label={label}
          optional={optional}
        />
        <input type="hidden" name={name} value={value} />
        <PopoverPrimitive.Root open={open} onOpenChange={handleOpenChange}>
          <PopoverPrimitive.Trigger asChild>
            <button
              ref={triggerRef}
              id={metadata.inputId}
              type="button"
              role="combobox"
              aria-expanded={open}
              aria-haspopup="listbox"
              aria-invalid={Boolean(error)}
              aria-describedby={metadata.describedBy}
              className={`input combobox-trigger ${error ? "input--error" : ""}`}
              disabled={disabled}
              onBlur={onBlur}
            >
              <span
                className={
                  selectedOption
                    ? "combobox-trigger__value"
                    : "combobox-trigger__placeholder"
                }
              >
                {selectedOption?.label ?? placeholder}
              </span>
              <CaretUpDown aria-hidden size={18} />
            </button>
          </PopoverPrimitive.Trigger>
          <PopoverPrimitive.Portal>
            <PopoverPrimitive.Content
              className="combobox-content"
              align="start"
              sideOffset={6}
              collisionPadding={12}
              onOpenAutoFocus={(event) => event.preventDefault()}
            >
              <Command>
                <div className="combobox-search">
                  <MagnifyingGlass aria-hidden size={17} />
                  <Command.Input
                    value={search}
                    onValueChange={setSearch}
                    className="combobox-input"
                    placeholder={searchPlaceholder}
                    autoFocus
                  />
                </div>
                <Command.List className="combobox-list">
                  <Command.Empty className="combobox-empty">
                    {emptyMessage}
                  </Command.Empty>
                  <Command.Group>
                    {options.map((option) => (
                      <Command.Item
                        key={option.value || EMPTY_VALUE}
                        value={`${option.label} ${option.value}`}
                        disabled={option.disabled}
                        onSelect={() => selectOption(option.value)}
                        className="combobox-item"
                      >
                        <span>{option.label}</span>
                        <Check
                          aria-hidden
                          size={16}
                          weight="bold"
                          className={
                            option.value === value
                              ? "combobox-item__check"
                              : "combobox-item__check combobox-item__check--hidden"
                          }
                        />
                      </Command.Item>
                    ))}
                  </Command.Group>
                </Command.List>
              </Command>
            </PopoverPrimitive.Content>
          </PopoverPrimitive.Portal>
        </PopoverPrimitive.Root>
        <FieldFeedback
          error={error}
          errorId={metadata.errorId}
          hint={hint}
          hintId={metadata.hintId}
        />
      </div>
    );
  },
);
