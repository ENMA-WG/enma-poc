import type { UIMessage } from '@tanstack/ai-react'
import type { Lang } from './i18n'
import { t } from './i18n'

interface MessageViewProps {
  message: UIMessage
  lang: Lang
}

export function MessageView({ message, lang }: MessageViewProps) {
  return (
    <div className={`chat-message chat-message--${message.role}`}>
      {message.parts.map((part, index) => {
        if (part.type === 'text') {
          return <p key={index}>{part.content}</p>
        }
        if (part.type === 'tool-call') {
          return (
            <div key={index} className="chat-tool-status">
              {t(lang, 'toolCallRunning', { name: part.name })}
            </div>
          )
        }
        if (part.type === 'tool-result') {
          return (
            <div key={index} className="chat-tool-status">
              {part.state === 'error' ? t(lang, 'toolCallError') : t(lang, 'toolCallDone')}
            </div>
          )
        }
        // Other part types (thinking, image, structured output, ...) are not
        // produced by this app's backend today; nothing to render for them.
        return null
      })}
    </div>
  )
}
