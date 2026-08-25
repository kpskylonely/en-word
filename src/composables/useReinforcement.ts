import { computed, ref, type Ref } from "vue";

type ReinforceItem = { word_id?: string; id?: string; book_id?: string };

function itemKey(item: ReinforceItem) {
  const id = item.word_id ?? item.id ?? "";
  return item.book_id ? `${item.book_id}:${id}` : id;
}

export function useReinforcement<T extends ReinforceItem>() {
  const phase = ref<"main" | "reinforce">("main");
  const wrongItems = ref<Record<string, T>>({});

  const reinforceCount = computed(() => Object.keys(wrongItems.value).length);
  const inReinforce = computed(() => phase.value === "reinforce");

  function markWrong(item: T) {
    wrongItems.value = { ...wrongItems.value, [itemKey(item)]: item };
  }

  function markCorrect(item: T) {
    if (phase.value === "reinforce") {
      const next = { ...wrongItems.value };
      delete next[itemKey(item)];
      wrongItems.value = next;
    }
  }

  function getReinforceQueue(): T[] {
    return Object.values(wrongItems.value);
  }

  function hasReinforce() {
    return Object.keys(wrongItems.value).length > 0;
  }

  function startReinforce() {
    phase.value = "reinforce";
  }

  function resetReinforcement() {
    phase.value = "main";
    wrongItems.value = {};
  }

  return {
    phase,
    reinforceCount,
    inReinforce,
    markWrong,
    markCorrect,
    getReinforceQueue,
    hasReinforce,
    startReinforce,
    resetReinforcement,
  };
}

export function advanceWithReinforcement<T extends ReinforceItem>(options: {
  index: Ref<number>;
  queue: Ref<T[]>;
  phase: Ref<"main" | "reinforce">;
  hasReinforce: () => boolean;
  getReinforceQueue: () => T[];
  startReinforce: () => void;
  onFinished: () => void;
}) {
  const { index, queue, phase, hasReinforce, getReinforceQueue, startReinforce, onFinished } =
    options;

  if (index.value < queue.value.length - 1) {
    index.value += 1;
    return;
  }

  if (phase.value === "main" && hasReinforce()) {
    startReinforce();
    queue.value = getReinforceQueue();
    index.value = 0;
    return;
  }

  if (phase.value === "reinforce" && hasReinforce()) {
    queue.value = getReinforceQueue();
    index.value = 0;
    return;
  }

  onFinished();
}
