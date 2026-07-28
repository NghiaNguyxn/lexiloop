import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  BookOpenText,
  ChatCircleText,
  NotePencil,
  Plus,
  Quotes,
  Trash,
  X,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { z } from "zod";
import {
  Button,
  ButtonLink,
  ConfirmDialog,
  Input,
  PageHeader,
  PageLoader,
  SelectField,
  StatusMessage,
  Textarea,
} from "../../components/ui";
import { ApiError, contentApi, vocabularyApi } from "../../lib/api";
import type {
  CefrLevel,
  Collocation,
  ExampleSentence,
  PartOfSpeech,
  VocabularyItem,
  VocabularyItemInput,
} from "../../lib/types";

const partOfSpeechValues: PartOfSpeech[] = [
  "noun",
  "verb",
  "adjective",
  "adverb",
  "pronoun",
  "preposition",
  "conjunction",
  "determiner",
  "interjection",
  "numeral",
  "auxiliary",
  "modal",
  "particle",
  "phrase",
  "idiom",
  "other",
];

const cefrValues: CefrLevel[] = ["A1", "A2", "B1", "B2", "C1", "C2"];

const itemSchema = z.object({
  part_of_speech: z.enum(partOfSpeechValues),
  ipa: z.string().trim().max(100).optional(),
  english_meaning: z
    .string()
    .trim()
    .min(1, "Add an English definition.")
    .max(500),
  vietnamese_meaning: z
    .string()
    .trim()
    .min(1, "Add a Vietnamese meaning.")
    .max(500),
  grammar_note: z.string().trim().max(1000).optional(),
  note: z.string().trim().max(2000).optional(),
  topic: z.string().trim().max(100).optional(),
  level: z.enum(cefrValues).or(z.literal("")).optional(),
});

const vocabularySchema = z.object({
  word: z.string().trim().min(1, "Enter a word or phrase.").max(100),
  items: z.array(itemSchema).min(1, "Add at least one meaning."),
});

type VocabularyFormValues = z.infer<typeof vocabularySchema>;
type ItemFormValues = z.infer<typeof itemSchema>;

const defaultItem: ItemFormValues = {
  part_of_speech: "noun",
  ipa: "",
  english_meaning: "",
  vietnamese_meaning: "",
  grammar_note: "",
  note: "",
  topic: "",
  level: "",
};

function cleanItem(values: ItemFormValues): VocabularyItemInput {
  return {
    part_of_speech: values.part_of_speech,
    ipa: values.ipa || null,
    english_meaning: values.english_meaning,
    vietnamese_meaning: values.vietnamese_meaning,
    grammar_note: values.grammar_note || null,
    note: values.note || null,
    topic: values.topic || null,
    level: values.level || null,
  };
}

function MeaningFields({
  index,
  register,
  errors,
  canRemove,
  onRemove,
}: {
  index: number;
  register: ReturnType<typeof useForm<VocabularyFormValues>>["register"];
  errors: ReturnType<typeof useForm<VocabularyFormValues>>["formState"]["errors"];
  canRemove: boolean;
  onRemove: () => void;
}) {
  const itemErrors = errors.items?.[index];
  return (
    <section className="meaning-editor">
      <div className="meaning-editor__header">
        <div>
          <span className="meaning-number">{index + 1}</span>
          <h2>Meaning {index + 1}</h2>
        </div>
        {canRemove ? (
          <button
            type="button"
            className="icon-button"
            onClick={onRemove}
            aria-label={`Remove meaning ${index + 1}`}
          >
            <X aria-hidden />
          </button>
        ) : null}
      </div>
      <div className="form-grid form-grid--three">
        <SelectField
          label="Part of speech"
          error={itemErrors?.part_of_speech?.message}
          {...register(`items.${index}.part_of_speech`)}
        >
          {partOfSpeechValues.map((value) => (
            <option value={value} key={value}>
              {value.charAt(0).toUpperCase() + value.slice(1)}
            </option>
          ))}
        </SelectField>
        <Input
          label="IPA"
          optional
          placeholder="/dɪˈplɔɪ/"
          error={itemErrors?.ipa?.message}
          {...register(`items.${index}.ipa`)}
        />
        <SelectField
          label="CEFR level"
          error={itemErrors?.level?.message}
          {...register(`items.${index}.level`)}
        >
          <option value="">Not specified</option>
          {cefrValues.map((value) => (
            <option value={value} key={value}>
              {value}
            </option>
          ))}
        </SelectField>
      </div>
      <div className="form-grid form-grid--two">
        <Textarea
          label="English definition"
          rows={3}
          placeholder="To make an application available for use"
          error={itemErrors?.english_meaning?.message}
          {...register(`items.${index}.english_meaning`)}
        />
        <Textarea
          label="Vietnamese meaning"
          rows={3}
          placeholder="Triển khai"
          error={itemErrors?.vietnamese_meaning?.message}
          {...register(`items.${index}.vietnamese_meaning`)}
        />
      </div>
      <div className="form-grid form-grid--two">
        <Input
          label="Topic"
          optional
          placeholder="Software development"
          error={itemErrors?.topic?.message}
          {...register(`items.${index}.topic`)}
        />
        <Input
          label="Grammar pattern"
          optional
          placeholder="deploy + object"
          error={itemErrors?.grammar_note?.message}
          {...register(`items.${index}.grammar_note`)}
        />
      </div>
      <Textarea
        label="Additional note"
        optional
        rows={2}
        error={itemErrors?.note?.message}
        {...register(`items.${index}.note`)}
      />
    </section>
  );
}

