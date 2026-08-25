import type {
  Book,
  BookNode,
  BookProgressSummary,
  BookStudyStats,
  QuizQuestion,
  SpellingItem,
  Stats,
  StatsOverview,
  WordItem,
} from "../types";

const API_BASE = import.meta.env.DEV ? "" : "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  listBooks: () => request<BookNode[]>("/api/books"),
  getBook: (bookId: string) => request<Book>(`/api/books/${bookId}`),
  listUnits: (bookId: string) => request<string[]>(`/api/books/${bookId}/units`),
  browseWords: (
    bookId: string,
    unit: string | null,
    offset: number,
    limit: number,
  ) => {
    const params = new URLSearchParams({
      offset: String(offset),
      limit: String(limit),
    });
    if (unit) params.set("unit", unit);
    return request<WordItem[]>(`/api/books/${bookId}/words?${params}`);
  },
  getDueWords: (bookId: string, limit: number) =>
    request<WordItem[]>(`/api/books/${bookId}/due?limit=${limit}`),
  getNewWords: (bookId: string, limit: number) =>
    request<WordItem[]>(`/api/books/${bookId}/new?limit=${limit}`),
  getQuizQuestions: (
    bookId: string,
    mode: string,
    count: number,
    source: "book" | "wrong" | "all_wrong" = "book",
  ) =>
    request<QuizQuestion[]>(
      `/api/books/${bookId}/quiz?mode=${encodeURIComponent(mode)}&count=${count}&source=${source}`,
    ),
  getSpellingWords: (
    bookId: string,
    count: number,
    source: "book" | "wrong" | "all_wrong" = "book",
  ) =>
    request<SpellingItem[]>(
      `/api/books/${bookId}/spelling?count=${count}&source=${source}`,
    ),
  getWrongWords: (bookId: string) =>
    request<WordItem[]>(`/api/books/${bookId}/wrong`),
  getAllWrongWords: () => request<WordItem[]>("/api/wrong"),
  submitReview: (
    wordId: string,
    bookId: string,
    mode: string,
    result: string,
  ) =>
    request<void>("/api/review", {
      method: "POST",
      body: JSON.stringify({ word_id: wordId, book_id: bookId, mode, result }),
    }),
  getStats: (bookId: string) => request<Stats>(`/api/books/${bookId}/stats`),
  getBookProgress: () => request<BookProgressSummary[]>("/api/progress/books"),
  getStudiedBooksStats: () => request<BookStudyStats[]>("/api/stats/books"),
  getStatsOverview: () => request<StatsOverview>("/api/stats/overview"),
  resetBookProgress: (bookId: string) =>
    request<void>(`/api/books/${bookId}/reset`, { method: "POST" }),
  resetAllProgress: () =>
    request<void>("/api/progress/reset", { method: "POST" }),
};
