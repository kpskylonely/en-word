import { onMounted, onUnmounted } from "vue";
import { useAppearanceSettings } from "../stores/appearance";

export const STEALTH_EXIT_SHORTCUT_MAC = "Esc 或 ⌘⇧E";
export const STEALTH_EXIT_SHORTCUT_WIN = "Esc 或 Ctrl+Shift+E";

function isEditableTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || target.isContentEditable;
}

export function stealthExitShortcutLabel() {
  const isMac = /Mac/i.test(navigator.platform);
  return isMac ? STEALTH_EXIT_SHORTCUT_MAC : STEALTH_EXIT_SHORTCUT_WIN;
}

export function useStealthShortcut() {
  const { appearance, setStealthMode } = useAppearanceSettings();

  function onKeyDown(event: KeyboardEvent) {
    if (!appearance.stealthMode) return;

    const modifier = event.metaKey || event.ctrlKey;
    if (modifier && event.shiftKey && event.key.toLowerCase() === "e") {
      event.preventDefault();
      setStealthMode(false);
      return;
    }

    if (event.key === "Escape" && !isEditableTarget(event.target)) {
      event.preventDefault();
      setStealthMode(false);
    }
  }

  onMounted(() => window.addEventListener("keydown", onKeyDown));
  onUnmounted(() => window.removeEventListener("keydown", onKeyDown));
}
