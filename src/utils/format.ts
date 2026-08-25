export function formatStudyDate(value: string | null | undefined) {
  if (!value) return "";
  const date = new Date(value.replace(" ", "T"));
  if (Number.isNaN(date.getTime())) return value.slice(0, 10);
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "numeric",
    day: "numeric",
  });
}

export function formatProgressRate(learned: number, total: number) {
  if (total <= 0) return 0;
  return Math.round((learned * 1000) / total) / 10;
}
