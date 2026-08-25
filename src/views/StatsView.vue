<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { useBookStore } from "../stores/book";
import { formatStudyDate } from "../utils/format";
import type { BookStudyStats, StatsOverview } from "../types";

const router = useRouter();
const { setBook } = useBookStore();
const overview = ref<StatsOverview | null>(null);
const books = ref<BookStudyStats[]>([]);
const loading = ref(true);
const error = ref("");
const resettingBookId = ref("");

const hasData = computed(() => books.value.length > 0);

async function loadStats() {
  const [overviewData, bookStats] = await Promise.all([
    api.getStatsOverview(),
    api.getStudiedBooksStats(),
  ]);
  overview.value = overviewData;
  books.value = bookStats;
}

async function openBook(bookId: string) {
  const book = await api.getBook(bookId);
  if (book) {
    setBook(book);
    router.push("/study");
  }
}

async function clearBookProgress(book: BookStudyStats) {
  if (resettingBookId.value) return;
  if (
    !window.confirm(
      `确定清除「${book.name}」的全部学习记录吗？\n\n包括复习进度、错词本和统计历史。此操作不可恢复。`,
    )
  ) {
    return;
  }
  resettingBookId.value = book.id;
  error.value = "";
  try {
    await api.resetBookProgress(book.id);
    await loadStats();
  } catch (e) {
    error.value = String(e);
  } finally {
    resettingBookId.value = "";
  }
}

onMounted(async () => {
  try {
    await loadStats();
  } catch (e) {
    error.value = String(e);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page">
    <h1 class="page-title">学习统计</h1>
    <p class="page-subtitle">查看已学词书、学习进度，以及整体正确率与错误率。</p>

    <div v-if="loading" class="empty">加载统计中...</div>
    <div v-else-if="error" class="card feedback bad">{{ error }}</div>

    <template v-else>
      <div v-if="overview" class="stat-row">
        <div class="stat-item">
          <strong>{{ overview.studied_books }}</strong>
          <span>已学词书</span>
        </div>
        <div class="stat-item">
          <strong>{{ overview.total_reviews }}</strong>
          <span>总复习次数</span>
        </div>
        <div class="stat-item">
          <strong>{{ overview.accuracy_rate }}%</strong>
          <span>总正确率</span>
        </div>
        <div class="stat-item">
          <strong>{{ overview.error_rate }}%</strong>
          <span>总错误率</span>
        </div>
      </div>

      <div v-if="!hasData" class="card empty">还没有学习记录，先去选书开始学习吧。</div>

      <div v-else class="card stats-table-wrap">
        <table class="stats-table">
          <thead>
            <tr>
              <th>词书</th>
              <th>进度</th>
              <th>正确率</th>
              <th>错误率</th>
              <th>最近学习</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="book in books" :key="book.id">
              <td>
                <div class="stats-book-name">{{ book.name }}</div>
                <div v-if="book.full_name" class="book-meta">{{ book.full_name }}</div>
              </td>
              <td>
                {{ book.learned_words }}/{{ book.total_words }}
                <span class="book-meta">({{ book.progress_rate }}%)</span>
              </td>
              <td>{{ book.accuracy_rate }}%</td>
              <td>{{ book.error_rate }}%</td>
              <td>{{ formatStudyDate(book.last_study_at) || "—" }}</td>
              <td class="stats-actions">
                <button class="btn btn-sm" @click="openBook(book.id)">继续学习</button>
                <button
                  class="btn btn-danger btn-sm"
                  :disabled="resettingBookId === book.id"
                  @click="clearBookProgress(book)"
                >
                  清除记录
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
