<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { api } from "../api";
import { useBookStore } from "../stores/book";
import { useStudySettings } from "../stores/settings";

const router = useRouter();
const { currentBook, stats, setStats } = useBookStore();
const { settings } = useStudySettings();
const loading = ref(true);

const bookId = computed(() => currentBook.value?.id ?? "");

onMounted(async () => {
  if (!currentBook.value) {
    router.replace("/");
    return;
  }
  try {
    setStats(await api.getStats(bookId.value));
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page">
    <h1 class="page-title">学习模式</h1>
    <p class="page-subtitle">
      选择一种方式开始背单词。
      <RouterLink to="/settings" class="settings-link">调整各模式词量</RouterLink>
    </p>

    <div v-if="loading" class="empty">加载统计中...</div>

    <div v-else-if="stats" class="stat-row">
      <div class="stat-item">
        <strong>{{ stats.total_words }}</strong>
        <span>总词数</span>
      </div>
      <div class="stat-item">
        <strong>{{ stats.learned_words }}</strong>
        <span>已学习</span>
      </div>
      <div class="stat-item">
        <strong>{{ stats.due_today }}</strong>
        <span>待复习</span>
      </div>
      <div class="stat-item">
        <strong>{{ stats.wrong_words }}</strong>
        <span>错词</span>
      </div>
    </div>

    <div class="mode-grid">
      <RouterLink class="mode-card" to="/flashcard">
        <h3>闪卡复习</h3>
        <p>认识 / 模糊 / 不认识 · 每轮 {{ settings.flashcard }} 词</p>
      </RouterLink>
      <RouterLink class="mode-card" to="/quiz/en_zh">
        <h3>英 → 中 选择</h3>
        <p>看英文选中文 · 每轮 {{ settings.en_zh }} 题</p>
      </RouterLink>
      <RouterLink class="mode-card" to="/quiz/zh_en">
        <h3>中 → 英 选择</h3>
        <p>看中文选英文 · 每轮 {{ settings.zh_en }} 题</p>
      </RouterLink>
      <RouterLink class="mode-card" to="/spelling">
        <h3>键盘拼写</h3>
        <p>看中文输入英文 · 每轮 {{ settings.spelling }} 题</p>
      </RouterLink>
      <RouterLink class="mode-card" to="/browse">
        <h3>浏览词表</h3>
        <p>按 Unit 查看 · 每次 {{ settings.browse }} 词</p>
      </RouterLink>
      <RouterLink class="mode-card" to="/study/wrong">
        <h3>本书错词本</h3>
        <p>当前词书的错词 · 选择方式复习</p>
      </RouterLink>
    </div>
  </div>
</template>
