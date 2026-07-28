export type Role = "user" | "admin";

export interface ApiResponse<T> {
  code: number;
  message: string;
  result: T;
  error_code?: string | null;
  errors?: ValidationIssue[] | null;
}

export interface ValidationIssue {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
}

export interface Token {
  access_token: string;
  token_type: "bearer";
}

export interface User {
  id: number;
  username: string;
  email: string;
  phone: string | null;
  full_name: string | null;
  avatar_url: string | null;
  role: Role;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface Deck {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export type PartOfSpeech =
  | "noun"
  | "verb"
  | "adjective"
  | "adverb"
  | "pronoun"
  | "preposition"
  | "conjunction"
  | "determiner"
  | "interjection"
  | "numeral"
  | "auxiliary"
  | "modal"
  | "particle"
  | "phrase"
  | "idiom"
  | "other";

export type CefrLevel = "A1" | "A2" | "B1" | "B2" | "C1" | "C2";

export interface Collocation {
  id: number;
  vocabulary_item_id: number;
  phrase: string;
  english_meaning: string | null;
  vietnamese_meaning: string | null;
  note: string | null;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExampleSentence {
  id: number;
  vocabulary_item_id: number;
  collocation_id: number | null;
  sentence: string;
  vietnamese_meaning: string | null;
  note: string | null;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface VocabularyItem {
  id: number;
  vocabulary_id: number;
  part_of_speech: PartOfSpeech;
  ipa: string | null;
  english_meaning: string;
  vietnamese_meaning: string;
  grammar_note: string | null;
  note: string | null;
  topic: string | null;
  level: CefrLevel | null;
  position: number;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  collocations: Collocation[];
  example_sentences: ExampleSentence[];
}

export interface Vocabulary {
  id: number;
  deck_id: number;
  word: string;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  items: VocabularyItem[];
}

export interface DeckInput {
  name: string;
  description?: string | null;
  is_public: boolean;
}

export interface VocabularyItemInput {
  part_of_speech: PartOfSpeech;
  ipa?: string | null;
  english_meaning: string;
  vietnamese_meaning: string;
  grammar_note?: string | null;
  note?: string | null;
  topic?: string | null;
  level?: CefrLevel | null;
}

export interface VocabularyInput {
  word: string;
  items: VocabularyItemInput[];
}