export function VocabularyCreatePage() {
  const { deckId } = useParams();
  const id = Number(deckId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState("");
  const form = useForm<VocabularyFormValues>({
    resolver: zodResolver(vocabularySchema),
    defaultValues: { word: "", items: [defaultItem] },
  });
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "items",
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setServerError("");
    try {
      const created = await vocabularyApi.create(id, {
        word: values.word.trim(),
        items: values.items.map(cleanItem),
      });
      await queryClient.invalidateQueries({ queryKey: ["vocabularies", id] });
      navigate(`/vocabularies/${created.id}`, { replace: true });
    } catch (error) {
      setServerError(
        error instanceof ApiError
          ? error.message
          : "Vocabulary could not be created.",
      );
    }
  });

  return (
    <div className="page page--wide-form">
      <Link className="back-link" to={`/decks/${id}`}>
        <ArrowLeft aria-hidden /> Back to deck
      </Link>
      <PageHeader
        eyebrow="Vocabulary builder"
        title="Add vocabulary"
        description="Start with the word and its meanings. Add collocations and examples after saving."
      />
      <form className="form-stack" onSubmit={onSubmit} noValidate>
        {serverError ? (
          <StatusMessage tone="error">{serverError}</StatusMessage>
        ) : null}
        <section className="surface">
          <Input
            label="Word or phrase"
            placeholder="deploy"
            autoFocus
            error={form.formState.errors.word?.message}
            {...form.register("word")}
          />
        </section>
        {fields.map((field, index) => (
          <MeaningFields
            key={field.id}
            index={index}
            register={form.register}
            errors={form.formState.errors}
            canRemove={fields.length > 1}
            onRemove={() => remove(index)}
          />
        ))}
        <Button
          type="button"
          variant="secondary"
          className="add-meaning-button"
          onClick={() => append({ ...defaultItem })}
        >
          <Plus aria-hidden /> Add another meaning
        </Button>
        <div className="sticky-actions">
          <span>
            {fields.length} {fields.length === 1 ? "meaning" : "meanings"}
          </span>
          <div>
            <ButtonLink to={`/decks/${id}`} variant="secondary">
              Cancel
            </ButtonLink>
            <Button type="submit" isLoading={form.formState.isSubmitting}>
              Save vocabulary
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}

