<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
import { useAppearance } from "./composables/useAppearance";
import { useAppearanceSettings } from "./stores/appearance";
import { useBookStore } from "./stores/book";

const { currentBook } = useBookStore();
const { appearance } = useAppearance();
const { setStealthMode } = useAppearanceSettings();
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

    <div v-if="appearance.stealthMode" class="stealth-bar">
      <nav class="stealth-nav">
        <RouterLink to="/study">学习</RouterLink>
        <RouterLink to="/flashcard">闪卡</RouterLink>
        <RouterLink to="/quiz/en_zh">英中</RouterLink>
        <RouterLink to="/quiz/zh_en">中英</RouterLink>
        <RouterLink to="/settings">设置</RouterLink>
      </nav>
      <button class="stealth-exit" type="button" @click="setStealthMode(false)">退出透明</button>
    </div>

    <main>
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
