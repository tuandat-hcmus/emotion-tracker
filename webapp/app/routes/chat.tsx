import { useEffect, useMemo, useRef, useState } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import {
  ArrowRight01Icon,
  Leaf02Icon,
  Mic01Icon,
  SparklesIcon,
} from "@hugeicons/core-free-icons"

import { useAuth } from "~/context/auth-context"
import { useSoulForest } from "~/context/soul-forest-context"
import { api } from "~/lib/api"
import type {
  CheckinDetail,
  ConversationSessionResponse,
  ConversationTurnResponse,
  JournalHistoryItem,
  RespondPreviewResponse,
} from "~/lib/contracts"
import { formatEmotionLabel, getEmotionColor, isSoulEmotion } from "~/lib/emotions"

function formatDateTime(value: string) {
  const parsed = new Date(value)

  if (Number.isNaN(parsed.getTime())) {
    return "Unknown time"
  }

  return parsed.toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  })
}

function formatRelativeDateLabel(value: string) {
  const parsed = new Date(value)

  if (Number.isNaN(parsed.getTime())) {
    return "Earlier"
  }

  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const target = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate())
  const diffDays = Math.round((today.getTime() - target.getTime()) / 86400000)

  if (diffDays === 0) {
    return "Today"
  }

  if (diffDays === 1) {
    return "Yesterday"
  }

  if (diffDays > 1 && diffDays < 7) {
    return parsed.toLocaleDateString([], { weekday: "long" })
  }

  return parsed.toLocaleDateString([], { dateStyle: "medium" })
}

function formatPercent(value: number | null | undefined) {
  if (typeof value !== "number") {
    return null
  }

  return `${Math.round(value * 100)}%`
}

function normalizeLabel(value: string | null | undefined) {
  return value && isSoulEmotion(value) ? formatEmotionLabel(value) : "Neutral"
}

