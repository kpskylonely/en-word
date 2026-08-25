import { onUnmounted, ref } from "vue";

const AUTO_DELAY_MS = 5000;

export function useAutoAdvanceTimer(onAdvance: () => void) {
  const autoCountdown = ref(0);
  let autoTimer: ReturnType<typeof setTimeout> | null = null;
  let countdownTimer: ReturnType<typeof setInterval> | null = null;

  function clearAutoTimer() {
    if (autoTimer) {
      clearTimeout(autoTimer);
      autoTimer = null;
    }
    if (countdownTimer) {
      clearInterval(countdownTimer);
      countdownTimer = null;
    }
    autoCountdown.value = 0;
  }

  function scheduleAutoNext(enabled: boolean) {
    clearAutoTimer();
    if (!enabled) return;

    autoCountdown.value = 5;
    countdownTimer = setInterval(() => {
      autoCountdown.value -= 1;
      if (autoCountdown.value <= 0 && countdownTimer) {
        clearInterval(countdownTimer);
        countdownTimer = null;
      }
    }, 1000);

    autoTimer = setTimeout(() => {
      onAdvance();
    }, AUTO_DELAY_MS);
  }

  onUnmounted(clearAutoTimer);

  return { autoCountdown, clearAutoTimer, scheduleAutoNext };
}
