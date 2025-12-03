import { createFileRoute } from '@tanstack/react-router'
import { useCallback, useEffect, useRef, useState } from 'react'
import {
  AlertCircle,
  Bot,
  Check,
  ChevronDown,
  FileText,
  FolderOpen,
  Loader2,
  MessageSquare,
  RefreshCw,
  Search,
  Send,
  Trash2,
  Upload,
  User,
  X,
  Zap,
} from 'lucide-react'
import type {
  PolicyCategory,
  PolicyChatResponse,
  PolicySummary,
} from '@/lib/api/types'
import { policyChatService, policyService } from '@/lib/api'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export const Route = createFileRoute('/_authenticated/policies')({
  component: PoliciesPage,
})

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Array<{
    policy_name: string
    category: string
    relevance: number
  }>
  followUpQuestions?: Array<string>
  isError?: boolean
}

type ViewMode = 'list' | 'chat'

const POLICY_CATEGORIES = [
  'general',
  'leave',
  'attendance',
  'conduct',
  'benefits',
  'compensation',
  'safety',
  'it',
  'travel',
  'expense',
  'other',
]

function PoliciesPage() {
  // View state
  const [viewMode, setViewMode] = useState<ViewMode>('list')

  // Policy list state
  const [policies, setPolicies] = useState<Array<PolicySummary>>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')

  // Upload dialog state
  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadName, setUploadName] = useState('')
  const [uploadCategory, setUploadCategory] = useState('general')
  const [uploadDescription, setUploadDescription] = useState('')
  const [uploadVersion, setUploadVersion] = useState('1.0')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')

  // Indexing state
  const [indexingPolicyId, setIndexingPolicyId] = useState<string | null>(null)
  const [isIndexingAll, setIsIndexingAll] = useState(false)

  // Chat state
  const [messages, setMessages] = useState<Array<Message>>([
    {
      id: '1',
      role: 'assistant',
      content:
        "Hello! I'm your Policy Assistant. I can help you find information in your organization's policies.\n\nAsk me questions like:\n• What is the leave policy for sick days?\n• How do I request time off?\n• What are the attendance requirements?\n• Tell me about employee benefits.",
      timestamp: new Date(),
    },
  ])
  const [chatInput, setChatInput] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    fetchPolicies()
  }, [selectedCategory])

  const fetchPolicies = async () => {
    setIsLoading(true)
    try {
      const response = await policyService.list({
        category: selectedCategory
          ? (selectedCategory as PolicyCategory)
          : undefined,
        includeArchived: false,
      })
      setPolicies(response.items)
    } catch (err) {
      setError('Failed to load policies')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadFile(file)
      if (!uploadName) {
        setUploadName(file.name.replace(/\.[^.]+$/, ''))
      }
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    setUploadError('')

    if (!uploadFile) {
      setUploadError('Please select a file')
      return
    }
    if (!uploadName.trim()) {
      setUploadError('Please enter a policy name')
      return
    }

    setIsUploading(true)
    try {
      await policyService.upload(uploadFile, {
        name: uploadName.trim(),
        category: uploadCategory,
        description: uploadDescription.trim() || undefined,
        version: uploadVersion.trim() || undefined,
      })

      setIsUploadOpen(false)
      resetUploadForm()
      fetchPolicies()
    } catch (err) {
      setUploadError(
        err instanceof Error ? err.message : 'Failed to upload policy',
      )
    } finally {
      setIsUploading(false)
    }
  }

  const resetUploadForm = () => {
    setUploadFile(null)
    setUploadName('')
    setUploadCategory('general')
    setUploadDescription('')
    setUploadVersion('1.0')
    setUploadError('')
  }

  const handleIndex = async (policyId: string) => {
    setIndexingPolicyId(policyId)
    try {
      await policyService.index(policyId)
      fetchPolicies()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to index policy')
    } finally {
      setIndexingPolicyId(null)
    }
  }

  const handleIndexAll = async () => {
    setIsIndexingAll(true)
    try {
      await policyService.indexAll()
      fetchPolicies()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to index all policies',
      )
    } finally {
      setIsIndexingAll(false)
    }
  }

  const handleDelete = async (policyId: string) => {
    if (!confirm('Are you sure you want to delete this policy?')) return

    try {
      await policyService.delete(policyId)
      fetchPolicies()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete policy')
    }
  }

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim() || isChatLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentInput = chatInput.trim()
    setChatInput('')
    setIsChatLoading(true)

    try {
      const response: PolicyChatResponse = await policyChatService.chat(
        currentInput,
        conversationId,
      )

      if (response.conversation_id) {
        setConversationId(response.conversation_id)
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
        followUpQuestions: response.follow_up_questions,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      console.error('Error:', err)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content:
          err instanceof Error
            ? `I encountered an error: ${err.message}. Please try again.`
            : 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        isError: true,
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsChatLoading(false)
    }
  }

  const handleFollowUpClick = (question: string) => {
    setChatInput(question)
  }

  const handleNewConversation = () => {
    setMessages([
      {
        id: '1',
        role: 'assistant',
        content:
          "Hello! I'm your Policy Assistant. I can help you find information in your organization's policies.\n\nAsk me questions like:\n• What is the leave policy for sick days?\n• How do I request time off?\n• What are the attendance requirements?\n• Tell me about employee benefits.",
        timestamp: new Date(),
      },
    ])
    setConversationId(undefined)
    setChatInput('')
  }

  const filteredPolicies = policies.filter(
    (policy) =>
      policy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      policy.category.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      leave: 'bg-blue-500/10 text-blue-400',
      attendance: 'bg-green-500/10 text-green-400',
      conduct: 'bg-purple-500/10 text-purple-400',
      benefits: 'bg-cyan-500/10 text-cyan-400',
      compensation: 'bg-yellow-500/10 text-yellow-400',
      safety: 'bg-red-500/10 text-red-400',
      it: 'bg-indigo-500/10 text-indigo-400',
      travel: 'bg-orange-500/10 text-orange-400',
      expense: 'bg-amber-500/10 text-amber-400',
      general: 'bg-slate-500/10 text-slate-400',
    }
    return colors[category] || 'bg-slate-500/10 text-slate-400'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground">
            Policies
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage organization policies and ask questions using AI
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-muted rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'list'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <FolderOpen className="w-4 h-4 inline-block mr-1.5" />
              Manage
            </button>
            <button
              onClick={() => setViewMode('chat')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'chat'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <MessageSquare className="w-4 h-4 inline-block mr-1.5" />
              Ask AI
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive border border-destructive/20 rounded-lg p-4 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
          <button
            onClick={() => setError('')}
            className="ml-auto hover:bg-destructive/20 p-1 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {viewMode === 'list' ? (
        /* Policy List View */
        <div className="space-y-4">
          {/* Actions Bar */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search policies..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="min-w-[140px]">
                  {selectedCategory || 'All Categories'}
                  <ChevronDown className="w-4 h-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setSelectedCategory('')}>
                  All Categories
                </DropdownMenuItem>
                {POLICY_CATEGORIES.map((cat) => (
                  <DropdownMenuItem
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                  >
                    {cat
                      .replace('_', ' ')
                      .replace(/\b\w/g, (c) => c.toUpperCase())}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            <Button
              variant="outline"
              onClick={handleIndexAll}
              disabled={isIndexingAll || policies.length === 0}
            >
              {isIndexingAll ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Zap className="w-4 h-4 mr-2" />
              )}
              Index All
            </Button>

            <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Policy
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>Upload Policy Document</DialogTitle>
                  <DialogDescription>
                    Upload a policy document (PDF, TXT, MD) to make it
                    searchable by AI.
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleUpload} className="space-y-4">
                  {uploadError && (
                    <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-lg">
                      {uploadError}
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="file">Policy File</Label>
                    <Input
                      id="file"
                      type="file"
                      accept=".pdf,.txt,.md"
                      onChange={handleFileChange}
                      className="cursor-pointer"
                    />
                    {uploadFile && (
                      <p className="text-sm text-muted-foreground">
                        Selected: {uploadFile.name} (
                        {(uploadFile.size / 1024).toFixed(1)} KB)
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="name">Policy Name</Label>
                    <Input
                      id="name"
                      type="text"
                      placeholder="e.g., Leave Policy"
                      value={uploadName}
                      onChange={(e) => setUploadName(e.target.value)}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="category">Category</Label>
                      <select
                        id="category"
                        value={uploadCategory}
                        onChange={(e) => setUploadCategory(e.target.value)}
                        className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm"
                      >
                        {POLICY_CATEGORIES.map((cat) => (
                          <option key={cat} value={cat}>
                            {cat
                              .replace('_', ' ')
                              .replace(/\b\w/g, (c) => c.toUpperCase())}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="version">Version</Label>
                      <Input
                        id="version"
                        type="text"
                        placeholder="1.0"
                        value={uploadVersion}
                        onChange={(e) => setUploadVersion(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="description">
                      Description{' '}
                      <span className="text-muted-foreground">(optional)</span>
                    </Label>
                    <textarea
                      id="description"
                      placeholder="Brief description of this policy..."
                      value={uploadDescription}
                      onChange={(e) => setUploadDescription(e.target.value)}
                      className="w-full min-h-20 px-3 py-2 rounded-md border border-input bg-background text-sm resize-none"
                    />
                  </div>

                  <div className="flex justify-end gap-3 pt-2">
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => {
                        setIsUploadOpen(false)
                        resetUploadForm()
                      }}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" disabled={isUploading}>
                      {isUploading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4 mr-2" />
                          Upload
                        </>
                      )}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {/* Policy Cards */}
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : filteredPolicies.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <FileText className="w-12 h-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No policies found</h3>
                <p className="text-muted-foreground text-center max-w-sm mb-4">
                  {searchQuery || selectedCategory
                    ? 'Try adjusting your search or filter.'
                    : 'Upload your first policy document to get started.'}
                </p>
                <Button onClick={() => setIsUploadOpen(true)}>
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Policy
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredPolicies.map((policy) => (
                <Card
                  key={policy.id}
                  className="hover:border-primary/50 transition-colors"
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1 flex-1 min-w-0">
                        <CardTitle className="text-base truncate">
                          {policy.name}
                        </CardTitle>
                        <CardDescription className="truncate">
                          {policy.file_type.toUpperCase()} • v{policy.version}
                        </CardDescription>
                      </div>
                      <span
                        className={`px-2 py-0.5 text-xs font-medium rounded-full shrink-0 ml-2 ${getCategoryColor(policy.category)}`}
                      >
                        {policy.category.replace('_', ' ')}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-4 text-muted-foreground">
                        <span
                          className={`px-2 py-0.5 text-xs rounded-full ${
                            policy.status === 'active'
                              ? 'bg-green-500/10 text-green-500'
                              : policy.status === 'draft'
                                ? 'bg-yellow-500/10 text-yellow-500'
                                : 'bg-slate-500/10 text-slate-400'
                          }`}
                        >
                          {policy.status}
                        </span>
                        {policy.is_indexed ? (
                          <span className="flex items-center gap-1 text-green-500">
                            <Check className="w-3 h-3" />
                            Indexed
                          </span>
                        ) : (
                          <span className="text-yellow-500">Not indexed</span>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleIndex(policy.id)}
                          disabled={indexingPolicyId === policy.id}
                          title={
                            policy.is_indexed
                              ? 'Re-index'
                              : 'Index for AI search'
                          }
                        >
                          {indexingPolicyId === policy.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Zap className="w-4 h-4" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(policy.id)}
                          className="text-destructive hover:text-destructive"
                          title="Delete policy"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Chat View */
        <div className="h-[calc(100vh-14rem)] flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-linear-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">
                  Policy Assistant
                </h2>
                <p className="text-sm text-muted-foreground">
                  Ask questions about your organization's policies
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
                          : 'bg-linear-to-br from-purple-500 to-pink-500'
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

                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {message.sources.map((source, idx) => (
                          <span
                            key={idx}
                            className={`px-2 py-1 text-xs rounded-full ${getCategoryColor(source.category)}`}
                            title={`Relevance: ${(source.relevance * 100).toFixed(0)}%`}
                          >
                            📄 {source.policy_name}
                          </span>
                        ))}
                      </div>
                    )}

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

              {isChatLoading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-lg bg-linear-to-br from-purple-500 to-pink-500 flex items-center justify-center shrink-0">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div className="bg-muted rounded-xl px-4 py-3">
                    <Loader2 className="w-5 h-5 text-primary animate-spin" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Suggested Questions for first message */}
            {messages.length === 1 && (
              <div className="px-4 pb-4">
                <div className="flex flex-wrap gap-2">
                  {[
                    'What is the leave policy?',
                    'How many sick days do I get?',
                    'What are the office hours?',
                    'Explain the code of conduct',
                  ].map((question) => (
                    <button
                      key={question}
                      onClick={() => setChatInput(question)}
                      className="px-3 py-1.5 bg-accent hover:bg-accent/80 text-accent-foreground text-sm rounded-full transition-colors"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <form
              onSubmit={handleChatSubmit}
              className="p-4 border-t border-border"
            >
              <div className="flex gap-3">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask about policies..."
                  className="flex-1 px-4 py-3 bg-background border border-input rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                />
                <button
                  type="submit"
                  disabled={!chatInput.trim() || isChatLoading}
                  className="px-4 py-3 bg-primary hover:bg-primary/90 disabled:bg-muted disabled:cursor-not-allowed text-primary-foreground rounded-xl transition-colors"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
