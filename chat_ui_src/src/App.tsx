import { useState } from 'react'
import type { FormEvent } from 'react'
import { fetchServerSentEvents, useChat } from '@tanstack/ai-react'
import './theme-tokens.css'
import './app.css'
import type { Lang } from './i18n'
import { t } from './i18n'
import { MessageView } from './MessageView'
import { useDocumentDataset } from './use-document-dataset'

// Same origin as the page itself (see api_server.py's StaticFiles mount at
// "/"), so no base URL is needed - and no CORS configuration either.
const connection = fetchServerSentEvents('/chat')

export default function App() {
  const lang = useDocumentDataset('lang', 'ja') as Lang
  const { messages, sendMessage, isLoading, stop, error } = useChat({ connection })
  const [input, setInput] = useState('')

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const trimmed = input.trim()
    if (trimmed === '') return
    sendMessage(trimmed)
    setInput('')
  }

  return (
    <div className="chat-app">
      <div className="chat-messages">
        {messages.length === 0 && <p className="chat-empty">{t(lang, 'emptyState')}</p>}
        {messages.map((message) => (
          <MessageView key={message.id} message={message} lang={lang} />
        ))}
        {error && <p className="chat-error">{error.message}</p>}
      </div>
      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          className="chat-input"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder={t(lang, 'inputPlaceholder')}
          disabled={isLoading}
        />
        {isLoading ? (
          <button type="button" className="chat-send" onClick={stop}>
            {t(lang, 'stop')}
          </button>
        ) : (
          <button type="submit" className="chat-send">
            {t(lang, 'send')}
          </button>
        )}
      </form>
    </div>
  )
}
