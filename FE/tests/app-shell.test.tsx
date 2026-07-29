import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "../src/components/AppShell";

vi.mock("../src/features/auth/AuthProvider", () => ({
  useAuth: () => ({
    user: {
      username: "learner",
      full_name: "Test Learner",
      email: "learner@example.com",
    },
    signOut: vi.fn(),
  }),
}));

describe("application shell", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("moves focus to main content after client-side navigation", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("scrollTo", vi.fn());

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<h1>Home</h1>} />
            <Route path="decks" element={<h1>Decks</h1>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getAllByRole("link", { name: "Decks" })[0]!);
    expect(
      await screen.findByRole("heading", { level: 1, name: "Decks" }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByRole("main")).toHaveFocus();
    });
  });

  it("exposes a keyboard skip link", () => {
    render(
      <MemoryRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<h1>Home</h1>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Skip to content" })).toHaveAttribute(
      "href",
      "#main-content",
    );
  });
});
