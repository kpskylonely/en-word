<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
import { useAppearance } from "./composables/useAppearance";
import {
  stealthExitShortcutLabel,
  useStealthShortcut,
} from "./composables/useStealthShortcut";
import { useAppearanceSettings } from "./stores/appearance";
import { useBookStore } from "./stores/book";

const { currentBook } = useBookStore();
const { appearance } = useAppearance();
const { setStealthMode } = useAppearanceSettings();

useStealthShortcut();

const stealthExitHint = stealthExitShortcutLabel();
</script>

<template>
  <div class="app-shell" :class="{ 'stealth-shell': appearance.stealthMode }">
    <header v-if="!appearance.stealthMode" class="topbar">
      <div class="topbar-title">离线背单词</div>
      <nav class="topbar-nav">
        <RouterLink to="/">选书</RouterLink>
        <RouterLink to="/study">学习</RouterLink>
        <RouterLink to="/stats">统计</RouterLink>
        <RouterLink to="/browse">浏览</RouterLink>
        <RouterLink to="/wrong">总错词本</RouterLink>
        <RouterLink to="/settings">设置</RouterLink>
      </nav>
    </header>

    <div v-if="appearance.stealthMode" class="stealth-float">
      <span class="stealth-float-hint">{{ stealthExitHint }}</span>
      <nav class="stealth-float-nav">
        <RouterLink to="/">选书</RouterLink>
        <RouterLink to="/study">学习</RouterLink>
        <RouterLink to="/flashcard">闪卡</RouterLink>
        <RouterLink to="/settings">设置</RouterLink>
      </nav>
      <button class="stealth-exit" type="button" @click="setStealthMode(false)">退出</button>
    </div>

    <main :class="{ 'stealth-main': appearance.stealthMode }">
      <div
        v-if="currentBook && !appearance.stealthMode"
        class="page-subtitle page"
        style="padding-bottom: 0"
      >
        当前词书：{{ currentBook.name }}（{{
          currentBook.direct_word_count || currentBook.word_count
        }}
        词）
      </div>
      <RouterView />
    </main>
  </div>
</template>
