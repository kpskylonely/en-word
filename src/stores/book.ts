import { ref } from "vue";
import type { Book, Stats } from "../types";

const currentBook = ref<Book | null>(null);
const stats = ref<Stats | null>(null);

export function useBookStore() {
  function setBook(book: Book | null) {
    currentBook.value = book;
  }

  function setStats(value: Stats | null) {
    stats.value = value;
  }

  return {
    currentBook,
    stats,
    setBook,
    setStats,
  };
}
