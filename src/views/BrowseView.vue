<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { useBookStore } from "../stores/book";
import { useStudySettings } from "../stores/settings";
import type { WordItem } from "../types";

const router = useRouter();
const { currentBook } = useBookStore();
const { settings } = useStudySettings();
const units = ref<string[]>([]);
const words = ref<WordItem[]>([]);
const selectedUnit = ref<string>("");
const loading = ref(true);
const offset = ref(0);

const bookId = computed(() => currentBook.value?.id ?? "");
const limit = computed(() => settings.browse);

async function loadWords(reset = false) {
  if (!bookId.value) return;
  loading.value = true;
  if (reset) offset.value = 0;
  words.value = await api.browseWords(
    bookId.value,
    selectedUnit.value || null,
    offset.value,
    limit.value,
  );
  loading.value = false;
}

async function changeUnit(unit: string) {
  selectedUnit.value = unit;
  await loadWords(true);
}

async function loadMore() {
  offset.value += limit.value;
  const more = await api.browseWords(
    bookId.value,
    selectedUnit.value || null,
    offset.value,
    limit.value,
  );
  words.value.push(...more);
}

onMounted(async () => {
  if (!currentBook.value) {
    router.replace("/");
    return;
  }
  units.value = await api.listUnits(bookId.value);
  await loadWords(true);
});
</script>

<template>
  <div class="page">
    <h1 class="page-title">浏览词表</h1>
    <p class="page-subtitle">按 Unit 查看单词、音标和释义。</p>

    <div class="toolbar">
      <button
        class="btn"
        :class="{ 'btn-primary': !selectedUnit }"
        @click="changeUnit('')"
      >
        全部
      </button>
      <button
        v-for="unit in units"
        :key="unit"
        class="btn"
        :class="{ 'btn-primary': selectedUnit === unit }"
        @click="changeUnit(unit)"
      >
        {{ unit }}
      </button>
    </div>

    <div v-if="loading" class="empty">加载中...</div>
    <div v-else class="card" style="margin-top: 16px">
      <div v-for="item in words" :key="item.id" style="padding: 14px 0; border-bottom: 1px solid #f3f4f6">
        <div style="display: flex; justify-content: space-between; gap: 12px">
          <div>
            <strong>{{ item.word }}</strong>
            <div class="phonetic">
              <span v-if="item.phonetic_uk">英 {{ item.phonetic_uk }}</span>
              <span v-if="item.phonetic_us" style="margin-left: 10px">美 {{ item.phonetic_us }}</span>
            </div>
          </div>
          <div class="book-meta">{{ item.unit_tag }}</div>
        </div>
        <div class="translation">{{ item.translations.join("；") }}</div>
      </div>
      <div v-if="words.length === 0" class="empty">暂无单词</div>
      <div v-else class="toolbar">
        <button class="btn" @click="loadMore">加载更多</button>
      </div>
    </div>
  </div>
</template>
