import { reactive, watch } from "vue";

export interface StudySettings {
  flashcard: number;
  en_zh: number;
  zh_en: number;
  spelling: number;
  browse: number;
}

export const SETTINGS_LIMITS = {
  min: 5,
  max: 100,
  browseMax: 200,
} as const;

const STORAGE_KEY = "enword_study_settings";

export const DEFAULT_SETTINGS: StudySettings = {
  flashcard: 20,
  en_zh: 10,
  zh_en: 10,
  spelling: 10,
  browse: 30,
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, Math.round(value)));
}

function normalizeSettings(raw: Partial<StudySettings>): StudySettings {
  return {
    flashcard: clamp(raw.flashcard ?? DEFAULT_SETTINGS.flashcard, SETTINGS_LIMITS.min, SETTINGS_LIMITS.max),
    en_zh: clamp(raw.en_zh ?? DEFAULT_SETTINGS.en_zh, SETTINGS_LIMITS.min, SETTINGS_LIMITS.max),
    zh_en: clamp(raw.zh_en ?? DEFAULT_SETTINGS.zh_en, SETTINGS_LIMITS.min, SETTINGS_LIMITS.max),
    spelling: clamp(raw.spelling ?? DEFAULT_SETTINGS.spelling, SETTINGS_LIMITS.min, SETTINGS_LIMITS.max),
    browse: clamp(raw.browse ?? DEFAULT_SETTINGS.browse, SETTINGS_LIMITS.min, SETTINGS_LIMITS.browseMax),
  };
}

function loadSettings(): StudySettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_SETTINGS };
    return normalizeSettings(JSON.parse(raw) as Partial<StudySettings>);
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

const settings = reactive(loadSettings());

watch(
  settings,
  (value) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  },
  { deep: true },
);

export function useStudySettings() {
  function resetSettings() {
    Object.assign(settings, DEFAULT_SETTINGS);
  }

  function updateSetting<K extends keyof StudySettings>(key: K, value: number) {
    const limits =
      key === "browse"
        ? { min: SETTINGS_LIMITS.min, max: SETTINGS_LIMITS.browseMax }
        : { min: SETTINGS_LIMITS.min, max: SETTINGS_LIMITS.max };
    settings[key] = clamp(value, limits.min, limits.max);
  }

  return {
    settings,
    resetSettings,
    updateSetting,
    DEFAULT_SETTINGS,
    SETTINGS_LIMITS,
  };
}
