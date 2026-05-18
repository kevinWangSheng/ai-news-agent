const CJK_RE = /[\u3400-\u9fff\uf900-\ufaff]/g;
const WORD_RE = /[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*/g;

export function estimateMinutes(content: string | null | undefined): number {
  const text = (content || "").replace(/```[\s\S]*?```/g, " ").replace(/[#>*_`\[\]()]/g, " ");
  if (!text.trim()) return 1;
  const chineseChars = text.match(CJK_RE)?.length ?? 0;
  const englishWords = text.replace(CJK_RE, " ").match(WORD_RE)?.length ?? 0;
  const minutes = chineseChars / 600 + englishWords / 250;
  return Math.max(1, Math.ceil(minutes));
}
