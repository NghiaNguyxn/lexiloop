import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button, Input, StatusMessage } from "../src/components/ui";

describe("UI primitives", () => {
  it("exposes field validation to assistive technology", () => {
    render(<Input label="Username" name="username" error="Username is required." />);

    const input = screen.getByLabelText("Username");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Username is required.");
  });

  it("disables a button while loading", () => {
    render(<Button isLoading>Save changes</Button>);

    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  });

  it("announces status messages", () => {
    render(<StatusMessage tone="success">Profile saved.</StatusMessage>);

    expect(screen.getByRole("status")).toHaveTextContent("Profile saved.");
  });
});
