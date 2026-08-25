import { watch } from "vue";
import { useAppearanceSettings } from "../stores/appearance";

function markDesktopShell() {
  document.documentElement.classList.add("desktop-shell");
}

function invokeDesktopStealth(enabled: boolean, alwaysOnTop: boolean) {
  const api = window.pywebview?.api;
  if (!api?.set_stealth_mode) return;

  const apply = () => {
    void api.set_stealth_mode(enabled, alwaysOnTop).catch(() => {
      /* desktop API unavailable */
    });
  };

  apply();
  window.setTimeout(apply, 120);
  window.setTimeout(apply, 400);
}

function initDesktopWindow(stealthMode: boolean) {
  const api = window.pywebview?.api;
  if (!api?.init_desktop_window) return;

  const apply = () => {
    void api.init_desktop_window(stealthMode).catch(() => {
      /* desktop API unavailable */
    });
  };

  apply();
  window.setTimeout(apply, 120);
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
    markDesktopShell();
    initDesktopWindow(stealthMode);
    invokeDesktopStealth(stealthMode, alwaysOnTop);
    return;
  }

  window.addEventListener(
    "pywebviewready",
    () => {
      markDesktopShell();
      initDesktopWindow(stealthMode);
      invokeDesktopStealth(stealthMode, alwaysOnTop);
    },
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
