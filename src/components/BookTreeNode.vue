<script setup lang="ts">
import { computed, ref, watch } from "vue";
import BookStatusTag from "./BookStatusTag.vue";
import type { Book, BookNode, BookProgressSummary } from "../types";
import {
  aggregateBookProgress,
  getStudyStatusLabel,
} from "../utils/bookProgress";
import { formatProgressRate, formatStudyDate } from "../utils/format";

const props = defineProps<{
  node: BookNode;
  selectedId: string;
  depth?: number;
  expandAll?: boolean;
  progressMap?: Record<string, BookProgressSummary>;
}>();

defineEmits<{
  select: [book: Book];
}>();

const expanded = ref(false);
const isCategory = computed(() => props.node.children.length > 0);
const isSelectable = computed(
  () => props.node.children.length === 0 && props.node.direct_word_count > 0,
);

const progress = computed(() => props.progressMap?.[props.node.id] ?? null);

const categoryProgress = computed(() => {
  if (!isCategory.value || !props.progressMap) return null;
  const aggregated = aggregateBookProgress(props.node, props.progressMap);
  if (aggregated.learnedWords <= 0) return null;
  return aggregated;
});

const studyStatusLabel = computed(() => {
  if (!progress.value) return null;
  return getStudyStatusLabel(progress.value.learned_words, progress.value.total_words);
});

const categoryStatusLabel = computed(() => {
  if (!categoryProgress.value) return null;
  return getStudyStatusLabel(
    categoryProgress.value.learnedWords,
    categoryProgress.value.totalWords,
  );
});

watch(
  () => props.expandAll,
  (value) => {
    if (isCategory.value) {
      expanded.value = !!value;
    }
  },
  { immediate: true },
);

function toggle() {
  if (isCategory.value) {
    expanded.value = !expanded.value;
  }
}

function progressText() {
  if (!progress.value) {
    return `${props.node.direct_word_count} 词`;
  }
  const rate = formatProgressRate(
    progress.value.learned_words,
    progress.value.total_words,
  );
  if (progress.value.learned_words <= 0) {
    return `${progress.value.total_words} 词 · 未学习`;
  }
  return `已学 ${progress.value.learned_words}/${progress.value.total_words} (${rate}%)`;
}

function categoryProgressText() {
  if (!categoryProgress.value) {
    return `${props.node.word_count} 词 · ${props.node.children.length} 个子分类`;
  }
  const { learnedWords, totalWords, studiedBooks } = categoryProgress.value;
  const rate = formatProgressRate(learnedWords, totalWords);
  return `已学 ${learnedWords}/${totalWords} (${rate}%) · ${studiedBooks} 本在学`;
}

function lastStudyText(value: string | null | undefined) {
  if (!value) return "";
  return `最近学习 ${formatStudyDate(value)}`;
}
</script>

<template>
  <li>
    <div
      v-if="isSelectable"
      class="book-item book-leaf"
      :class="{
        active: selectedId === node.id,
        studied: progress && progress.learned_words > 0,
      }"
      @click="$emit('select', node)"
    >
      <div class="book-item-main">
        <div class="book-item-row">
          <span class="book-item-name">{{ node.name }}</span>
          <BookStatusTag v-if="studyStatusLabel" :label="studyStatusLabel" />
        </div>
        <div class="book-meta">{{ progressText() }}</div>
        <div v-if="lastStudyText(progress?.last_study_at)" class="book-meta book-last-study">
          {{ lastStudyText(progress?.last_study_at) }}
        </div>
      </div>
    </div>

    <div v-else-if="isCategory" class="book-category">
      <div
        class="book-item category-header"
        :class="{ studied: categoryProgress }"
        @click="toggle"
      >
        <div class="book-item-main">
          <div class="book-item-row">
            <span class="book-item-name">
              {{ expanded ? "▾" : "▸" }} {{ node.name }}
            </span>
            <BookStatusTag v-if="categoryStatusLabel" :label="categoryStatusLabel" />
          </div>
          <div class="book-meta">{{ categoryProgressText() }}</div>
          <div
            v-if="lastStudyText(categoryProgress?.lastStudyAt)"
            class="book-meta book-last-study"
          >
            {{ lastStudyText(categoryProgress?.lastStudyAt) }}
          </div>
        </div>
      </div>
      <ul v-show="expanded">
        <BookTreeNode
          v-for="child in node.children"
          :key="child.id"
          :node="child"
          :selected-id="selectedId"
          :depth="(depth ?? 0) + 1"
          :expand-all="expandAll"
          :progress-map="progressMap"
          @select="$emit('select', $event)"
        />
      </ul>
    </div>

    <div v-else class="book-item">
      <div class="book-item-row">
        <span class="book-item-name">{{ node.name }}</span>
      </div>
    </div>
  </li>
</template>

<script lang="ts">
export default {
  name: "BookTreeNode",
};
</script>
