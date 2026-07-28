import type {
  ApiResponse,
  Deck,
  DeckInput,
  Token,
  User,
  ValidationIssue,
  Vocabulary,
  VocabularySummary,
  VocabularyInput,
  VocabularyItem,
  VocabularyItemInput,
  Collocation,
  ExampleSentence,
} from "./types";

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export class ApiError extends Error {
  status: number;
  code?: string | null;
  issues?: ValidationIssue[] | null;

  constructor(
    message: string,
    status: number,
    code?: string | null,
    issues?: ValidationIssue[] | null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.issues = issues;
  }
}

export function setAccessToken(token: string | null) {
  accessToken = token;
}

async function readError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as Partial<ApiResponse<null>>;
    return new ApiError(
      body.message || "Something went wrong. Please try again.",
      response.status,
      body.error_code,
      body.errors,
    );
  } catch {
    return new ApiError(
      response.status >= 500
        ? "The server is unavailable. Please try again shortly."
        : "The request could not be completed.",
      response.status,
    );
  }
}

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    })
      .then(async (response) => {
        if (!response.ok) {
          setAccessToken(null);
          return null;
        }
        const token = (await response.json()) as Token;
        setAccessToken(token.access_token);
        return token.access_token;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

interface ApiFetchOptions extends RequestInit {
  auth?: boolean;
  retryOnUnauthorized?: boolean;
}

async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const {
    auth = true,
    retryOnUnauthorized = true,
    headers,
    ...requestOptions
  } = options;
  const requestHeaders = new Headers(headers);

  if (
    requestOptions.body &&
    !(requestOptions.body instanceof FormData) &&
    !requestHeaders.has("Content-Type")
  ) {
    requestHeaders.set("Content-Type", "application/json");
  }
  if (auth && accessToken) {
    requestHeaders.set("Authorization", `Bearer ${accessToken}`);
  }

  let response = await fetch(`${API_URL}${path}`, {
    ...requestOptions,
    headers: requestHeaders,
    credentials: "include",
  });

  if (auth && response.status === 401 && retryOnUnauthorized) {
    const refreshedToken = await refreshAccessToken();
    if (refreshedToken) {
      requestHeaders.set("Authorization", `Bearer ${refreshedToken}`);
      response = await fetch(`${API_URL}${path}`, {
        ...requestOptions,
        headers: requestHeaders,
        credentials: "include",
      });
    }
  }

  if (!response.ok) throw await readError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function unwrap<T>(response: ApiResponse<T>): T {
  return response.result;
}

export const authApi = {
  async login(username: string, password: string) {
    const form = new URLSearchParams({ username, password });
    const token = await apiFetch<Token>("/auth/login", {
      method: "POST",
      body: form,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      auth: false,
    });
    setAccessToken(token.access_token);
    return token;
  },
  async register(payload: {
    username: string;
    email: string;
    password: string;
    password_confirm: string;
    full_name?: string | null;
  }) {
    return unwrap(
      await apiFetch<ApiResponse<User>>("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
        auth: false,
      }),
    );
  },
  async restoreSession() {
    const token = await refreshAccessToken();
    return token ? userApi.me() : null;
  },
  async logout() {
    await apiFetch<void>("/auth/logout", {
      method: "POST",
      auth: false,
    });
    setAccessToken(null);
  },
  async changePassword(payload: {
    current_password: string;
    new_password: string;
    new_password_confirm: string;
  }) {
    return apiFetch<ApiResponse<null>>("/auth/change-password", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};

export const userApi = {
  async me() {
    return unwrap(await apiFetch<ApiResponse<User>>("/users/me"));
  },
  async update(payload: Partial<Pick<User, "username" | "email" | "phone" | "full_name" | "avatar_url">>) {
    return unwrap(
      await apiFetch<ApiResponse<User>>("/users/me", {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    );
  },
  async remove() {
    return apiFetch<ApiResponse<null>>("/users/me", { method: "DELETE" });
  },
};

export const deckApi = {
  async owned() {
    return unwrap(await apiFetch<ApiResponse<Deck[]>>("/decks/owned?limit=100&offset=0"));
  },
  async public() {
    return unwrap(await apiFetch<ApiResponse<Deck[]>>("/decks/public?limit=100&offset=0"));
  },
  async detail(id: number) {
    return unwrap(await apiFetch<ApiResponse<Deck>>(`/decks/${id}`));
  },
  async create(payload: DeckInput) {
    return unwrap(
      await apiFetch<ApiResponse<Deck>>("/decks", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    );
  },
  async update(id: number, payload: Partial<DeckInput>) {
    return unwrap(
      await apiFetch<ApiResponse<Deck>>(`/decks/${id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    );
  },
  async remove(id: number) {
    return apiFetch<ApiResponse<null>>(`/decks/${id}`, { method: "DELETE" });
  },
};

export const vocabularyApi = {
  async list(deckId: number) {
    return unwrap(
      await apiFetch<ApiResponse<VocabularySummary[]>>(
        `/decks/${deckId}/vocabularies?limit=100&offset=0`,
      ),
    );
  },
  async detail(id: number) {
    return unwrap(
      await apiFetch<ApiResponse<Vocabulary>>(`/vocabularies/${id}`),
    );
  },
  async create(deckId: number, payload: VocabularyInput) {
    return unwrap(
      await apiFetch<ApiResponse<Vocabulary>>(
        `/decks/${deckId}/vocabularies`,
        { method: "POST", body: JSON.stringify(payload) },
      ),
    );
  },
  async updateWord(id: number, word: string) {
    return unwrap(
      await apiFetch<ApiResponse<Vocabulary>>(`/vocabularies/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ word }),
      }),
    );
  },
  async remove(id: number) {
    return apiFetch<ApiResponse<null>>(`/vocabularies/${id}`, {
      method: "DELETE",
    });
  },
  async createItem(vocabularyId: number, payload: VocabularyItemInput) {
    return unwrap(
      await apiFetch<ApiResponse<VocabularyItem>>(
        `/vocabularies/${vocabularyId}/items`,
        { method: "POST", body: JSON.stringify(payload) },
      ),
    );
  },
  async updateItem(id: number, payload: Partial<VocabularyItemInput>) {
    return unwrap(
      await apiFetch<ApiResponse<VocabularyItem>>(`/vocabulary-items/${id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    );
  },
  async removeItem(id: number) {
    return apiFetch<ApiResponse<null>>(`/vocabulary-items/${id}`, {
      method: "DELETE",
    });
  },
};

export const contentApi = {
  async createCollocation(
    itemId: number,
    payload: Pick<Collocation, "phrase"> &
      Partial<Pick<Collocation, "english_meaning" | "vietnamese_meaning" | "note">>,
  ) {
    return unwrap(
      await apiFetch<ApiResponse<Collocation>>(
        `/vocabulary-items/${itemId}/collocations`,
        { method: "POST", body: JSON.stringify(payload) },
      ),
    );
  },
  async removeCollocation(id: number) {
    return apiFetch<ApiResponse<null>>(`/vocabulary-collocations/${id}`, {
      method: "DELETE",
    });
  },
  async updateCollocation(
    id: number,
    payload: Partial<
      Pick<
        Collocation,
        "phrase" | "english_meaning" | "vietnamese_meaning" | "note"
      >
    >,
  ) {
    return unwrap(
      await apiFetch<ApiResponse<Collocation>>(
        `/vocabulary-collocations/${id}`,
        { method: "PATCH", body: JSON.stringify(payload) },
      ),
    );
  },
  async createExample(
    itemId: number,
    payload: Pick<ExampleSentence, "sentence"> &
      Partial<
        Pick<ExampleSentence, "collocation_id" | "vietnamese_meaning" | "note">
      >,
  ) {
    return unwrap(
      await apiFetch<ApiResponse<ExampleSentence>>(
        `/vocabulary-items/${itemId}/example-sentences`,
        { method: "POST", body: JSON.stringify(payload) },
      ),
    );
  },
  async removeExample(id: number) {
    return apiFetch<ApiResponse<null>>(`/example-sentences/${id}`, {
      method: "DELETE",
    });
  },
  async updateExample(
    id: number,
    payload: Partial<
      Pick<
        ExampleSentence,
        "sentence" | "collocation_id" | "vietnamese_meaning" | "note"
      >
    >,
  ) {
    return unwrap(
      await apiFetch<ApiResponse<ExampleSentence>>(`/example-sentences/${id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    );
  },
};
