<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";
import { useAutoAdvance } from "../composables/useAutoAdvance";
import { useAutoAdvanceTimer } from "../composables/useAutoAdvanceTimer";
import { advanceWithReinforcement, useReinforcement } from "../composables/useReinforcement";
import { useBookStore } from "../stores/book";
import { useStudySettings } from "../stores/settings";
import { parseWrongReviewSource, resolveReviewBookId } from "../utils/wrongBook";
import type { QuizQuestion } from "../types";

const route = useRoute();
const router = useRouter();
const { currentBook } = useBookStore();
const { settings } = useStudySettings();

const questions = ref<QuizQuestion[]>([]);
const index = ref(0);
const selectedId = ref("");
const isCorrect = ref(false);
const feedback = ref("");
const finished = ref(false);
const loading = ref(true);

const mode = computed(() => String(route.params.mode));
const bookId = computed(() => currentBook.value?.id ?? "");
const wrongSource = computed(() => parseWrongReviewSource(route.query.source));
const fromWrongBook = computed(() => wrongSource.value !== null);
const fromAllWrongBook = computed(() => wrongSource.value === "all_wrong");
const current = computed(() => questions.value[index.value] ?? null);
const title = computed(() => {
  const base = mode.value === "zh_en" ? "中 → 英 选择" : "英 → 中 选择";
  if (fromAllWrongBook.value) return `总错词本 · ${base}`;
  if (fromWrongBook.value) return `本书错词本 · ${base}`;
  return base;
});

const { autoAdvance } = useAutoAdvance(`quiz_auto_advance_${mode.value}`);

const {
  phase,
  reinforceCount,
  inReinforce,
  markWrong,
  markCorrect,
  getReinforceQueue,
  hasReinforce,
  startReinforce,
} = useReinforcement<QuizQuestion>();

function nextQuestion() {
  clearAutoTimer();
  selectedId.value = "";
  isCorrect.value = false;
  feedback.value = "";

  advanceWithReinforcement({
    index,
    queue: questions,
    phase,
    hasReinforce,
    getReinforceQueue,
    startReinforce,
    onFinished: () => {
      finished.value = true;
    },
  });
}

const { autoCountdown, clearAutoTimer, scheduleAutoNext } =
  useAutoAdvanceTimer(nextQuestion);

async function choose(optionId: string) {
  if (!current.value || selectedId.value) return;
  selectedId.value = optionId;
  const correct = optionId === current.value.correct_id;
  isCorrect.value = correct;
  feedback.value = correct
    ? "回答正确"
    : `回答错误，正确答案：${current.value.correct_text}`;

  if (correct) {
    markCorrect(current.value);
  } else {
    markWrong({ ...current.value });
  }

  await api.submitReview(
    current.value.word_id,
    resolveReviewBookId(current.value, bookId.value, wrongSource.value),
    mode.value,
    correct ? "correct" : "wrong",
  );

  scheduleAutoNext(autoAdvance.value);
}

const answerEnglish = computed(() => {
  if (!current.value) return "";
  return mode.value === "zh_en" ? current.value.correct_text : current.value.prompt;
});

const showAnswerPhonetic = computed(
  () =>
    mode.value === "zh_en" &&
    !!selectedId.value &&
    !!current.value &&
    (current.value.phonetic_uk || current.value.phonetic_us),
);

onMounted(async () => {
  if (!fromAllWrongBook.value && !currentBook.value) {
    router.replace("/");
    return;
  }
  if (mode.value !== "en_zh" && mode.value !== "zh_en") {
    router.replace("/study");
    return;
  }
  const count = mode.value === "zh_en" ? settings.zh_en : settings.en_zh;
  const source = wrongSource.value ?? "book";
  questions.value = await api.getQuizQuestions(bookId.value || "all", mode.value, count, source);
  loading.value = false;
  if (questions.value.length === 0) {
    finished.value = true;
  }
});

</script>

<template>
  <div class="page">
    <h1 class="page-title">{{ title }}</h1>
    <p class="page-subtitle">
      {{
        fromAllWrongBook
          ? "从所有已学词书的错词中出题，错题会在本轮结束后继续强化。"
          : fromWrongBook
            ? "仅从当前词书错词本出题，错题会在本轮结束后继续强化。"
            : "每题四选一。错题会在本轮结束后自动强化，直至全部答对。"
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
        fromWrongBook && questions.length === 0
          ? "错词本为空，暂无需要复习的单词。"
          : "本轮测验完成。"
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
        <h2>{{ current.prompt }}</h2>
        <div v-if="mode === 'en_zh'" class="phonetic phonetic-strong">
          <span v-if="current.phonetic_uk">英 {{ current.phonetic_uk }}</span>
          <span v-if="current.phonetic_us" style="margin-left: 10px">美 {{ current.phonetic_us }}</span>
        </div>
      </div>

      <div class="option-list">
        <button
          v-for="option in current.options"
          :key="option.id"
          class="option-btn"
          :class="{
            selected: selectedId === option.id,
            correct: selectedId && option.id === current.correct_id,
            wrong:
              selectedId &&
              selectedId === option.id &&
              option.id !== current.correct_id,
          }"
          @click="choose(option.id)"
        >
          {{ option.text }}
        </button>
      </div>

      <div
        v-if="feedback"
        class="feedback"
        :class="isCorrect ? 'ok' : 'bad'"
      >
        <div>{{ feedback }}</div>
        <div v-if="showAnswerPhonetic" class="quiz-answer-detail">
          <strong v-if="mode === 'zh_en'">{{ answerEnglish }}</strong>
          <div class="phonetic">
            <span v-if="current.phonetic_uk">英 {{ current.phonetic_uk }}</span>
            <span v-if="current.phonetic_us" style="margin-left: 10px">
              美 {{ current.phonetic_us }}
            </span>
          </div>
        </div>
        <span v-if="autoCountdown > 0" class="book-meta">（{{ autoCountdown }} 秒后下一题）</span>
      </div>

      <div class="toolbar">
        <button class="btn btn-primary" :disabled="!selectedId" @click="nextQuestion">
          下一题
        </button>
        <span class="book-meta">{{ index + 1 }} / {{ questions.length }}</span>
      </div>
    </div>
  </div>
</template>