function AddMeaningForm({
  vocabularyId,
  item,
  onDone,
}: {
  vocabularyId: number;
  item?: VocabularyItem;
  onDone: () => void;
}) {
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState("");
  const form = useForm<ItemFormValues>({
    resolver: zodResolver(itemSchema),
    defaultValues: item
      ? {
          part_of_speech: item.part_of_speech,
          ipa: item.ipa ?? "",
          english_meaning: item.english_meaning,
          vietnamese_meaning: item.vietnamese_meaning,
          grammar_note: item.grammar_note ?? "",
          note: item.note ?? "",
          topic: item.topic ?? "",
          level: item.level ?? "",
        }
      : defaultItem,
  });
  const onSubmit = form.handleSubmit(async (values) => {
    setServerError("");
    try {
      if (item) {
        await vocabularyApi.updateItem(item.id, cleanItem(values));
      } else {
        await vocabularyApi.createItem(vocabularyId, cleanItem(values));
      }
      await queryClient.invalidateQueries({
        queryKey: ["vocabulary", vocabularyId],
      });
      onDone();
    } catch (error) {
      setServerError(
        error instanceof ApiError ? error.message : "Meaning could not be saved.",
      );
    }
  });
  return (
    <form className="surface form-stack inline-editor" onSubmit={onSubmit}>
      <div className="inline-editor__header">
        <h2>{item ? "Edit meaning" : "Add a meaning"}</h2>
        <button type="button" className="icon-button" onClick={onDone} aria-label="Close">
          <X aria-hidden />
        </button>
      </div>
      {serverError ? <StatusMessage tone="error">{serverError}</StatusMessage> : null}
      <div className="form-grid form-grid--three">
        <SelectField label="Part of speech" {...form.register("part_of_speech")}>
          {partOfSpeechValues.map((value) => (
            <option key={value} value={value}>{value}</option>
          ))}
        </SelectField>
        <Input label="IPA" optional {...form.register("ipa")} />
        <SelectField label="CEFR level" {...form.register("level")}>
          <option value="">Not specified</option>
          {cefrValues.map((value) => <option key={value}>{value}</option>)}
        </SelectField>
      </div>
      <div className="form-grid form-grid--two">
        <Textarea label="English definition" error={form.formState.errors.english_meaning?.message} {...form.register("english_meaning")} />
        <Textarea label="Vietnamese meaning" error={form.formState.errors.vietnamese_meaning?.message} {...form.register("vietnamese_meaning")} />
      </div>
      <Input label="Topic" optional {...form.register("topic")} />
      <Input label="Grammar pattern" optional {...form.register("grammar_note")} />
      <Textarea label="Additional note" optional {...form.register("note")} />
      <div className="form-actions">
        <Button type="button" variant="secondary" onClick={onDone}>Cancel</Button>
        <Button type="submit" isLoading={form.formState.isSubmitting}>
          {item ? "Save meaning" : "Add meaning"}
        </Button>
      </div>
    </form>
  );
}

function ContentComposer({
  item,
  type,
  existing,
  onDone,
}: {
  item: VocabularyItem;
  type: "collocation" | "example";
  existing?: Collocation | ExampleSentence;
  onDone: () => void;
}) {
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState("");
  const schema =
    type === "collocation"
      ? z.object({
          primary: z.string().trim().min(1, "Enter a phrase."),
          vietnamese: z.string().trim().optional(),
          note: z.string().trim().optional(),
          collocationId: z.string().optional(),
        })
      : z.object({
          primary: z.string().trim().min(1, "Enter an example sentence."),
          vietnamese: z.string().trim().optional(),
          note: z.string().trim().optional(),
          collocationId: z.string().optional(),
        });
  type Values = z.infer<typeof schema>;
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: {
      primary:
        existing && "phrase" in existing
          ? existing.phrase
          : existing && "sentence" in existing
            ? existing.sentence
            : "",
      vietnamese: existing?.vietnamese_meaning ?? "",
      note: existing?.note ?? "",
      collocationId:
        existing && "collocation_id" in existing && existing.collocation_id
          ? String(existing.collocation_id)
          : "",
    },
  });
  const onSubmit = form.handleSubmit(async (values) => {
    setServerError("");
    try {
      if (type === "collocation") {
        const payload = {
          phrase: values.primary,
          vietnamese_meaning: values.vietnamese || null,
          note: values.note || null,
        };
        if (existing && "phrase" in existing) {
          await contentApi.updateCollocation(existing.id, payload);
        } else {
          await contentApi.createCollocation(item.id, payload);
        }
      } else {
        const payload = {
          sentence: values.primary,
          vietnamese_meaning: values.vietnamese || null,
          note: values.note || null,
          collocation_id: values.collocationId
            ? Number(values.collocationId)
            : null,
        };
        if (existing && "sentence" in existing) {
          await contentApi.updateExample(existing.id, payload);
        } else {
          await contentApi.createExample(item.id, payload);
        }
      }
      await queryClient.invalidateQueries({
        queryKey: ["vocabulary", item.vocabulary_id],
      });
      onDone();
    } catch (error) {
      setServerError(
        error instanceof ApiError ? error.message : "Content could not be added.",
      );
    }
  });
  return (
    <form className="content-composer form-stack" onSubmit={onSubmit}>
      {serverError ? <StatusMessage tone="error">{serverError}</StatusMessage> : null}
      <Textarea
        label={type === "collocation" ? "Collocation phrase" : "English sentence"}
        rows={2}
        autoFocus
        error={form.formState.errors.primary?.message}
        {...form.register("primary")}
      />
      <Textarea
        label="Vietnamese translation"
        optional
        rows={2}
        {...form.register("vietnamese")}
      />
      {type === "example" && item.collocations.length ? (
        <SelectField label="Linked collocation" {...form.register("collocationId")}>
          <option value="">None</option>
          {item.collocations.map((collocation) => (
            <option value={collocation.id} key={collocation.id}>
              {collocation.phrase}
            </option>
          ))}
        </SelectField>
      ) : null}
      <Textarea label="Note" optional rows={2} {...form.register("note")} />
      <div className="form-actions">
        <Button type="button" variant="ghost" onClick={onDone}>Cancel</Button>
        <Button type="submit" isLoading={form.formState.isSubmitting}>
          {existing ? "Save changes" : `Add ${type}`}
        </Button>
      </div>
    </form>
  );
}

