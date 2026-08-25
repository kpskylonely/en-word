import type { BookNode, BookProgressSummary } from "../types";

export function collectLeafBookIds(node: BookNode): string[] {
  if (node.children.length === 0 && node.direct_word_count > 0) {
    return [node.id];
  }
  return node.children.flatMap(collectLeafBookIds);
}

export function findBookNode(nodes: BookNode[], id: string): BookNode | null {
  for (const node of nodes) {
    if (node.id === id) return node;
    const found = findBookNode(node.children, id);
    if (found) return found;
  }
  return null;
}

export function aggregateBookProgress(
  node: BookNode,
  progressMap: Record<string, BookProgressSummary>,
) {
  let learnedWords = 0;
  let totalWords = 0;
  let lastStudyAt: string | null = null;
  let studiedBooks = 0;

  for (const id of collectLeafBookIds(node)) {
    const item = progressMap[id];
    if (!item) continue;
    totalWords += item.total_words;
    learnedWords += item.learned_words;
    if (item.learned_words > 0) {
      studiedBooks += 1;
    }
    if (item.last_study_at && (!lastStudyAt || item.last_study_at > lastStudyAt)) {
      lastStudyAt = item.last_study_at;
    }
  }

  return { learnedWords, totalWords, lastStudyAt, studiedBooks };
}

export function getStudyStatusLabel(learnedWords: number, totalWords: number) {
  if (learnedWords <= 0 || totalWords <= 0) return null;
  if (learnedWords >= totalWords) return "已学完";
  return "学习中";
}

export function hasStudiedDescendant(
  node: BookNode,
  progressMap: Record<string, BookProgressSummary>,
) {
  return collectLeafBookIds(node).some(
    (id) => (progressMap[id]?.learned_words ?? 0) > 0,
  );
}
