import { reactive, watch } from "vue";

export interface AppearanceSettings {
  stealthMode: boolean;
  stealthOpacity: number;
  alwaysOnTop: boolean;
}

const STORAGE_KEY = "enword_appearance_settings";

export const APPEARANCE_LIMITS = {
  opacityMin: 0.55,
  opacityMax: 0.95,
} as const;

export const DEFAULT_APPEARANCE: AppearanceSettings = {
  stealthMode: false,
  stealthOpacity: 0.88,
  alwaysOnTop: true,
};

function clampOpacity(value: number) {
  return Math.min(
    APPEARANCE_LIMITS.opacityMax,
    Math.max(APPEARANCE_LIMITS.opacityMin, Math.round(value * 100) / 100),
  );
}

function normalizeAppearance(raw: Partial<AppearanceSettings>): AppearanceSettings {
  return {
    stealthMode: Boolean(raw.stealthMode),
    stealthOpacity: clampOpacity(raw.stealthOpacity ?? DEFAULT_APPEARANCE.stealthOpacity),
    alwaysOnTop: raw.alwaysOnTop ?? DEFAULT_APPEARANCE.alwaysOnTop,
  };
}

function loadAppearance(): AppearanceSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_APPEARANCE };
    return normalizeAppearance(JSON.parse(raw) as Partial<AppearanceSettings>);
  } catch {
    return { ...DEFAULT_APPEARANCE };
  }
}

const appearance = reactive(loadAppearance());

watch(
  appearance,
  (value) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  },
  { deep: true },
);

export function useAppearanceSettings() {
  function resetAppearance() {
    Object.assign(appearance, DEFAULT_APPEARANCE);
  }

  function setStealthMode(enabled: boolean) {
    appearance.stealthMode = enabled;
  }

  function setStealthOpacity(value: number) {
    appearance.stealthOpacity = clampOpacity(value);
  }

  function setAlwaysOnTop(value: boolean) {
    appearance.alwaysOnTop = value;
  }

  return {
    appearance,
    resetAppearance,
    setStealthMode,
    setStealthOpacity,
    setAlwaysOnTop,
    DEFAULT_APPEARANCE,
    APPEARANCE_LIMITS,
  };
}
