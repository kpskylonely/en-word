import { ref, watch } from "vue";

export function useAutoAdvance(storageKey: string) {
  const enabled = ref(localStorage.getItem(storageKey) === "1");

  watch(enabled, (value) => {
    localStorage.setItem(storageKey, value ? "1" : "0");
  });

  return { autoAdvance: enabled };
}