function Bubble({
  align = "left",
  badge,
  meta,
  text,
  timestamp,
}: {
  align?: "left" | "right"
  badge: string
  meta?: string | null
  text: string
  timestamp?: string | null
}) {
  const isRight = align === "right"

  return (
    <div className={`flex ${isRight ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[92%] rounded-[1.55rem] px-4 py-3 sm:max-w-[78%] ${
          isRight
            ? "bg-[var(--brand-primary)] text-[var(--brand-on-primary)]"
            : "border border-[#D6F4E6] bg-white text-[#163D33]"
        }`}
      >
        <div className="flex items-center gap-2 text-[0.68rem] uppercase tracking-[0.16em] opacity-70">
          <span>{badge}</span>
          {meta ? <span className="rounded-full bg-black/5 px-2 py-1 normal-case">{meta}</span> : null}
        </div>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-7">{text}</p>
        {timestamp ? <p className="mt-3 text-[0.72rem] opacity-55">{timestamp}</p> : null}
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { token, user } = useAuth()
  const { currentMood, refreshHome, syncCheckinResult } = useSoulForest()
  const [text, setText] = useState("")
  const [history, setHistory] = useState<JournalHistoryItem[]>([])
  const [preview, setPreview] = useState<RespondPreviewResponse | null>(null)
  const [pageStatus, setPageStatus] = useState<"idle" | "loading" | "ready" | "error">(
    "idle"
  )
  const [pageError, setPageError] = useState<string | null>(null)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [historyDetails, setHistoryDetails] = useState<Record<string, CheckinDetail>>({})
  const [conversationSessions, setConversationSessions] = useState<
    ConversationSessionResponse[]
  >([])
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null)
  const [selectedConversationTurns, setSelectedConversationTurns] = useState<
    ConversationTurnResponse[]
  >([])
  const [conversationStatus, setConversationStatus] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle")
  const threadBottomRef = useRef<HTMLDivElement | null>(null)

  async function loadChatData() {
    if (!token || !user) {
      return
    }

    const results = await Promise.allSettled([
      api.getHistory(token, user.id, 24, 0),
      api.getConversationSessions(token, 10, 0),
    ])

    const historyResult = results[0]
    const conversationResult = results[1]

    if (historyResult.status === "fulfilled") {
      setHistory(historyResult.value.items)
    } else {
      setHistory([])
    }

    if (conversationResult.status === "fulfilled") {
      const sessions = conversationResult.value.items
      setConversationSessions(sessions)
      setSelectedConversationId((current) => {
        if (current && sessions.some((item) => item.id === current)) {
          return current
        }
        return sessions[0]?.id ?? null
      })
    } else {
      setConversationSessions([])
      setSelectedConversationId(null)
    }

    const failures = results.filter(
      (result): result is PromiseRejectedResult => result.status === "rejected"
    )

    if (failures.length > 0) {
      const reason = failures[0]?.reason
      setPageError(reason instanceof Error ? reason.message : "Unable to load chat data.")
      setPageStatus(failures.length === results.length ? "error" : "ready")
      return
    }

    setPageError(null)
    setPageStatus("ready")
  }

  useEffect(() => {
    if (!token || !user) {
      setHistory([])
      setConversationSessions([])
      setHistoryDetails({})
      return
    }

    let cancelled = false

    async function hydrate() {
      setPageStatus("loading")
      setPageError(null)

      try {
        if (cancelled) {
          return
        }

        await loadChatData()
      } catch (error) {
        if (cancelled) {
          return
        }

        setPageStatus("error")
        setPageError(error instanceof Error ? error.message : "Unable to load chat data.")
      }
    }

    void hydrate()

    return () => {
      cancelled = true
    }
  }, [token, user])

  useEffect(() => {
    if (!token) {
      setHistoryDetails({})
      return
    }

    const accessToken = token
    const visibleEntries = history.slice(0, 10)

    if (visibleEntries.length === 0) {
      setHistoryDetails({})
      return
    }

    let cancelled = false

    async function loadVisibleDetails() {
      const results = await Promise.allSettled(
        visibleEntries.map((item) => api.getCheckin(accessToken, item.entry_id))
      )

      if (cancelled) {
        return
      }

      setHistoryDetails((current) => {
        const next = { ...current }

        results.forEach((result, index) => {
          const entryId = visibleEntries[index]?.entry_id

          if (!entryId || result.status !== "fulfilled") {
            return
          }

          next[entryId] = result.value
        })

        return next
      })
    }

    void loadVisibleDetails()

    return () => {
      cancelled = true
    }
  }, [history, token])

  useEffect(() => {
    if (!token || !selectedConversationId) {
      setSelectedConversationTurns([])
      setConversationStatus("idle")
      return
    }

    const accessToken = token
    const sessionId = selectedConversationId
    let cancelled = false

    async function loadTurns() {
      setConversationStatus("loading")

      try {
        const response = await api.getConversationSessionTurns(
          accessToken,
          sessionId,
          24,
          0
        )

        if (cancelled) {
          return
        }

        setSelectedConversationTurns(response.items)
        setConversationStatus("ready")
      } catch {
        if (cancelled) {
          return
        }

        setSelectedConversationTurns([])
        setConversationStatus("error")
      }
    }

    void loadTurns()

    return () => {
      cancelled = true
    }
  }, [selectedConversationId, token])

  useEffect(() => {
    threadBottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [history, preview])

  async function handlePreview() {
    if (!token || !text.trim()) {
      return
    }

    setIsPreviewing(true)
    setPageError(null)

    try {
      const response = await api.getRespondPreview(token, {
        transcript: text.trim(),
        session_type: "free",
      })
      setPreview(response)
    } catch (error) {
      setPageError(error instanceof Error ? error.message : "Unable to preview right now.")
    } finally {
      setIsPreviewing(false)
    }
  }

  async function handleSubmit() {
    if (!token || !text.trim()) {
      return
    }

    setIsSubmitting(true)
    setPageError(null)

    try {
      const result = await api.createTextCheckin(token, {
        text: text.trim(),
        session_type: "free",
      })

      syncCheckinResult(result)
      setText("")
      setPreview(null)
      await refreshHome()
      await loadChatData()
    } catch (error) {
      setPageError(error instanceof Error ? error.message : "Unable to save this check-in.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const recentHistory = useMemo(() => history.slice(0, 10).reverse(), [history])
  const currentMoodColor = getEmotionColor(currentMood)

  return (
    <section className="h-[calc(100svh-8rem)] p-4 md:p-6">
      <div className="mx-auto grid h-full max-w-6xl gap-4 xl:grid-cols-[240px_minmax(0,1fr)]">
        <aside className="hidden h-full overflow-y-auto xl:block">
          <div className="space-y-4">
            <div className="rounded-[2rem] bg-white/82 p-5 shadow-[0_18px_50px_rgba(22,68,61,0.08)]">
              <div className="flex items-center gap-3">
                <span
                  className="flex h-11 w-11 items-center justify-center rounded-2xl"
                  style={{ backgroundColor: `${currentMoodColor}22`, color: currentMoodColor }}
                >
                  <HugeiconsIcon icon={Leaf02Icon} size={20} strokeWidth={1.8} />
                </span>
                <div>
                  <p className="text-sm font-semibold text-[#163D33]">
                    {normalizeLabel(currentMood)}
                  </p>
                  <p className="text-xs text-[#648078]">{history.length} entries</p>
                </div>
              </div>
            </div>

            <div className="rounded-[2rem] bg-white/82 p-5 shadow-[0_18px_50px_rgba(22,68,61,0.08)]">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-[#163D33]">Voice archive</p>
                <HugeiconsIcon
                  icon={Mic01Icon}
                  size={18}
                  strokeWidth={1.8}
                  className="text-[var(--brand-primary)]"
                />
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {conversationSessions.length === 0 ? (
                  <p className="text-sm text-[#648078]">No saved sessions.</p>
                ) : (
                  conversationSessions.map((session) => (
                    <button
                      key={session.id}
                      type="button"
                      onClick={() => setSelectedConversationId(session.id)}
                      className={`rounded-full px-3 py-2 text-xs transition-colors ${
                        selectedConversationId === session.id
                          ? "bg-[var(--brand-primary)] text-[var(--brand-on-primary)]"
                          : "bg-[var(--brand-primary-soft)] text-[var(--brand-primary-muted)]"
                      }`}
                    >
                      {formatDateTime(session.started_at)}
                    </button>
                  ))
                )}
              </div>

              {selectedConversationId ? (
                <div className="mt-4 space-y-3">
                  {conversationStatus === "loading" ? (
                    <p className="text-sm text-[#648078]">Loading...</p>
                  ) : conversationStatus === "error" ? (
                    <p className="text-sm text-[#A34F38]">This conversation is unavailable.</p>
                  ) : (
                    selectedConversationTurns.map((turn) => (
                      <div key={turn.id} className="rounded-[1.25rem] bg-[#F8FFFC] p-3">
                        <p className="text-[0.68rem] uppercase tracking-[0.16em] text-[var(--brand-primary-muted)]">
                          {turn.role === "user" ? "You" : "Companion"}
                        </p>
                        <p className="mt-2 text-sm leading-6 text-[#234640]">{turn.text}</p>
                      </div>
                    ))
                  )}
                </div>
              ) : null}
            </div>
          </div>
        </aside>

        <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-[2.2rem] bg-white/88 shadow-[0_24px_70px_rgba(19,60,55,0.1)]">
          <div className="border-b border-[#D6F4E6] bg-[linear-gradient(135deg,#E8FFF4,#F7FFFA)] px-5 py-4 md:px-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-[var(--brand-primary-muted)]">Chat</p>
                <h1 className="mt-1 text-2xl font-semibold text-[#163D33]">Conversation</h1>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className="rounded-full px-3 py-1 text-xs"
                  style={{
                    backgroundColor: `${currentMoodColor}22`,
                    color: currentMoodColor,
                  }}
                >
                  {normalizeLabel(currentMood)}
                </span>
                <span className="rounded-full bg-[var(--brand-primary-soft)] px-3 py-1 text-xs text-[var(--brand-primary-muted)]">
                  {history.length}
                </span>
              </div>
            </div>

            {pageError ? (
              <p className="mt-3 rounded-[1rem] bg-[#FFF1ED] px-4 py-3 text-sm text-[#A34F38]">
                {pageError}
              </p>
            ) : null}
          </div>

          <div className="flex min-h-0 flex-1 flex-col">
            <div className="min-h-0 flex-1 space-y-4 overflow-y-auto bg-[linear-gradient(180deg,#FCFFFE,#F4FFF9)] px-4 py-4 md:px-5">
              {pageStatus === "loading" && recentHistory.length === 0 && !preview ? (
                <div className="rounded-[1.5rem] border border-dashed border-[#D6F4E6] bg-white/80 p-5 text-sm text-[#58736C]">
                  Loading your recent check-ins...
                </div>
              ) : null}

              {recentHistory.map((item, index, items) => {
                const currentLabel = formatRelativeDateLabel(item.created_at)
                const previousLabel =
                  index > 0 ? formatRelativeDateLabel(items[index - 1]?.created_at) : null
                const showSeparator = index === 0 || currentLabel !== previousLabel
                const detail = historyDetails[item.entry_id]
                const transcriptText = detail?.transcript_text || item.transcript_excerpt
                const assistantResponse = detail?.ai_response || item.ai_response_excerpt

                return (
                  <div key={item.id} className="space-y-2.5">
                    {showSeparator ? (
                      <div className="flex items-center gap-3 py-1">
                        <div className="h-px flex-1 bg-[#D6F4E6]" />
                        <p className="text-[0.7rem] uppercase tracking-[0.18em] text-[#648078]">
                          {currentLabel}
                        </p>
                        <div className="h-px flex-1 bg-[#D6F4E6]" />
                      </div>
                    ) : null}

                    {transcriptText ? (
                      <Bubble
                        align="right"
                        badge="You"
                        text={transcriptText}
                        timestamp={formatDateTime(item.created_at)}
                      />
                    ) : null}

                    {assistantResponse ? (
                      <Bubble
                        badge="Companion"
                        meta={`${normalizeLabel(item.primary_label)}${
                          item.stress_score != null
                            ? ` - ${formatPercent(item.stress_score) ?? ""} stress`
                            : ""
                        }`}
                        text={assistantResponse}
                      />
                    ) : null}
                  </div>
                )
              })}

              {recentHistory.length === 0 && !preview && pageStatus !== "loading" ? (
                <div className="rounded-[1.5rem] border border-dashed border-[#D6F4E6] bg-white/80 p-5 text-sm text-[#58736C]">
                  Start with a short message.
                </div>
              ) : null}

              {preview && text.trim() ? (
                <div className="space-y-3 rounded-[1.55rem] border border-[#D6F4E6] bg-white/88 p-4">
                  <Bubble align="right" badge="Draft" text={text.trim()} />
                  <Bubble
                    badge="Preview"
                    meta={`${normalizeLabel(preview.emotion_analysis.primary_label)}${
                      preview.emotion_analysis.stress_score != null
                        ? ` - ${formatPercent(preview.emotion_analysis.stress_score) ?? ""} stress`
                        : ""
                    }`}
                    text={preview.ai_response}
                  />
                </div>
              ) : null}
              <div ref={threadBottomRef} />
            </div>

            <div className="border-t border-[#D6F4E6] bg-white px-4 py-4 md:px-5">
              <textarea
                value={text}
                onChange={(event) => {
                  setText(event.target.value)
                  setPreview(null)
                }}
                className="min-h-28 w-full rounded-[1.45rem] border border-[#D6F4E6] bg-[#F8FFFB] p-4 text-sm leading-7 text-[#163D33] outline-none"
                placeholder="Write what today feels like..."
              />

              <div className="mt-4 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => void handlePreview()}
                  disabled={isPreviewing || isSubmitting || text.trim().length === 0}
                  className="rounded-full bg-[var(--brand-primary-soft)] px-4 py-2.5 text-sm text-[var(--brand-primary-muted)] transition-colors hover:bg-[var(--brand-primary-soft-strong)] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <HugeiconsIcon
                    icon={SparklesIcon}
                    size={16}
                    strokeWidth={1.8}
                    className="mr-2 inline-block"
                  />
                  {isPreviewing ? "Previewing..." : "Preview"}
                </button>
                <button
                  type="button"
                  onClick={() => void handleSubmit()}
                  disabled={isSubmitting || text.trim().length === 0}
                  className="rounded-full bg-[var(--brand-primary)] px-4 py-2.5 text-sm text-[var(--brand-on-primary)] transition-colors hover:bg-[var(--brand-primary-strong)] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <HugeiconsIcon
                    icon={ArrowRight01Icon}
                    size={16}
                    strokeWidth={1.8}
                    className="mr-2 inline-block"
                  />
                  {isSubmitting ? "Saving..." : "Send"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
