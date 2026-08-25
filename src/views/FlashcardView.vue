<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";
import { advanceWithReinforcement, useReinforcement } from "../composables/useReinforcement";
import { useBookStore } from "../stores/book";
import { useStudySettings } from "../stores/settings";
import { parseWrongReviewSource, resolveReviewBookId } from "../utils/wrongBook";
import type { WordItem } from "../types";

const route = useRoute();
const router = useRouter();
const { currentBook } = useBookStore();
const { settings } = useStudySettings();
const queue = ref<WordItem[]>([]);
const index = ref(0);
const flipped = ref(false);
const answering = ref(false);
const loading = ref(true);
const finished = ref(false);

const bookId = computed(() => currentBook.value?.id ?? "");
const wrongSource = computed(() => parseWrongReviewSource(route.query.source));
const fromWrongBook = computed(() => wrongSource.value !== null);
const fromAllWrongBook = computed(() => wrongSource.value === "all_wrong");
const current = computed(() => queue.value[index.value] ?? null);
const pageTitle = computed(() => {
  if (fromAllWrongBook.value) return "总错词本 · 闪卡复习";
  if (fromWrongBook.value) return "本书错词本 · 闪卡复习";
  return "闪卡复习";
});

const {
  phase,
  reinforceCount,
  inReinforce,
  markWrong,
  markCorrect,
  getReinforceQueue,
  hasReinforce,
  startReinforce,
} = useReinforcement<WordItem>();

async function loadQueue() {
  const limit = settings.flashcard;
  if (fromAllWrongBook.value) {
    const wrong = await api.getAllWrongWords();
    queue.value = wrong.slice(0, limit);
    return;
  }
  if (wrongSource.value === "wrong") {
    const wrong = await api.getWrongWords(bookId.value);
    queue.value = wrong.slice(0, limit);
    return;
  }
  const due = await api.getDueWords(bookId.value, limit);
  if (due.length > 0) {
    queue.value = due;
    return;
  }
  queue.value = await api.getNewWords(bookId.value, limit);
}

function toggleFlip() {
  if (answering.value) return;
  flipped.value = !flipped.value;
}

function isCorrectAnswer(result: string) {
  return result === "known";
}

async function answer(result: string) {
  if (!current.value || answering.value) return;
  answering.value = true;
  flipped.value = true;

  if (isCorrectAnswer(result)) {
    markCorrect(current.value);
  } else {
    markWrong({ ...current.value });
  }

  await new Promise((resolve) => setTimeout(resolve, 900));

  await api.submitReview(
    current.value.id,
    resolveReviewBookId(current.value, bookId.value, wrongSource.value),
    "flashcard",
    result,
  );
  flipped.value = false;
  answering.value = false;

  advanceWithReinforcement({
    index,
    queue,
    phase,
    hasReinforce,
    getReinforceQueue,
    startReinforce,
    onFinished: () => {
      finished.value = true;
    },
  });
}

onMounted(async () => {
  if (!fromAllWrongBook.value && !currentBook.value) {
    router.replace("/");
    return;
  }
  await loadQueue();
  loading.value = false;
  if (queue.value.length === 0) {
    finished.value = true;
  }
});
</script>

<template>
  <div class="page">
    <h1 class="page-title">{{ pageTitle }}</h1>
    <p class="page-subtitle">
      {{
        fromAllWrongBook
          ? "复习所有已学词书中的错词，按设置中的词量出题。"
          : fromWrongBook
            ? "仅复习当前词书错词本中的单词，按设置中的词量出题。"
            : "看单词后直接选择掌握程度。不认识/模糊的词会在本轮结束后继续强化。"
      }}
    </p>

    <div v-if="inReinforce" class="feedback bad reinforce-banner">
      强化练习：还有 {{ reinforceCount }} 个错词待掌握（需选「认识」）
    </div>

    <div v-if="loading" class="empty">加载中...</div>
    <div v-else-if="finished" class="card empty">
      {{
        fromWrongBook && queue.length === 0
          ? "错词本为空，暂无需要复习的单词。"
          : "本轮复习完成，错词已全部掌握。"
      }}
      <div class="toolbar" style="justify-content: center">
        <button
          class="btn btn-primary"
          @click="$router.push(fromAllWrongBook ? '/wrong' : '/study')"
        >
          返回
        </button>
      </div>
    </div>

    <div v-else-if="current" class="card">
      <div class="word-display" style="cursor: pointer" @click="toggleFlip">
        <h2>{{ current.word }}</h2>
        <div class="phonetic">
          <span v-if="current.phonetic_uk">英 {{ current.phonetic_uk }}</span>
          <span v-if="current.phonetic_us" style="margin-left: 10px">美 {{ current.phonetic_us }}</span>
        </div>
        <div v-if="fromAllWrongBook && current.book_name" class="book-meta">
          来自：{{ current.book_name }}
        </div>
        <div v-if="flipped" class="translation">
          {{ current.translations.join("；") }}
        </div>
        <div v-if="!flipped" class="book-meta" style="margin-top: 12px">
          也可点击卡片提前查看释义
        </div>
      </div>

      <div class="grid-3">
        <button class="btn btn-danger" :disabled="answering" @click="answer('unknown')">
          不认识
        </button>
        <button class="btn" :disabled="answering" @click="answer('fuzzy')">模糊</button>
        <button class="btn btn-success" :disabled="answering" @click="answer('known')">
          认识
        </button>
      </div>

      <div class="book-meta" style="margin-top: 12px; text-align: center">
        {{ index + 1 }} / {{ queue.length }}
      </div>
    </div>
  </div>
</template>
