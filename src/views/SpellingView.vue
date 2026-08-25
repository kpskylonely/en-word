<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";
import { useAutoAdvance } from "../composables/useAutoAdvance";
import { useAutoAdvanceTimer } from "../composables/useAutoAdvanceTimer";
import { advanceWithReinforcement, useReinforcement } from "../composables/useReinforcement";
import { useBookStore } from "../stores/book";
import { useStudySettings } from "../stores/settings";
import { parseWrongReviewSource, resolveReviewBookId } from "../utils/wrongBook";
import type { SpellingItem } from "../types";

const route = useRoute();
const router = useRouter();
const { currentBook } = useBookStore();
const { settings } = useStudySettings();

const items = ref<SpellingItem[]>([]);
const index = ref(0);
const input = ref("");
const feedback = ref("");
const finished = ref(false);
const loading = ref(true);
const checked = ref(false);
const inputRef = ref<HTMLInputElement | null>(null);

const bookId = computed(() => currentBook.value?.id ?? "");
const wrongSource = computed(() => parseWrongReviewSource(route.query.source));
const fromWrongBook = computed(() => wrongSource.value !== null);
const fromAllWrongBook = computed(() => wrongSource.value === "all_wrong");
const current = computed(() => items.value[index.value] ?? null);
const pageTitle = computed(() => {
  if (fromAllWrongBook.value) return "总错词本 · 键盘拼写";
  if (fromWrongBook.value) return "本书错词本 · 键盘拼写";
  return "键盘拼写";
});

const { autoAdvance } = useAutoAdvance("spelling_auto_advance");

const {
  phase,
  reinforceCount,
  inReinforce,
  markWrong,
  markCorrect,
  getReinforceQueue,
  hasReinforce,
  startReinforce,
} = useReinforcement<SpellingItem>();

function normalize(text: string) {
  return text.trim().toLowerCase();
}

function nextItem() {
  clearAutoTimer();
  input.value = "";
  feedback.value = "";
  checked.value = false;

  advanceWithReinforcement({
    index,
    queue: items,
    phase,
    hasReinforce,
    getReinforceQueue,
    startReinforce,
    onFinished: () => {
      finished.value = true;
    },
  });
  void focusInput();
}

const { autoCountdown, clearAutoTimer, scheduleAutoNext } =
  useAutoAdvanceTimer(nextItem);

async function checkAnswer() {
  if (!current.value || checked.value) return;
  checked.value = true;
  const correct = normalize(input.value) === normalize(current.value.answer);
  feedback.value = correct
    ? "拼写正确"
    : `拼写错误，正确答案：${current.value.answer}`;

  if (correct) {
    markCorrect(current.value);
  } else {
    markWrong({ ...current.value });
  }

  await api.submitReview(
    current.value.word_id,
    resolveReviewBookId(current.value, bookId.value, wrongSource.value),
    "spelling",
    correct ? "correct" : "wrong",
  );

  scheduleAutoNext(autoAdvance.value);
  await nextTick();
  inputRef.value?.focus();
}

function handleEnter() {
  if (!current.value) return;
  if (!checked.value) {
    if (!input.value.trim()) return;
    void checkAnswer();
    return;
  }
  nextItem();
}

async function focusInput() {
  await nextTick();
  inputRef.value?.focus();
}

onMounted(async () => {
  if (!fromAllWrongBook.value && !currentBook.value) {
    router.replace("/");
    return;
  }
  const source = wrongSource.value ?? "book";
  items.value = await api.getSpellingWords(
    bookId.value || "all",
    settings.spelling,
    source,
  );
  loading.value = false;
  if (items.value.length === 0) {
    finished.value = true;
  }
  await focusInput();
});
</script>

<template>
  <div class="page">
    <h1 class="page-title">{{ pageTitle }}</h1>
    <p class="page-subtitle">
      {{
        fromAllWrongBook
          ? "从所有已学词书的错词中拼写，按 Enter 检查，再按 Enter 下一题。"
          : fromWrongBook
            ? "仅从当前词书错词本拼写，按 Enter 检查，再按 Enter 下一题。"
            : "看中文释义输入英文，按 Enter 检查，再按 Enter 下一题。"
      }}
    </p>

    <div class="setting-row">
      <label class="setting-toggle">
        <input v-model="autoAdvance" type="checkbox" />
        <span>答后 5 秒自动下一题</span>
      </label>
    </div>

    <div v-if="inReinforce" class="feedback bad reinforce-banner">
      强化练习：还有 {{ reinforceCount }} 个错词待掌握
    </div>

    <div v-if="loading" class="empty">加载中...</div>
    <div v-else-if="finished" class="card empty">
      {{
        fromWrongBook && items.length === 0
          ? "错词本为空，暂无需要复习的单词。"
          : "本轮拼写完成，错词已全部掌握。"
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
      <div class="word-display">
        <h2 style="font-size: 28px">{{ current.prompt }}</h2>
        <div class="phonetic">
          <span v-if="current.phonetic_uk">英 {{ current.phonetic_uk }}</span>
          <span v-if="current.phonetic_us" style="margin-left: 10px">美 {{ current.phonetic_us }}</span>
        </div>
      </div>

      <input
        ref="inputRef"
        v-model="input"
        class="input-field"
        placeholder="请输入英文单词，按 Enter 检查"
        autocomplete="off"
        spellcheck="false"
        @keydown.enter.prevent="handleEnter"
      />

      <div
        v-if="feedback"
        class="feedback"
        :class="feedback.startsWith('拼写正确') ? 'ok' : 'bad'"
      >
        {{ feedback }}
        <span v-if="autoCountdown > 0" class="book-meta">（{{ autoCountdown }} 秒后下一题）</span>
      </div>

      <div class="toolbar">
        <button class="btn btn-primary" :disabled="!input || checked" @click="checkAnswer">
          检查
        </button>
        <button class="btn" :disabled="!checked" @click="nextItem">下一题</button>
        <span class="book-meta">{{ index + 1 }} / {{ items.length }}</span>
      </div>
    </div>
  </div>
</template>
