<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { api } from "../api";
import BookTreeNode from "../components/BookTreeNode.vue";
import { useBookStore } from "../stores/book";
import BookStatusTag from "../components/BookStatusTag.vue";
import { findBookNode, getStudyStatusLabel } from "../utils/bookProgress";
import { formatProgressRate, formatStudyDate } from "../utils/format";
import type { Book, BookNode, BookProgressSummary } from "../types";

const router = useRouter();
const { setBook } = useBookStore();
const books = ref<BookNode[]>([]);
const progressMap = ref<Record<string, BookProgressSummary>>({});
const loading = ref(true);
const progressLoaded = ref(false);
const error = ref("");
const selectedId = ref("");
const keyword = ref("");

function flattenLeaves(nodes: BookNode[]): BookNode[] {
  const result: BookNode[] = [];
  for (const node of nodes) {
    if (node.children.length === 0 && node.direct_word_count > 0) {
      result.push(node);
    } else {
      result.push(...flattenLeaves(node.children));
    }
  }
  return result;
}

const filteredRoots = computed(() => {
  const q = keyword.value.trim().toLowerCase();
  if (!q) return books.value;

  function filterNode(node: BookNode): BookNode | null {
    const nameMatch = node.name.toLowerCase().includes(q);
    const children = node.children
      .map(filterNode)
      .filter((item): item is BookNode => item !== null);

    if (node.children.length === 0) {
      return nameMatch && node.direct_word_count > 0 ? node : null;
    }
    if (nameMatch || children.length > 0) {
      return { ...node, children };
    }
    return null;
  }

  return books.value
    .map(filterNode)
    .filter((item): item is BookNode => item !== null);
});

const leafCount = computed(() => flattenLeaves(books.value).length);
const studiedCount = computed(
  () =>
    Object.values(progressMap.value).filter((item) => item.learned_words > 0).length,
);
const expandAll = computed(() => keyword.value.trim().length > 0);

const recentStudiedBooks = computed(() =>
  Object.values(progressMap.value)
    .filter((item) => item.learned_words > 0)
    .sort((a, b) => (b.last_study_at ?? "").localeCompare(a.last_study_at ?? ""))
    .slice(0, 6)
    .map((item) => ({
      ...item,
      name: findBookNode(books.value, item.book_id)?.name ?? item.book_id,
      rate: formatProgressRate(item.learned_words, item.total_words),
      status: getStudyStatusLabel(item.learned_words, item.total_words),
    })),
);

function selectBook(book: Book) {
  selectedId.value = book.id;
}

async function continueStudy(bookId: string) {
  selectedId.value = bookId;
  const book = await api.getBook(bookId);
  if (book) {
    setBook(book);
    router.push("/study");
  }
}

async function startStudy() {
  if (!selectedId.value) return;
  await continueStudy(selectedId.value);
}

onMounted(async () => {
  try {
    books.value = await api.listBooks();
    try {
      const progressData = await api.getBookProgress();
      progressMap.value = Object.fromEntries(
        progressData.map((item) => [item.book_id, item]),
      );
      progressLoaded.value = true;
    } catch {
      progressMap.value = {};
      progressLoaded.value = false;
    }
  } catch (e) {
    error.value = String(e);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page">
    <h1 class="page-title">选择单词书</h1>
    <p class="page-subtitle">
      先选分类，再选具体词表。共 {{ leafCount }} 本词书
      <template v-if="progressLoaded">，已学习 {{ studiedCount }} 本</template>。
      <RouterLink to="/stats" class="settings-link">查看学习统计</RouterLink>
    </p>

    <div v-if="!loading && !progressLoaded" class="card feedback bad" style="margin-bottom: 12px">
      学习进度暂时未能加载，请重启后端服务后刷新页面。
    </div>

    <div v-if="recentStudiedBooks.length > 0" class="recent-studied">
      <h2 class="section-title">最近学习</h2>
      <div class="recent-studied-grid">
        <button
          v-for="item in recentStudiedBooks"
          :key="item.book_id"
          class="recent-studied-card"
          :class="{ active: selectedId === item.book_id }"
          @click="selectedId = item.book_id"
          @dblclick="continueStudy(item.book_id)"
        >
          <div class="recent-studied-head">
            <strong>{{ item.name }}</strong>
            <BookStatusTag v-if="item.status" :label="item.status" />
          </div>
          <span class="book-meta">
            已学 {{ item.learned_words }}/{{ item.total_words }} ({{ item.rate }}%)
          </span>
          <span v-if="item.last_study_at" class="book-meta book-last-study">
            最近学习 {{ formatStudyDate(item.last_study_at) }}
          </span>
        </button>
      </div>
    </div>

    <input
      v-model="keyword"
      class="input-field"
      placeholder="搜索词书名称，例如：四级、人教版、托福"
    />

    <div v-if="loading" class="empty">正在加载词库...</div>
    <div v-else-if="error" class="card feedback bad">{{ error }}</div>

    <div v-else class="card book-panel">
      <ul class="book-tree">
        <BookTreeNode
          v-for="node in filteredRoots"
          :key="node.id"
          :node="node"
          :selected-id="selectedId"
          :expand-all="expandAll"
          :progress-map="progressMap"
          @select="selectBook"
          @open="continueStudy"
        />
      </ul>
      <div v-if="filteredRoots.length === 0" class="empty">没有匹配的词书</div>
    </div>

    <div class="toolbar">
      <button class="btn btn-primary" :disabled="!selectedId" @click="startStudy">
        开始学习
      </button>
    </div>
  </div>
</template>
