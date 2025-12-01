import { createFileRoute } from '@tanstack/react-router'
import { useCallback, useEffect, useRef, useState } from 'react'
import {
  AlertCircle,
  Bot,
  Loader2,
  RefreshCw,
  Send,
  Sparkles,
  User,
} from 'lucide-react'
import type { SuggestedPromptCategory } from '@/lib/api/types'
import { aiService } from '@/lib/api/services/ai'

export const Route = createFileRoute('/_authenticated/ai-assistant')({
  component: AIAssistantPage,
})

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  data?: Record<string, unknown>
  followUpQuestions?: Array<string>
  isError?: boolean
}

function AIAssistantPage() {
  const [messages, setMessages] = useState<Array<Message>>([
    {
      id: '1',
      role: 'assistant',
      content:
        "Hello! I'm your AI HR Assistant. I can help you with HR-related queries such as:\n\n• Leave policies and balances\n• Employee information\n• Attendance queries\n• Payroll questions\n• HR policies and procedures\n\nHow can I assist you today?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()
  const [suggestedPrompts, setSuggestedPrompts] = useState<
    Array<SuggestedPromptCategory>
  >([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    const loadSuggestedPrompts = async () => {
      try {
        const response = await aiService.getSuggestedPrompts()
        setSuggestedPrompts(response.prompts)
      } catch (error) {
        console.error('Failed to load suggested prompts:', error)
      }
    }
    loadSuggestedPrompts()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentInput = input.trim()
    setInput('')
    setIsLoading(true)

    try {
      const response = await aiService.chat(currentInput, conversationId)

      if (response.conversation_id) {
        setConversationId(response.conversation_id)
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        data: response.data,
        followUpQuestions: response.follow_up_questions,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content:
          error instanceof Error
            ? `I encountered an error: ${error.message}. Please try again.`
            : 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        isError: true,
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleFollowUpClick = (question: string) => {
    setInput(question)
  }

  const handleNewConversation = () => {
    setMessages([
      {
        id: '1',
        role: 'assistant',
        content:
          "Hello! I'm your AI HR Assistant. I can help you with HR-related queries such as:\n\n• Leave policies and balances\n• Employee information\n• Attendance queries\n• Payroll questions\n• HR policies and procedures\n\nHow can I assist you today?",
        timestamp: new Date(),
      },
    ])
    setConversationId(undefined)
    setInput('')
  }

  const flatSuggestions = suggestedPrompts
    .flatMap((cat) => cat.suggestions)
    .slice(0, 4)

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-linear-to-br from-cyan-500 to-purple-500 flex items-center justify-center">
            <Bot className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              AI HR Assistant
            </h1>
            <p className="text-muted-foreground text-sm">
              Powered by AI to help with your HR queries
            </p>
          </div>
        </div>
        <button
          onClick={handleNewConversation}
          className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
          title="Start new conversation"
        >
          <RefreshCw className="w-4 h-4" />
          New Chat
        </button>
      </div>

      <div className="flex-1 bg-card rounded-xl border border-border flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : ''}`}
            >
              {message.role === 'assistant' && (
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                    message.isError
                      ? 'bg-destructive/20'
                      : 'bg-linear-to-br from-cyan-500 to-purple-500'
                  }`}
                >
                  {message.isError ? (
                    <AlertCircle className="w-5 h-5 text-destructive" />
                  ) : (
                    <Bot className="w-5 h-5 text-white" />
                  )}
                </div>
              )}
              <div className="max-w-[80%] space-y-2">
                <div
                  className={`rounded-xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : message.isError
                        ? 'bg-destructive/10 text-foreground border border-destructive/20'
                        : 'bg-muted text-foreground'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  <p
                    className={`text-xs mt-2 ${
                      message.role === 'user'
                        ? 'text-primary-foreground/70'
                        : 'text-muted-foreground'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>

                {/* Follow-up questions */}
                {message.followUpQuestions &&
                  message.followUpQuestions.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {message.followUpQuestions.map((question, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleFollowUpClick(question)}
                          className="px-3 py-1.5 bg-accent hover:bg-accent/80 text-accent-foreground text-sm rounded-full transition-colors"
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  )}
              </div>
              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center shrink-0">
                  <User className="w-5 h-5 text-secondary-foreground" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-linear-to-br from-cyan-500 to-purple-500 flex items-center justify-center shrink-0">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-muted rounded-xl px-4 py-3">
                <Loader2 className="w-5 h-5 text-primary animate-spin" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {messages.length === 1 && flatSuggestions.length > 0 && (
          <div className="px-4 pb-4">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-sm text-muted-foreground">
                Suggested questions
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {flatSuggestions.map((question) => (
                <button
                  key={question}
                  onClick={() => setInput(question)}
                  className="px-3 py-1.5 bg-accent hover:bg-accent/80 text-accent-foreground text-sm rounded-full transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-4 border-t border-border">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything about HR..."
              className="flex-1 px-4 py-3 bg-background border border-input rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-4 py-3 bg-primary hover:bg-primary/90 disabled:bg-muted disabled:cursor-not-allowed text-primary-foreground rounded-xl transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
