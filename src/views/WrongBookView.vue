<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { api } from "../api";
import { useBookStore } from "../stores/book";
import { useStudySettings } from "../stores/settings";
import type { WrongReviewSource } from "../utils/wrongBook";
import type { WordItem } from "../types";

const route = useRoute();
const router = useRouter();
const { currentBook } = useBookStore();
const { settings } = useStudySettings();
const words = ref<WordItem[]>([]);
const loading = ref(true);

const isGlobal = computed(() => route.meta.wrongScope === "all");
const bookId = computed(() => currentBook.value?.id ?? "");

const pageTitle = computed(() => (isGlobal.value ? "总错词本" : "本书错词本"));
const pageSubtitle = computed(() =>
  isGlobal.value
    ? "汇总所有已学词书中答错的单词，可跨词书复习错词。"
    : `仅显示当前词书「${currentBook.value?.name ?? ""}」的错词，可专门复习。`,
);

const reviewSource = computed<WrongReviewSource>(() =>
  isGlobal.value ? "all_wrong" : "wrong",
);

const reviewModes = computed(() => [
  {
    title: "闪卡复习",
    desc: `每轮最多 ${settings.flashcard} 词`,
    to: { path: "/flashcard", query: { source: reviewSource.value } },
  },
  {
    title: "英 → 中 选择",
    desc: `每轮最多 ${settings.en_zh} 题`,
    to: { path: "/quiz/en_zh", query: { source: reviewSource.value } },
  },
  {
    title: "中 → 英 选择",
    desc: `每轮最多 ${settings.zh_en} 题`,
    to: { path: "/quiz/zh_en", query: { source: reviewSource.value } },
  },
  {
    title: "键盘拼写",
    desc: `每轮最多 ${settings.spelling} 题`,
    to: { path: "/spelling", query: { source: reviewSource.value } },
  },
]);

onMounted(async () => {
  if (!isGlobal.value && !currentBook.value) {
    router.replace("/");
    return;
  }
  words.value = isGlobal.value
    ? await api.getAllWrongWords()
    : await api.getWrongWords(bookId.value);
  loading.value = false;
});
</script>

<template>
  <div class="page">
    <h1 class="page-title">{{ pageTitle }}</h1>
    <p class="page-subtitle">{{ pageSubtitle }}</p>

    <div v-if="loading" class="empty">加载中...</div>
    <template v-else>
      <div v-if="words.length === 0" class="card empty">暂无错词，继续保持。</div>

      <template v-else>
        <p class="book-meta" style="margin-bottom: 12px">共 {{ words.length }} 个错词</p>

        <h2 class="section-title">复习错词</h2>
        <div class="mode-grid wrong-review-grid">
          <RouterLink
            v-for="mode in reviewModes"
            :key="mode.title"
            class="mode-card"
            :to="mode.to"
          >
            <h3>{{ mode.title }}</h3>
            <p>{{ mode.desc }}</p>
          </RouterLink>
        </div>

        <h2 class="section-title">错词列表</h2>
        <div class="card">
          <div v-for="item in words" :key="`${item.book_id ?? bookId}-${item.id}`" class="wrong-word-item">
            <div class="wrong-word-head">
              <strong>{{ item.word }}</strong>
              <span v-if="isGlobal && item.book_name" class="book-tag">{{ item.book_name }}</span>
            </div>
            <div class="phonetic">
              <span v-if="item.phonetic_uk">英 {{ item.phonetic_uk }}</span>
              <span v-if="item.phonetic_us" style="margin-left: 10px">美 {{ item.phonetic_us }}</span>
            </div>
            <div class="translation">{{ item.translations.join("；") }}</div>
          </div>
        </div>
      </template>
    </template>

    <div class="toolbar">
      <RouterLink v-if="isGlobal" class="btn" to="/">返回选书</RouterLink>
      <button v-else class="btn" @click="$router.push('/study')">返回学习</button>
    </div>
  </div>
</template>
