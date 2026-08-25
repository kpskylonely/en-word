export type WrongReviewSource = "wrong" | "all_wrong";

export function parseWrongReviewSource(
  value: unknown,
): WrongReviewSource | null {
  if (value === "wrong" || value === "all_wrong") return value;
  return null;
}

export function resolveReviewBookId(
  item: { book_id?: string },
  fallbackBookId: string,
  source: WrongReviewSource | null,
) {
  if (source === "all_wrong") {
    return item.book_id ?? fallbackBookId;
  }
  return fallbackBookId;
}
