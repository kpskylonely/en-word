export interface Book {
  id: string;
  parent_id: string;
  level: number;
  sort_order: number;
  name: string;
  full_name: string;
  word_count: number;
  direct_word_count: number;
  author: string;
  publisher: string;
  comment: string;
}

export interface BookNode {
  id: string;
  parent_id: string;
  level: number;
  sort_order: number;
  name: string;
  full_name: string;
  word_count: number;
  direct_word_count: number;
  author: string;
  publisher: string;
  comment: string;
  children: BookNode[];
}

export interface WordItem {
  id: string;
  word: string;
  phonetic_uk: string;
  phonetic_us: string;
  translations: string[];
  unit_tag: string;
  unit_order: number;
  book_id?: string;
  book_name?: string;
  wrong_count?: number;
}

export interface QuizOption {
  id: string;
  text: string;
}

export interface QuizQuestion {
  word_id: string;
  prompt: string;
  phonetic_uk: string;
  phonetic_us: string;
  correct_id: string;
  correct_text: string;
  options: QuizOption[];
  mode: string;
  book_id?: string;
}

export interface SpellingItem {
  word_id: string;
  prompt: string;
  answer: string;
  phonetic_uk: string;
  phonetic_us: string;
  book_id?: string;
}

export interface Stats {
  total_words: number;
  learned_words: number;
  mastered_words: number;
  due_today: number;
  wrong_words: number;
}

export interface BookProgressSummary {
  book_id: string;
  total_words: number;
  learned_words: number;
  last_study_at: string | null;
  correct_count: number;
  wrong_count: number;
}

export interface BookStudyStats {
  id: string;
  name: string;
  full_name: string;
  total_words: number;
  learned_words: number;
  mastered_words: number;
  last_study_at: string | null;
  review_count: number;
  correct_count: number;
  wrong_count: number;
  accuracy_rate: number;
  error_rate: number;
  progress_rate: number;
}

export interface StatsOverview {
  studied_books: number;
  total_reviews: number;
  correct_count: number;
  wrong_count: number;
  accuracy_rate: number;
  error_rate: number;
}

export type StudyMode =
  | "flashcard"
  | "en_zh"
  | "zh_en"
  | "spelling"
  | "browse"
  | "wrong";
