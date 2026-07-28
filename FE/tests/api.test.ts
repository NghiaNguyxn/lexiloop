import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, authApi } from "../src/lib/api";

describe("auth API", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends OAuth2 form data and includes refresh cookies", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ access_token: "access-token", token_type: "bearer" }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await authApi.login("learner", "safe-password");

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(options.credentials).toBe("include");
    expect(options.body?.toString()).toContain("username=learner");
    expect(options.body?.toString()).not.toContain("safe-password=");
    expect((options.headers as Headers).get("Content-Type")).toBe(
      "application/x-www-form-urlencoded",
    );
  });

  it("maps backend errors into ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            message: "Invalid username or password.",
            error_code: "INVALID_CREDENTIALS",
          }),
          { status: 401, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(authApi.login("learner", "wrong")).rejects.toMatchObject({
      status: 401,
      code: "INVALID_CREDENTIALS",
      message: "Invalid username or password.",
    } satisfies Partial<ApiError>);
  });
});