function MeaningCard({
  item,
  index,
}: {
  item: VocabularyItem;
  index: number;
}) {
  const queryClient = useQueryClient();
  const [composer, setComposer] = useState<{
    type: "collocation" | "example";
    existing?: Collocation | ExampleSentence;
  } | null>(null);
  const [editingMeaning, setEditingMeaning] = useState(false);
  const removeItem = useMutation({
    mutationFn: () => vocabularyApi.removeItem(item.id),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: ["vocabulary", item.vocabulary_id],
      }),
  });
  const removeCollocation = useMutation({
    mutationFn: contentApi.removeCollocation,
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: ["vocabulary", item.vocabulary_id],
      }),
  });
  const removeExample = useMutation({
    mutationFn: contentApi.removeExample,
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: ["vocabulary", item.vocabulary_id],
      }),
  });

  return (
    <>
    {editingMeaning ? (
      <AddMeaningForm
        vocabularyId={item.vocabulary_id}
        item={item}
        onDone={() => setEditingMeaning(false)}
      />
    ) : null}
    <article className="meaning-card">
      <header className="meaning-card__header">
        <div>
          <span className="meaning-number">{index + 1}</span>
          <div>
            <div className="meaning-card__badges">
              <span className="badge badge--primary">{item.part_of_speech}</span>
              {item.level ? <span className="badge">{item.level}</span> : null}
              {item.topic ? <span className="badge">{item.topic}</span> : null}
            </div>
            {item.ipa ? <p className="ipa">{item.ipa}</p> : null}
          </div>
        </div>
        <div className="meaning-card__actions">
        <Button variant="ghost" onClick={() => setEditingMeaning(true)}>
          <NotePencil aria-hidden /> Edit
        </Button>
        <ConfirmDialog
          trigger={
            <Button variant="ghost" aria-label={`Delete meaning ${index + 1}`}>
              <Trash aria-hidden />
            </Button>
          }
          title="Delete this meaning?"
          description="Its collocations and example sentences will also be removed."
          confirmLabel="Delete meaning"
          onConfirm={() => removeItem.mutate()}
          isLoading={removeItem.isPending}
        />
        </div>
      </header>
      <div className="meaning-card__definitions">
        <div>
          <span>English definition</span>
          <p>{item.english_meaning}</p>
        </div>
        <div>
          <span>Vietnamese meaning</span>
          <p>{item.vietnamese_meaning}</p>
        </div>
      </div>
      {item.grammar_note || item.note ? (
        <div className="note-grid">
          {item.grammar_note ? (
            <div><strong>Grammar</strong><p>{item.grammar_note}</p></div>
          ) : null}
          {item.note ? <div><strong>Note</strong><p>{item.note}</p></div> : null}
        </div>
      ) : null}
      <section className="content-section">
        <div className="content-section__header">
          <h3><ChatCircleText aria-hidden /> Collocations</h3>
          <Button variant="ghost" onClick={() => setComposer({ type: "collocation" })}>
            <Plus aria-hidden /> Add
          </Button>
        </div>
        {composer?.type === "collocation" ? (
          <ContentComposer item={item} type="collocation" existing={composer.existing} onDone={() => setComposer(null)} />
        ) : null}
        {item.collocations.length ? (
          <div className="content-list">
            {item.collocations.map((collocation) => (
              <div className="content-card" key={collocation.id}>
                <div><strong>{collocation.phrase}</strong><p>{collocation.vietnamese_meaning || collocation.english_meaning || "No meaning added."}</p></div>
                <div className="content-card__actions">
                <button className="icon-button" aria-label={`Edit ${collocation.phrase}`} onClick={() => setComposer({ type: "collocation", existing: collocation })}>
                  <NotePencil aria-hidden />
                </button>
                <button className="icon-button" aria-label={`Delete ${collocation.phrase}`} onClick={() => removeCollocation.mutate(collocation.id)}>
                  <Trash aria-hidden />
                </button>
                </div>
              </div>
            ))}
          </div>
        ) : <p className="content-empty">No collocations yet.</p>}
      </section>
      <section className="content-section">
        <div className="content-section__header">
          <h3><Quotes aria-hidden /> Example sentences</h3>
          <Button variant="ghost" onClick={() => setComposer({ type: "example" })}>
            <Plus aria-hidden /> Add
          </Button>
        </div>
        {composer?.type === "example" ? (
          <ContentComposer item={item} type="example" existing={composer.existing} onDone={() => setComposer(null)} />
        ) : null}
        {item.example_sentences.length ? (
          <div className="content-list">
            {item.example_sentences.map((example) => (
              <blockquote className="example-card" key={example.id}>
                <div><p>“{example.sentence}”</p>{example.vietnamese_meaning ? <cite>{example.vietnamese_meaning}</cite> : null}</div>
                <div className="content-card__actions">
                <button className="icon-button" aria-label="Edit example sentence" onClick={() => setComposer({ type: "example", existing: example })}>
                  <NotePencil aria-hidden />
                </button>
                <button className="icon-button" aria-label="Delete example sentence" onClick={() => removeExample.mutate(example.id)}>
                  <Trash aria-hidden />
                </button>
                </div>
              </blockquote>
            ))}
          </div>
        ) : <p className="content-empty">No example sentences yet.</p>}
      </section>
    </article>
    </>
  );
}

