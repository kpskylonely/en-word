<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { api } from "../api";
import { useAppearanceSettings } from "../stores/appearance";
import { useStudySettings } from "../stores/settings";
import type { BookStudyStats } from "../types";

const { settings, resetSettings, updateSetting, DEFAULT_SETTINGS, SETTINGS_LIMITS } =
  useStudySettings();
const {
  appearance,
  setStealthMode,
  setStealthOpacity,
  setAlwaysOnTop,
  APPEARANCE_LIMITS,
} = useAppearanceSettings();

const studiedBooks = ref<BookStudyStats[]>([]);
const selectedResetBookId = ref("");
const progressLoading = ref(true);
const resetting = ref(false);
const resetMessage = ref("");
const resetError = ref("");

const modeItems = [
  {
    key: "flashcard" as const,
    title: "闪卡复习",
    desc: "每轮复习的单词数量",
    max: SETTINGS_LIMITS.max,
  },
  {
    key: "en_zh" as const,
    title: "英 → 中 选择",
    desc: "每轮测验的题目数量",
    max: SETTINGS_LIMITS.max,
  },
  {
    key: "zh_en" as const,
    title: "中 → 英 选择",
    desc: "每轮测验的题目数量",
    max: SETTINGS_LIMITS.max,
  },
  {
    key: "spelling" as const,
    title: "键盘拼写",
    desc: "每轮拼写的题目数量",
    max: SETTINGS_LIMITS.max,
  },
  {
    key: "browse" as const,
    title: "浏览词表",
    desc: "每次加载显示的单词数量",
    max: SETTINGS_LIMITS.browseMax,
  },
];

function onInput(key: (typeof modeItems)[number]["key"], event: Event) {
  const value = Number((event.target as HTMLInputElement).value);
  if (Number.isNaN(value)) return;
  updateSetting(key, value);
}
function onOpacityInput(event: Event) {
  const value = Number((event.target as HTMLInputElement).value);
  if (Number.isNaN(value)) return;
  setStealthOpacity(value);
}

async function loadStudiedBooks() {
  progressLoading.value = true;
  resetError.value = "";
  try {
    studiedBooks.value = await api.getStudiedBooksStats();
    if (
      selectedResetBookId.value &&
      !studiedBooks.value.some((book) => book.id === selectedResetBookId.value)
    ) {
      selectedResetBookId.value = "";
    }
    if (!selectedResetBookId.value && studiedBooks.value.length > 0) {
      selectedResetBookId.value = studiedBooks.value[0].id;
    }
  } catch (e) {
    resetError.value = String(e);
  } finally {
    progressLoading.value = false;
  }
}

function selectedBookName() {
  return studiedBooks.value.find((book) => book.id === selectedResetBookId.value)?.name ?? "该词书";
}

async function clearBookProgress() {
  if (!selectedResetBookId.value || resetting.value) return;
  if (
    !window.confirm(
      `确定清除「${selectedBookName()}」的全部学习记录吗？\n\n包括复习进度、错词本和统计历史。此操作不可恢复。`,
    )
  ) {
    return;
  }
  resetting.value = true;
  resetMessage.value = "";
  resetError.value = "";
  try {
    await api.resetBookProgress(selectedResetBookId.value);
    resetMessage.value = `已清除「${selectedBookName()}」的学习记录。`;
    await loadStudiedBooks();
  } catch (e) {
    resetError.value = String(e);
  } finally {
    resetting.value = false;
  }
}

async function clearAllProgress() {
  if (resetting.value) return;
  if (
    !window.confirm(
      "确定清除所有词书的学习记录吗？\n\n包括复习进度、错词本和统计历史。此操作不可恢复。",
    )
  ) {
    return;
  }
  resetting.value = true;
  resetMessage.value = "";
  resetError.value = "";
  try {
    await api.resetAllProgress();
    resetMessage.value = "已清除全部学习记录。";
    selectedResetBookId.value = "";
    await loadStudiedBooks();
  } catch (e) {
    resetError.value = String(e);
  } finally {
    resetting.value = false;
  }
}

onMounted(loadStudiedBooks);
</script>

