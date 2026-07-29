import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import {
  ComboboxField,
  SelectField,
} from "../src/components/form-controls";
import {
  Button,
  ConfirmDialog,
  EmptyState,
  Input,
  StatusMessage,
} from "../src/components/ui";

describe("UI primitives", () => {
  it("exposes field validation to assistive technology", () => {
    render(
      <Input
        label="Username"
        name="username"
        error="Username is required."
        hint="Use your public profile name."
      />,
    );

    const input = screen.getByLabelText("Username");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription(
      "Username is required. Use your public profile name.",
    );
  });

  it("generates a stable accessible id when a field has no name", () => {
    render(<Input label="Search term" />);

    expect(screen.getByLabelText("Search term")).toHaveAttribute("id");
  });

  it("connects select errors to their control", () => {
    render(
      <SelectField
        label="Part of speech"
        value=""
        onValueChange={() => undefined}
        options={[{ value: "", label: "Choose" }]}
        error="Choose a value."
      />,
    );

    const select = screen.getByRole("combobox", {
      name: "Part of speech",
    });
    expect(select).toHaveAttribute("aria-invalid", "true");
    expect(select).toHaveAccessibleDescription("Choose a value.");
  });

  it("lets users choose a select option", async () => {
    const user = userEvent.setup();
    const onValueChange = vi.fn();
    render(
      <SelectField
        label="Part of speech"
        value="noun"
        onValueChange={onValueChange}
        options={[
          { value: "noun", label: "Noun" },
          { value: "verb", label: "Verb" },
        ]}
      />,
    );

    await user.click(
      screen.getByRole("combobox", { name: "Part of speech" }),
    );
    await user.click(screen.getByRole("option", { name: "Verb" }));

    expect(onValueChange).toHaveBeenCalledWith("verb");
  });

  it("lets users search and choose a combobox option", async () => {
    const user = userEvent.setup();
    const onValueChange = vi.fn();
    render(
      <ComboboxField
        label="Linked collocation"
        value=""
        onValueChange={onValueChange}
        options={[
          { value: "", label: "None" },
          { value: "1", label: "deploy an application" },
          { value: "2", label: "deploy to production" },
        ]}
      />,
    );

    await user.click(
      screen.getByRole("combobox", { name: "Linked collocation" }),
    );
    await user.type(
      screen.getByPlaceholderText("Search..."),
      "production",
    );
    await user.click(
      screen.getByRole("option", { name: "deploy to production" }),
    );

    expect(onValueChange).toHaveBeenCalledWith("2");
  });

  it("disables a button while loading", () => {
    render(<Button isLoading>Save changes</Button>);

    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  });

  it("announces status messages", () => {
    render(<StatusMessage tone="success">Profile saved.</StatusMessage>);

    expect(screen.getByRole("status")).toHaveTextContent("Profile saved.");
  });

  it("uses an assertive alert for server errors", () => {
    render(<StatusMessage tone="error">Saving failed.</StatusMessage>);

    expect(screen.getByRole("alert")).toHaveAttribute(
      "aria-live",
      "assertive",
    );
  });

  it("supports a page-level heading in empty states", () => {
    render(
      <EmptyState
        icon={<span>Icon</span>}
        title="Learning is the next loop"
        description="This feature is coming next."
        headingLevel="h1"
      />,
    );

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Learning is the next loop",
      }),
    ).toBeInTheDocument();
  });

  it("returns focus after dismissing a destructive confirmation", async () => {
    const user = userEvent.setup();
    render(
      <ConfirmDialog
        trigger={<Button>Delete example</Button>}
        title="Delete this example?"
        description="This cannot be undone."
        onConfirm={() => undefined}
      />,
    );

    const trigger = screen.getByRole("button", { name: "Delete example" });
    await user.click(trigger);
    expect(
      screen.getByRole("dialog", { name: "Delete this example?" }),
    ).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(trigger).toHaveFocus();
  });
});
