import { watch } from "vue";
import { useAppearanceSettings } from "../stores/appearance";

function invokeDesktopStealth(enabled: boolean, alwaysOnTop: boolean) {
  const api = window.pywebview?.api;
  if (!api?.set_stealth_mode) return;

  void api.set_stealth_mode(enabled, alwaysOnTop).catch(() => {
    /* desktop API unavailable */
  });
}

function applyAppearanceClasses(
  stealthMode: boolean,
  stealthOpacity: number,
  alwaysOnTop: boolean,
) {
  const root = document.documentElement;
  root.classList.toggle("stealth-mode", stealthMode);
  root.style.setProperty("--stealth-surface-opacity", String(stealthOpacity));

  if (window.pywebview?.api) {
    invokeDesktopStealth(stealthMode, alwaysOnTop);
    return;
  }

  window.addEventListener(
    "pywebviewready",
    () => invokeDesktopStealth(stealthMode, alwaysOnTop),
    { once: true },
  );
}

export function useAppearance() {
  const { appearance } = useAppearanceSettings();

  watch(
    appearance,
    (value) => {
      applyAppearanceClasses(value.stealthMode, value.stealthOpacity, value.alwaysOnTop);
    },
    { immediate: true, deep: true },
  );

  return { appearance };
}
