// Mirrors the shape of desktop_viewer/i18n.py: a plain dict-based lookup
// keyed by string id, switched by the `data-lang` attribute ChatPanel sets
// on <html> (see use-document-dataset.ts). Keep the two tables in sync by
// hand; there is no shared source of truth across the Python/TS boundary.
export type Lang = 'en' | 'ja'

const STRINGS = {
  inputPlaceholder: {
    en: 'Ask about the loaded IFC model...',
    ja: '読み込んだ IFC モデルについて質問...',
  },
  send: { en: 'Send', ja: '送信' },
  stop: { en: 'Stop', ja: '停止' },
  toolCallRunning: { en: 'Running {name}...', ja: '{name} を実行中...' },
  toolCallDone: { en: 'Done.', ja: '完了しました。' },
  toolCallError: { en: 'Tool call failed.', ja: 'ツール呼び出しに失敗しました。' },
  emptyState: {
    en: 'Ask the assistant to highlight elements in the 3D view.',
    ja: '3D ビューの要素をハイライトするようアシスタントに依頼できます。',
  },
} satisfies Record<string, Record<Lang, string>>

export function t(lang: Lang, key: keyof typeof STRINGS, vars?: Record<string, string>): string {
  const template = STRINGS[key][lang]
  if (!vars) return template
  return Object.entries(vars).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, value),
    template,
  )
}
