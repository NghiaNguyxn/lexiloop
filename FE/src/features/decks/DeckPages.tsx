import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  ArrowRight,
  Books,
  Globe,
  Lock,
  MagnifyingGlass,
  Plus,
  Trash,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { z } from "zod";
import {
  Button,
  ButtonLink,
  ConfirmDialog,
  EmptyState,
  Input,
  PageHeader,
  PageLoader,
  StatusMessage,
  Textarea,
} from "../../components/ui";
import { ApiError, deckApi, vocabularyApi } from "../../lib/api";
import type { DeckInput } from "../../lib/types";

const deckSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Give your deck a name.")
    .max(100, "Use no more than 100 characters."),
  description: z
    .string()
    .trim()
    .max(500, "Use no more than 500 characters.")
    .optional(),
  is_public: z.boolean(),
});

type DeckFormValues = z.infer<typeof deckSchema>;

export function DecksPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const scope = searchParams.get("scope") === "public" ? "public" : "owned";
  const query = searchParams.get("q") ?? "";
  const { data, isLoading, error } = useQuery({
    queryKey: ["decks", scope],
    queryFn: scope === "owned" ? deckApi.owned : deckApi.public,
  });

  const visibleDecks = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    if (!normalized) return data ?? [];
    return (data ?? []).filter((deck) =>
      `${deck.name} ${deck.description ?? ""}`
        .toLocaleLowerCase()
        .includes(normalized),
    );
  }, [data, query]);

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    setSearchParams(next, { replace: true });
  };

  return (
    <div className="page">
      <PageHeader
        eyebrow="Vocabulary library"
        title={scope === "owned" ? "My decks" : "Explore public decks"}
        description={
          scope === "owned"
            ? "Keep your vocabulary organized by topic, goal or course."
            : "Browse vocabulary collections shared by other learners."
        }
        actions={
          <ButtonLink to="/decks/new">
            <Plus aria-hidden /> Create deck
          </ButtonLink>
        }
      />

      <div className="toolbar">
        <div className="segmented-control" aria-label="Deck scope">
          <button
            className={scope === "owned" ? "is-active" : ""}
            onClick={() => setParam("scope", "owned")}
          >
            My decks
          </button>
          <button
            className={scope === "public" ? "is-active" : ""}
            onClick={() => setParam("scope", "public")}
          >
            Public decks
          </button>
        </div>
        <label className="search-field">
          <span className="sr-only">Search decks</span>
          <MagnifyingGlass aria-hidden />
          <input
            value={query}
            onChange={(event) => setParam("q", event.target.value)}
            placeholder="Search by name or description"
          />
        </label>
      </div>

      {isLoading ? <PageLoader label="Loading decks" /> : null}
      {error ? (
        <StatusMessage tone="error">
          {error instanceof ApiError ? error.message : "Decks could not be loaded."}
        </StatusMessage>
      ) : null}
      {!isLoading && !error && visibleDecks.length === 0 ? (
        <EmptyState
          icon={<Books aria-hidden size={38} weight="duotone" />}
          title={query ? "No matching decks" : "No decks here yet"}
          description={
            query
              ? "Try a shorter search or clear the current filter."
              : scope === "owned"
                ? "Create a focused collection and add your first vocabulary."
                : "No public deck is available right now."
          }
          action={
            scope === "owned" && !query ? (
              <ButtonLink to="/decks/new">Create your first deck</ButtonLink>
            ) : undefined
          }
        />
      ) : null}
      {visibleDecks.length ? (
        <div className="deck-grid">
          {visibleDecks.map((deck, index) => (
            <article
              className={`deck-card deck-card--tone-${(index % 3) + 1}`}
              key={deck.id}
            >
              <div className="deck-card__top">
                <div className="deck-card__icon">
                  <Books aria-hidden weight="duotone" />
                </div>
                <span className="badge">
                  {deck.is_public ? (
                    <Globe aria-hidden />
                  ) : (
                    <Lock aria-hidden />
                  )}
                  {deck.is_public ? "Public" : "Private"}
                </span>
              </div>
              <h2>{deck.name}</h2>
              <p>{deck.description || "No description yet."}</p>
              <div className="deck-card__footer">
                <time dateTime={deck.updated_at}>
                  Updated {new Date(deck.updated_at).toLocaleDateString()}
                </time>
                <ButtonLink to={`/decks/${deck.id}`} variant="ghost">
                  Open <ArrowRight aria-hidden />
                </ButtonLink>
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function DeckFormPage() {
  const { deckId } = useParams();
  const id = Number(deckId);
  const isEditing = Number.isFinite(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState("");
  const { data: deck, isLoading } = useQuery({
    queryKey: ["deck", id],
    queryFn: () => deckApi.detail(id),
    enabled: isEditing,
  });
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    control,
    formState: { errors, isSubmitting },
  } = useForm<DeckFormValues>({
    resolver: zodResolver(deckSchema),
    values: deck
      ? {
          name: deck.name,
          description: deck.description ?? "",
          is_public: deck.is_public,
        }
      : undefined,
    defaultValues: { name: "", description: "", is_public: false },
  });
  const isPublic = useWatch({ control, name: "is_public" });

  if (isEditing && isLoading) return <PageLoader label="Loading deck" />;

  const onSubmit = handleSubmit(async (values) => {
    setServerError("");
    const payload: DeckInput = {
      name: values.name.trim(),
      description: values.description?.trim() || null,
      is_public: values.is_public,
    };
    try {
      const saved = isEditing
        ? await deckApi.update(id, payload)
        : await deckApi.create(payload);
      await queryClient.invalidateQueries({ queryKey: ["decks"] });
      queryClient.setQueryData(["deck", saved.id], saved);
      reset(values);
      navigate(`/decks/${saved.id}`);
    } catch (error) {
      setServerError(
        error instanceof ApiError ? error.message : "The deck could not be saved.",
      );
    }
  });

  return (
    <div className="page page--form">
      <Link className="back-link" to={isEditing ? `/decks/${id}` : "/decks"}>
        <ArrowLeft aria-hidden /> Back to {isEditing ? "deck" : "decks"}
      </Link>
      <PageHeader
        eyebrow={isEditing ? "Edit collection" : "New collection"}
        title={isEditing ? "Edit deck" : "Create a deck"}
        description="Give this collection a clear focus. You can add vocabulary after saving it."
      />
      <form className="surface form-stack" onSubmit={onSubmit} noValidate>
        {serverError ? (
          <StatusMessage tone="error">{serverError}</StatusMessage>
        ) : null}
        <Input
          label="Deck name"
          placeholder="e.g. English for developers"
          autoFocus
          error={errors.name?.message}
          {...register("name")}
        />
        <Textarea
          label="Description"
          optional
          rows={4}
          placeholder="What will you collect in this deck?"
          error={errors.description?.message}
          {...register("description")}
        />
        <fieldset className="visibility-picker">
          <legend>Visibility</legend>
          <label className={!isPublic ? "is-selected" : ""}>
            <input type="radio" value="private" checked={!isPublic} onChange={() => setValue("is_public", false, { shouldDirty: true })} />
            <Lock aria-hidden weight="duotone" />
            <span>
              <strong>Private</strong>
              <small>Only you can view and manage this deck.</small>
            </span>
          </label>
          <label className={isPublic ? "is-selected" : ""}>
            <input type="radio" value="public" checked={isPublic} onChange={() => setValue("is_public", true, { shouldDirty: true })} />
            <Globe aria-hidden weight="duotone" />
            <span>
              <strong>Public</strong>
              <small>Other learners can discover and read this deck.</small>
            </span>
          </label>
        </fieldset>
        <div className="form-actions">
          <ButtonLink to={isEditing ? `/decks/${id}` : "/decks"} variant="secondary">
            Cancel
          </ButtonLink>
          <Button type="submit" isLoading={isSubmitting}>
            {isEditing ? "Save changes" : "Create deck"}
          </Button>
        </div>
      </form>
    </div>
  );
}

export function DeckDetailPage() {
  const { deckId } = useParams();
  const id = Number(deckId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const deckQuery = useQuery({
    queryKey: ["deck", id],
    queryFn: () => deckApi.detail(id),
    enabled: Number.isFinite(id),
  });
  const vocabularyQuery = useQuery({
    queryKey: ["vocabularies", id],
    queryFn: () => vocabularyApi.list(id),
    enabled: Number.isFinite(id),
  });
  const removeDeck = useMutation({
    mutationFn: () => deckApi.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["decks"] });
      navigate("/decks", { replace: true });
    },
  });

  if (deckQuery.isLoading || vocabularyQuery.isLoading) {
    return <PageLoader label="Loading deck" />;
  }
  if (deckQuery.error || !deckQuery.data) {
    return (
      <div className="page">
        <StatusMessage tone="error">
          {deckQuery.error instanceof ApiError
            ? deckQuery.error.message
            : "This deck could not be found."}
        </StatusMessage>
      </div>
    );
  }

  const deck = deckQuery.data;
  const vocabularies = (vocabularyQuery.data ?? []).filter((vocabulary) =>
    vocabulary.word.toLocaleLowerCase().includes(search.toLocaleLowerCase()),
  );

  return (
    <div className="page">
      <Link className="back-link" to="/decks">
        <ArrowLeft aria-hidden /> Back to decks
      </Link>
      <section className="deck-hero">
        <div className="deck-hero__icon">
          <Books aria-hidden size={34} weight="duotone" />
        </div>
        <div className="deck-hero__copy">
          <span className="badge">
            {deck.is_public ? <Globe aria-hidden /> : <Lock aria-hidden />}
            {deck.is_public ? "Public" : "Private"}
          </span>
          <h1>{deck.name}</h1>
          <p>{deck.description || "No description yet."}</p>
          <div className="deck-hero__meta">
            <span>{vocabularyQuery.data?.length ?? 0} vocabulary entries</span>
            <span>Updated {new Date(deck.updated_at).toLocaleDateString()}</span>
          </div>
        </div>
        <div className="deck-hero__actions">
          <ButtonLink to={`/decks/${id}/words/new`}>
            <Plus aria-hidden /> Add vocabulary
          </ButtonLink>
          <ButtonLink to={`/decks/${id}/edit`} variant="secondary">
            Edit deck
          </ButtonLink>
          <ConfirmDialog
            trigger={
              <Button variant="ghost" aria-label="Delete deck">
                <Trash aria-hidden /> Delete
              </Button>
            }
            title="Delete this deck?"
            description="Its vocabulary will no longer appear in your library. This action cannot be undone from the app."
            confirmLabel="Delete deck"
            onConfirm={() => removeDeck.mutate()}
            isLoading={removeDeck.isPending}
          />
        </div>
      </section>

      <section className="section">
        <div className="section__heading section__heading--wrap">
          <div>
            <p className="eyebrow">Deck vocabulary</p>
            <h2>Words and meanings</h2>
          </div>
          <label className="search-field">
            <span className="sr-only">Search vocabulary</span>
            <MagnifyingGlass aria-hidden />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search this deck"
            />
          </label>
        </div>

        {vocabularyQuery.error ? (
          <StatusMessage tone="error">Vocabulary could not be loaded.</StatusMessage>
        ) : null}
        {!vocabularies.length && !vocabularyQuery.error ? (
          <EmptyState
            icon={<Books aria-hidden size={38} weight="duotone" />}
            title={search ? "No matching vocabulary" : "Add the first word"}
            description={
              search
                ? "Try a different spelling or clear the search."
                : "Each vocabulary can hold multiple meanings, collocations and examples."
            }
            action={
              !search ? (
                <ButtonLink to={`/decks/${id}/words/new`}>
                  Add vocabulary
                </ButtonLink>
              ) : undefined
            }
          />
        ) : (
          <div className="vocabulary-list">
            {vocabularies.map((vocabulary) => (
              <Link
                className="vocabulary-row"
                to={`/vocabularies/${vocabulary.id}`}
                key={vocabulary.id}
              >
                <div className="word-mark" aria-hidden>
                  {vocabulary.word[0]?.toUpperCase()}
                </div>
                <div>
                  <h3>{vocabulary.word}</h3>
                  <p>
                    {vocabulary.items?.[0]?.vietnamese_meaning ||
                      "Open to view its meanings"}
                  </p>
                </div>
                <span className="badge">
                  {vocabulary.items?.length ?? 0} meanings
                </span>
                <ArrowRight aria-hidden />
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