<template>
  <div class="page">
    <h1 class="page-title">学习设置</h1>
    <p class="page-subtitle">学习词量与界面显示选项，修改后自动保存。</p>

    <h2 class="section-title">透明摸鱼模式</h2>
    <div class="card settings-list appearance-panel">
      <div class="setting-item">
        <div class="setting-info">
          <strong>启用透明模式</strong>
          <span class="book-meta">
            界面伪装成 Word 文档风格，窗口半透明，方便叠在 Word 上摸鱼。
          </span>
        </div>
        <label class="setting-toggle">
          <input
            :checked="appearance.stealthMode"
            type="checkbox"
            @change="setStealthMode(($event.target as HTMLInputElement).checked)"
          />
          <span>{{ appearance.stealthMode ? "已开启" : "已关闭" }}</span>
        </label>
      </div>

      <div class="setting-item">
        <div class="setting-info">
          <strong>界面透明度</strong>
          <span class="book-meta">
            {{ Math.round(appearance.stealthOpacity * 100) }}%（数值越低越透明）
          </span>
        </div>
        <input
          class="opacity-slider"
          type="range"
          :min="APPEARANCE_LIMITS.opacityMin"
          :max="APPEARANCE_LIMITS.opacityMax"
          step="0.01"
          :value="appearance.stealthOpacity"
          @input="onOpacityInput"
        />
      </div>

      <div class="setting-item">
        <div class="setting-info">
          <strong>窗口置顶</strong>
          <span class="book-meta">透明模式开启时，窗口保持在最前（桌面版有效）</span>
        </div>
        <label class="setting-toggle">
          <input
            :checked="appearance.alwaysOnTop"
            type="checkbox"
            @change="setAlwaysOnTop(($event.target as HTMLInputElement).checked)"
          />
          <span>{{ appearance.alwaysOnTop ? "置顶" : "不置顶" }}</span>
        </label>
      </div>
    </div>

    <p class="book-meta appearance-note">
      透明窗口与置顶需使用桌面版（npm start）。浏览器开发模式仅 UI 半透明。
    </p>

    <h2 class="section-title">各模式词量</h2>
    <div class="card settings-list">
      <div v-for="item in modeItems" :key="item.key" class="setting-item">
        <div class="setting-info">
          <strong>{{ item.title }}</strong>
          <span class="book-meta">{{ item.desc }}（{{ SETTINGS_LIMITS.min }}-{{ item.max }}）</span>
        </div>
        <div class="setting-control">
          <input
            class="input-field setting-input"
            type="number"
            :min="SETTINGS_LIMITS.min"
            :max="item.max"
            :value="settings[item.key]"
            @change="onInput(item.key, $event)"
          />
          <span class="book-meta">词</span>
        </div>
      </div>
    </div>

    <h2 class="section-title">学习数据</h2>
    <div class="card settings-list">
      <p class="book-meta progress-reset-desc">
        清除学习记录会重置复习进度、错词本和统计数据，词库内容不会被删除。
      </p>

      <div v-if="progressLoading" class="empty">加载已学词书中...</div>
      <template v-else>
        <div class="setting-item">
          <div class="setting-info">
            <strong>清除指定词书</strong>
            <span class="book-meta">仅清除所选词书的学习记录</span>
          </div>
          <div class="setting-control progress-reset-control">
            <select
              v-model="selectedResetBookId"
              class="input-field progress-reset-select"
              :disabled="studiedBooks.length === 0 || resetting"
            >
              <option v-if="studiedBooks.length === 0" value="">暂无已学词书</option>
              <option v-for="book in studiedBooks" :key="book.id" :value="book.id">
                {{ book.name }}
              </option>
            </select>
            <button
              class="btn btn-danger btn-sm"
              :disabled="!selectedResetBookId || resetting"
              @click="clearBookProgress"
            >
              清除该词书
            </button>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <strong>清除全部记录</strong>
            <span class="book-meta">一键清空所有词书的学习数据</span>
          </div>
          <button
            class="btn btn-danger btn-sm"
            :disabled="studiedBooks.length === 0 || resetting"
            @click="clearAllProgress"
          >
            清除全部
          </button>
        </div>
      </template>

      <p v-if="resetMessage" class="book-meta progress-reset-msg">{{ resetMessage }}</p>
      <p v-if="resetError" class="book-meta progress-reset-error">{{ resetError }}</p>
    </div>

    <div class="toolbar">
      <button class="btn" @click="resetSettings">恢复默认</button>
      <RouterLink class="btn btn-primary" to="/study">返回学习</RouterLink>
    </div>

    <p class="book-meta" style="margin-top: 12px">
      默认：闪卡 {{ DEFAULT_SETTINGS.flashcard }} · 选择题 {{ DEFAULT_SETTINGS.en_zh }} · 拼写
      {{ DEFAULT_SETTINGS.spelling }} · 浏览 {{ DEFAULT_SETTINGS.browse }}
    </p>
  </div>
</template>
