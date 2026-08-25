<script setup lang="ts">
defineProps<{
  label: string;
}>();
</script>

<template>
  <span class="book-tag" :class="{ completed: label === '已学完' }">
    {{ label }}
  </span>
</template>