export function VocabularyDetailPage() {
  const { vocabularyId } = useParams();
  const id = Number(vocabularyId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [editingWord, setEditingWord] = useState(false);
  const [addingMeaning, setAddingMeaning] = useState(false);
  const [word, setWord] = useState("");
  const { data, isLoading, error } = useQuery({
    queryKey: ["vocabulary", id],
    queryFn: () => vocabularyApi.detail(id),
    enabled: Number.isFinite(id),
  });
  const updateWord = useMutation({
    mutationFn: () => vocabularyApi.updateWord(id, word),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["vocabulary", id] });
      setEditingWord(false);
    },
  });
  const removeVocabulary = useMutation({
    mutationFn: () => vocabularyApi.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["vocabularies", data?.deck_id],
      });
      navigate(`/decks/${data?.deck_id}`, { replace: true });
    },
  });

  if (isLoading) return <PageLoader label="Loading vocabulary" />;
  if (error || !data) {
    return <div className="page"><StatusMessage tone="error">{error instanceof ApiError ? error.message : "Vocabulary could not be found."}</StatusMessage></div>;
  }

  return (
    <div className="page page--vocabulary">
      <Link className="back-link" to={`/decks/${data.deck_id}`}>
        <ArrowLeft aria-hidden /> Back to deck
      </Link>
      <header className="vocabulary-hero">
        <div>
          <p className="eyebrow">Vocabulary detail</p>
          {editingWord ? (
            <form className="word-editor" onSubmit={(event) => { event.preventDefault(); updateWord.mutate(); }}>
              <label className="sr-only" htmlFor="word-edit">Word</label>
              <input id="word-edit" value={word} onChange={(event) => setWord(event.target.value)} autoFocus />
              <Button type="submit" isLoading={updateWord.isPending}>Save</Button>
              <Button type="button" variant="ghost" onClick={() => setEditingWord(false)}>Cancel</Button>
            </form>
          ) : (
            <h1>{data.word}</h1>
          )}
          <p>{data.items.length} {data.items.length === 1 ? "meaning" : "meanings"} with contextual learning content.</p>
        </div>
        <div className="page-header__actions">
          <Button variant="secondary" onClick={() => { setWord(data.word); setEditingWord(true); }}>
            <NotePencil aria-hidden /> Edit word
          </Button>
          <Button onClick={() => setAddingMeaning(true)}>
            <Plus aria-hidden /> Add meaning
          </Button>
          <ConfirmDialog
            trigger={<Button variant="ghost"><Trash aria-hidden /> Delete</Button>}
            title="Delete this vocabulary?"
            description="All its meanings, collocations and examples will be removed from the deck."
            confirmLabel="Delete vocabulary"
            onConfirm={() => removeVocabulary.mutate()}
            isLoading={removeVocabulary.isPending}
          />
        </div>
      </header>
      {addingMeaning ? (
        <AddMeaningForm vocabularyId={id} onDone={() => setAddingMeaning(false)} />
      ) : null}
      <div className="meaning-stack">
        {data.items.map((item, index) => (
          <MeaningCard item={item} index={index} key={item.id} />
        ))}
      </div>
      {!data.items.length ? (
        <div className="surface no-meanings">
          <BookOpenText aria-hidden size={36} weight="duotone" />
          <h2>Add a meaning to continue</h2>
          <Button onClick={() => setAddingMeaning(true)}><Plus aria-hidden /> Add meaning</Button>
        </div>
      ) : null}
    </div>
  );
}
