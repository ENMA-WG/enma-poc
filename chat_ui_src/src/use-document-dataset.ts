import { useEffect, useState } from 'react'

/**
 * Tracks a `data-*` attribute on <html>. ChatPanel (the QWebEngineView host)
 * sets `data-theme` / `data-lang` via `runJavaScript` after this page has
 * already loaded, so a plain read at mount time would miss later changes -
 * a MutationObserver is required to react to them.
 */
export function useDocumentDataset(name: 'theme' | 'lang', fallback: string): string {
  const [value, setValue] = useState(() => document.documentElement.dataset[name] ?? fallback)

  useEffect(() => {
    const root = document.documentElement
    const observer = new MutationObserver(() => {
      setValue(root.dataset[name] ?? fallback)
    })
    observer.observe(root, { attributes: true, attributeFilter: [`data-${name}`] })
    return () => observer.disconnect()
  }, [name, fallback])

  return value
}
