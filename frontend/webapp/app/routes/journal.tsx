import { useEffect, useRef, useState } from "react"
import type { ReactNode } from "react"

import { DeferredSoulTree } from "~/components/home/deferred-soul-tree"
import { useAuth } from "~/context/auth-context"
import { useSoulForest } from "~/context/soul-forest-context"
import { api } from "~/lib/api"
import type {
  CalendarDayItem,
  CheckinDetail,
  ConversationSessionResponse,
  ConversationTurnResponse,
  JournalHistoryItem,
  RespondPreviewResponse,
  UserSummaryResponse,
  WrapupSnapshotResponse,
} from "~/lib/contracts"
import { formatEmotionLabel, getEmotionColor, isSoulEmotion } from "~/lib/emotions"

type WrapupKind = "weekly" | "monthly"
type TrendsTab = "7d" | "30d" | "month"

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
    return "n/a"
  }

  return `${Math.round(value * 100)}%`
}

function normalizeLabel(value: string | null | undefined) {
  return value && isSoulEmotion(value) ? formatEmotionLabel(value) : "Neutral"
}

function MiniBarChart({
  items,
}: {
  items: Array<{ color: string; label: string; value: number }>
}) {
  const maxValue = Math.max(...items.map((item) => item.value), 1)

  return (
    <div className="flex items-end gap-2">
      {items.map((item) => (
        <div key={item.label} className="flex flex-1 flex-col items-center gap-2">
          <div
            className="w-full rounded-full"
            style={{
              height: 18 + (item.value / maxValue) * 34,
              backgroundColor: item.color,
              opacity: item.value > 0 ? 0.9 : 0.28,
            }}
          />
          <span className="text-[0.65rem] text-[#2F3E36]/45">{item.label}</span>
        </div>
      ))}
    </div>
  )
}

function MiniSparkline({
  points,
}: {
  points: number[]
}) {
  if (points.length === 0) {
    return (
      <div className="flex h-16 items-center justify-center rounded-[1rem] bg-white/52 text-sm text-[#2F3E36]/52">
        No trend yet
      </div>
    )
  }

  const width = 220
  const height = 64
  const min = Math.min(...points)
  const max = Math.max(...points)
  const range = max - min || 1

  const path = points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * width
      const y = height - ((point - min) / range) * (height - 12) - 6
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(" ")

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-16 w-full overflow-visible">
      <path
        d={path}
        fill="none"
        stroke="#7E9F8B"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function MiniStackedBar({
  items,
}: {
  items: Array<{ color: string; label: string; value: number }>
}) {
  const total = items.reduce((sum, item) => sum + item.value, 0)

  if (total <= 0) {
    return (
      <div className="rounded-[1rem] bg-white/52 px-4 py-5 text-sm text-[#2F3E36]/52">
        Mood distribution will appear here once more check-ins are saved.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex h-3 overflow-hidden rounded-full bg-white/60">
        {items
          .filter((item) => item.value > 0)
          .map((item) => (
            <div
              key={item.label}
              style={{
                width: `${(item.value / total) * 100}%`,
                backgroundColor: item.color,
              }}
            />
          ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {items
          .filter((item) => item.value > 0)
          .map((item) => (
            <span
              key={item.label}
              className="rounded-full bg-white/68 px-3 py-1 text-[0.68rem] text-[#2F3E36]/68"
            >
              {item.label} {item.value}
            </span>
          ))}
      </div>
    </div>
  )
}

type JournalLoadState = {
  calendar: CalendarDayItem[]
  history: JournalHistoryItem[]
  summary: UserSummaryResponse | null
  wrapup: WrapupSnapshotResponse | null
}

const INITIAL_LOAD_STATE: JournalLoadState = {
  calendar: [],
  history: [],
  summary: null,
  wrapup: null,
}

function ThreadBubble({
  align = "left",
  badge,
  meta,
  text,
  timestamp,
  note,
  footer,
}: {
  align?: "left" | "right"
  badge?: string | null
  meta?: string | null
  text: string
  timestamp?: string | null
  note?: string | null
  footer?: ReactNode
}) {
  const isRight = align === "right"

  return (
    <div className={`flex ${isRight ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[92%] rounded-[1.7rem] px-4 py-3 shadow-sm sm:max-w-[78%] ${
          isRight
            ? "bg-[#7E9F8B] text-white shadow-[0_14px_28px_rgba(126,159,139,0.18)]"
            : "border border-[#E7E0D3] bg-[linear-gradient(180deg,rgba(255,255,255,0.95),rgba(248,245,238,1))] text-[#2F3E36] shadow-[0_12px_24px_rgba(80,94,87,0.08)]"
        }`}
      >
        {badge ? (
          <div className="flex items-center gap-2">
            {!isRight ? (
              <span className="h-2 w-2 rounded-full bg-[#7E9F8B]/70 shadow-[0_0_0_4px_rgba(126,159,139,0.08)]" />
            ) : null}
            <p
              className={`text-[0.62rem] uppercase tracking-[0.16em] ${
                isRight ? "text-white/64" : "text-[#7E9F8B]/84"
              }`}
            >
              {badge}
            </p>
            {meta ? (
              <span
                className={`rounded-full px-2.5 py-1 text-[0.65rem] ${
                  isRight
                    ? "bg-white/14 text-white/74"
                    : "bg-[#F1F5EF] text-[#6A8375]"
                }`}
              >
                {meta}
              </span>
            ) : null}
          </div>
        ) : null}
        <p className="mt-1 whitespace-pre-wrap text-sm leading-7">{text}</p>
        {note ? (
          <p
            className={`mt-2 text-[0.68rem] ${
              isRight ? "text-white/58" : "text-[#2F3E36]/46"
            }`}
          >
            {note}
          </p>
        ) : null}
        {footer ? <div className="mt-3 space-y-2 text-sm leading-6">{footer}</div> : null}
        {timestamp ? (
          <p
            className={`mt-2 text-[0.68rem] tracking-[0.04em] ${
              isRight ? "text-white/58" : "text-[#2F3E36]/38"
            }`}
          >
            {timestamp}
          </p>
        ) : null}
      </div>
    </div>
  )
}

export default function JournalPage() {
  const { token, user } = useAuth()
  const { currentMood, refreshHome, syncCheckinResult, treeScore } = useSoulForest()
  const [text, setText] = useState("")
  const [history, setHistory] = useState<JournalHistoryItem[]>(INITIAL_LOAD_STATE.history)
  const [summary, setSummary] = useState<UserSummaryResponse | null>(INITIAL_LOAD_STATE.summary)
  const [calendar, setCalendar] = useState<CalendarDayItem[]>(INITIAL_LOAD_STATE.calendar)
  const [wrapupKind, setWrapupKind] = useState<WrapupKind>("weekly")
  const [wrapup, setWrapup] = useState<WrapupSnapshotResponse | null>(INITIAL_LOAD_STATE.wrapup)
  const [preview, setPreview] = useState<RespondPreviewResponse | null>(null)
  const [pageStatus, setPageStatus] = useState<"idle" | "loading" | "ready" | "error">(
    "idle"
  )
  const [pageError, setPageError] = useState<string | null>(null)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [conversationSessions, setConversationSessions] = useState<
    ConversationSessionResponse[]
  >([])
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(
    null
  )
  const [selectedConversationTurns, setSelectedConversationTurns] = useState<
    ConversationTurnResponse[]
  >([])
  const [conversationStatus, setConversationStatus] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle")
  const [historyDetails, setHistoryDetails] = useState<Record<string, CheckinDetail>>({})
  const [archiveOpen, setArchiveOpen] = useState(false)
  const [trendsTab, setTrendsTab] = useState<TrendsTab>("7d")
  const threadViewportRef = useRef<HTMLDivElement | null>(null)
  const threadBottomRef = useRef<HTMLDivElement | null>(null)

  async function reloadJournalData(activeWrapupKind: WrapupKind) {
    if (!token || !user) {
      return
    }

    const results = await Promise.allSettled([
      api.getHistory(token, user.id, 20, 0),
      api.getUserSummary(token, user.id, 30),
      api.getCalendar(token, 14),
      activeWrapupKind === "weekly"
        ? api.getLatestWeeklyWrapup(token)
        : api.getLatestMonthlyWrapup(token),
      api.getConversationSessions(token, 8, 0),
    ])

    const failures = results.filter(
      (result): result is PromiseRejectedResult => result.status === "rejected"
    )

    if (results[0]?.status === "fulfilled") {
      setHistory(results[0].value.items)
    } else {
      setHistory([])
    }

    if (results[1]?.status === "fulfilled") {
      setSummary(results[1].value)
    } else {
      setSummary(null)
    }

    if (results[2]?.status === "fulfilled") {
      setCalendar(results[2].value.items)
    } else {
      setCalendar([])
    }

    if (results[3]?.status === "fulfilled") {
      setWrapup(results[3].value)
    } else {
      setWrapup(null)
    }

    if (results[4]?.status === "fulfilled") {
      const sessions = results[4].value.items
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

    if (failures.length === 0) {
      setPageStatus("ready")
      setPageError(null)
      return
    }

    const firstFailure = failures[0]?.reason
    setPageStatus(failures.length === results.length ? "error" : "ready")
    setPageError(
      firstFailure instanceof Error
        ? firstFailure.message
        : "Some journal data could not be loaded."
    )
  }

  useEffect(() => {
    if (!token || !user) {
      setHistoryDetails({})
      return
    }

    let cancelled = false

    async function loadJournalPage() {
      setPageStatus("loading")
      setPageError(null)

      try {
        if (cancelled) {
          return
        }

        await reloadJournalData(wrapupKind)
      } catch (error) {
        if (cancelled) {
          return
        }

        setPageStatus("error")
        setPageError(
          error instanceof Error ? error.message : "Failed to load journal data."
        )
      }
    }

    void loadJournalPage()

    return () => {
      cancelled = true
    }
  }, [token, user, wrapupKind])

  useEffect(() => {
    if (!token || !selectedConversationId) {
      setSelectedConversationTurns([])
      setConversationStatus("idle")
      return
    }

    const accessToken = token as string
    const sessionId = selectedConversationId as string
    let cancelled = false

    async function loadConversationTurns() {
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

    void loadConversationTurns()

    return () => {
      cancelled = true
    }
  }, [selectedConversationId, token])

  useEffect(() => {
    if (!token) {
      setHistoryDetails({})
      return
    }

    const authToken = token
    const visibleEntries = history.slice(0, 8)

    if (visibleEntries.length === 0) {
      setHistoryDetails({})
      return
    }

    const visibleEntryIds = new Set(visibleEntries.map((item) => item.entry_id))
    setHistoryDetails((current) =>
      Object.fromEntries(
        Object.entries(current).filter(([entryId]) => visibleEntryIds.has(entryId))
      )
    )

    let cancelled = false

    async function loadVisibleEntryDetails() {
      const results = await Promise.allSettled(
        visibleEntries.map((item) => api.getCheckin(authToken, item.entry_id))
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

    void loadVisibleEntryDetails()

    return () => {
      cancelled = true
    }
  }, [history, token])

  useEffect(() => {
    setWrapupKind(trendsTab === "month" ? "monthly" : "weekly")
  }, [trendsTab])

  async function handlePreview() {
    if (!token || !text.trim()) {
      return
    }

    setIsPreviewing(true)

    try {
      const response = await api.getRespondPreview(token, {
        transcript: text.trim(),
        session_type: "free",
      })
      setPreview(response)
    } catch (error) {
      setPageError(
        error instanceof Error ? error.message : "Failed to preview response."
      )
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
      await reloadJournalData(wrapupKind)
    } catch (error) {
      setPageError(
        error instanceof Error ? error.message : "Failed to save your check-in."
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  useEffect(() => {
    const viewport = threadViewportRef.current
    const bottom = threadBottomRef.current

    if (!viewport || !bottom) {
      return
    }

    bottom.scrollIntoView({ block: "end", behavior: "smooth" })
  }, [history, preview, text])

  const recentHistory = history.slice(0, 8).reverse()
  const treeStageLabel =
    treeScore >= 80 ? "Steady growth" : treeScore >= 55 ? "Growing gently" : "Taking root"
  const weeklyCheckins = calendar.slice(0, 7).reduce((sum, day) => sum + day.entry_count, 0)
  const recentStressValues = history
    .map((item) => item.stress_score)
    .filter((value): value is number => typeof value === "number")
    .slice(0, 7)
  const recentStressAverage =
    recentStressValues.length > 0
      ? recentStressValues.reduce((sum, value) => sum + value, 0) / recentStressValues.length
      : null
  const recentDays = calendar.slice(0, 7).reverse()
  const recentEntries = history.slice(0, 4)
  const rhythmBars7d = recentDays.map((day) => {
    const emotionLabel =
      day.primary_emotion_label && isSoulEmotion(day.primary_emotion_label)
        ? day.primary_emotion_label
        : null
    return {
      label: day.date.slice(5),
      value: day.entry_count,
      color: emotionLabel ? getEmotionColor(emotionLabel) : "#DCE6DE",
    }
  })
  const stressPoints7d = recentDays
    .map((day) => day.average_stress_score)
    .filter((value): value is number => typeof value === "number")
  const stressByDay30 = Array.from(
    history.reduce((accumulator, item) => {
      if (item.stress_score == null) {
        return accumulator
      }
      const dayKey = item.created_at.slice(0, 10)
      const current = accumulator.get(dayKey) ?? { total: 0, count: 0 }
      current.total += item.stress_score
      current.count += 1
      accumulator.set(dayKey, current)
      return accumulator
    }, new Map<string, { total: number; count: number }>())
  )
    .sort(([left], [right]) => left.localeCompare(right))
    .slice(-10)
    .map(([, value]) => value.total / value.count)
  const moodDistribution = Object.entries(summary?.emotion_counts ?? {}).flatMap(
    ([label, count]) => {
      if (!isSoulEmotion(label) || count <= 0) {
        return []
      }

      return [
        {
          label: formatEmotionLabel(label),
          value: count,
          color: getEmotionColor(label),
        },
      ]
    }
  )

  return (
    <section className="min-h-[calc(100vh-7.5rem)] p-3 md:p-5">
      <div className="mx-auto grid max-w-[1280px] gap-4 xl:grid-cols-[minmax(0,1.75fr)_minmax(0,0.75fr)] xl:items-start">
        <div className="order-2 space-y-4">
          <div className="rounded-[1.45rem] border border-white/28 bg-white/18 p-4">
            <p className="text-[0.68rem] uppercase tracking-[0.22em] text-[#7E9F8B]">
              Companion
            </p>
            <div className="mt-3 rounded-[1.35rem] bg-[radial-gradient(circle_at_top,rgba(168,195,216,0.22),rgba(253,251,247,0.94),rgba(126,159,139,0.1))] p-3">
              <DeferredSoulTree
                emotion={currentMood}
                score={treeScore}
                deferMs={120}
                className="h-56 rounded-[1.2rem] border-0 bg-transparent shadow-none"
              />
            </div>
            <div className="mt-4 flex flex-wrap gap-2 text-xs text-[#2F3E36]/66">
              <span className="rounded-full bg-white/70 px-3 py-1.5">
                {formatEmotionLabel(currentMood)}
              </span>
              <span className="rounded-full bg-white/70 px-3 py-1.5">
                {treeStageLabel}
              </span>
              <span className="rounded-full bg-white/70 px-3 py-1.5">
                {Math.round(treeScore)}/100
              </span>
            </div>
            <p className="mt-3 text-sm leading-6 text-[#2F3E36]/62">
              A quiet visual marker of how the conversation has been unfolding.
            </p>
          </div>

          <div className="rounded-[1.45rem] border border-white/28 bg-white/12 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[0.68rem] uppercase tracking-[0.22em] text-[#7E9F8B]">
                Trends
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setTrendsTab("7d")}
                  className={`rounded-full px-3 py-1.5 text-xs ${
                    trendsTab === "7d"
                      ? "bg-[#7E9F8B] text-white"
                      : "bg-white/60 text-[#2F3E36]/66"
                  }`}
                >
                  7D
                </button>
                <button
                  type="button"
                  onClick={() => setTrendsTab("30d")}
                  className={`rounded-full px-3 py-1.5 text-xs ${
                    trendsTab === "30d"
                      ? "bg-[#7E9F8B] text-white"
                      : "bg-white/60 text-[#2F3E36]/66"
                  }`}
                >
                  30D
                </button>
                <button
                  type="button"
                  onClick={() => setTrendsTab("month")}
                  className={`rounded-full px-3 py-1.5 text-xs ${
                    trendsTab === "month"
                      ? "bg-[#7E9F8B] text-white"
                      : "bg-white/60 text-[#2F3E36]/66"
                  }`}
                >
                  Month
                </button>
              </div>
            </div>

            <div className="mt-4 space-y-4">
              {trendsTab === "7d" ? (
                <>
                  <div className="rounded-[1.15rem] bg-[#FDFBF7]/44 p-4">
                    <p className="text-sm font-medium text-[#2F3E36]">7-day check-in rhythm</p>
                    <div className="mt-4">
                      <MiniBarChart items={rhythmBars7d} />
                    </div>
                  </div>
                  <div className="rounded-[1.15rem] bg-[#FDFBF7]/44 p-4">
                    <p className="text-sm font-medium text-[#2F3E36]">Recent stress shape</p>
                    <div className="mt-3">
                      <MiniSparkline points={stressPoints7d} />
                    </div>
                  </div>
                </>
              ) : null}

              {trendsTab === "30d" ? (
                <>
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-white/68 px-3 py-1.5 text-xs text-[#2F3E36]/70">
                      {summary?.total_entries ?? 0} check-ins
                    </span>
                    <span className="rounded-full bg-white/68 px-3 py-1.5 text-xs text-[#2F3E36]/70">
                      {summary?.emotional_direction_trend ?? "mixed"}
                    </span>
                    <span className="rounded-full bg-white/68 px-3 py-1.5 text-xs text-[#2F3E36]/70">
                      {summary ? formatPercent(summary.high_stress_frequency) : "n/a"} high stress
                    </span>
                  </div>
                  <div className="rounded-[1.15rem] bg-[#FDFBF7]/44 p-4">
                    <p className="text-sm font-medium text-[#2F3E36]">30-day stress trend</p>
                    <div className="mt-3">
                      <MiniSparkline points={stressByDay30} />
                    </div>
                  </div>
                  <p className="text-sm leading-6 text-[#2F3E36]/64">
                    {summary?.summary_text
                      ? summary.summary_text.split(".")[0]
                      : "A longer-view pattern will appear here as your check-ins collect over time."}
                  </p>
                </>
              ) : null}

              {trendsTab === "month" ? (
                <>
                  <div className="rounded-[1.15rem] bg-[#FDFBF7]/44 p-4">
                    <p className="text-sm font-medium text-[#2F3E36]">Monthly mood distribution</p>
                    <div className="mt-4">
                      <MiniStackedBar items={moodDistribution} />
                    </div>
                  </div>
                  <div className="rounded-[1.15rem] bg-[#FDFBF7]/44 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-medium text-[#2F3E36]">Monthly reflection</p>
                      <span className="rounded-full bg-white/70 px-3 py-1 text-[0.68rem] text-[#2F3E36]/62">
                        {wrapup ? formatPercent(wrapup.payload.high_stress_frequency) : "n/a"}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-[#2F3E36]/64">
                      {wrapup?.payload.summary_text
                        ? wrapup.payload.summary_text.split(".")[0]
                        : "A monthly reflection will appear here once enough check-ins have been saved."}
                    </p>
                  </div>
                </>
              ) : null}
            </div>
          </div>

          <div className="rounded-[1.45rem] border border-white/28 bg-white/12 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[0.68rem] uppercase tracking-[0.22em] text-[#7E9F8B]">
                Past conversations
              </p>
              <button
                type="button"
                onClick={() => setArchiveOpen((current) => !current)}
                className="rounded-full bg-white/56 px-3 py-1.5 text-xs text-[#2F3E36]/62"
              >
                {archiveOpen ? "Hide" : "Open"}
              </button>
            </div>

            <div className="mt-4 space-y-3">
              {recentEntries.length === 0 ? (
                <p className="rounded-[1.2rem] border border-dashed border-white/40 bg-white/18 p-4 text-sm leading-6 text-[#2F3E36]/64">
                  Past conversations will appear here after you save a few check-ins.
                </p>
              ) : (
                recentEntries.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-[1.1rem] bg-[#FDFBF7]/44 px-3 py-3"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="rounded-full bg-white/72 px-2.5 py-1 text-[0.68rem] text-[#2F3E36]/68">
                        {normalizeLabel(item.primary_label)}
                      </span>
                      <span className="text-[0.68rem] text-[#2F3E36]/42">
                        {formatDateTime(item.created_at)}
                      </span>
                    </div>
                    <p className="mt-2 line-clamp-2 text-sm leading-6 text-[#2F3E36]/70">
                      {item.transcript_excerpt || item.ai_response_excerpt || "Saved reflection"}
                    </p>
                  </div>
                ))
              )}

              {archiveOpen ? (
                <div className="border-t border-white/40 pt-3">
                  <div className="flex flex-wrap gap-2">
                    {conversationSessions.length === 0 ? (
                      <p className="rounded-[1rem] border border-dashed border-white/40 bg-white/18 p-3 text-sm leading-6 text-[#2F3E36]/64">
                        Saved voice conversations will appear here after you use the mic.
                      </p>
                    ) : (
                      conversationSessions.map((session) => (
                        <button
                          key={session.id}
                          type="button"
                          onClick={() => setSelectedConversationId(session.id)}
                          className={`rounded-full px-3 py-1.5 text-xs ${
                            selectedConversationId === session.id
                              ? "bg-[#7E9F8B] text-white"
                              : "bg-white/56 text-[#2F3E36]/70"
                          }`}
                        >
                          {formatDateTime(session.started_at)}
                        </button>
                      ))
                    )}
                  </div>

                  {selectedConversationId ? (
                    <div className="mt-3 rounded-[1.1rem] border border-white/34 bg-[#F8F5EE]/36 p-3">
                      <div className="space-y-3">
                        {conversationStatus === "loading" ? (
                          <p className="text-sm leading-6 text-[#2F3E36]/66">
                            Loading this conversation...
                          </p>
                        ) : conversationStatus === "error" ? (
                          <p className="text-sm leading-6 text-[#8b4e3d]">
                            This saved conversation could not be loaded right now.
                          </p>
                        ) : selectedConversationTurns.length === 0 ? (
                          <p className="text-sm leading-6 text-[#2F3E36]/66">
                            No saved turns were returned for this conversation.
                          </p>
                        ) : (
                          selectedConversationTurns.map((turn) => (
                            <ThreadBubble
                              key={turn.id}
                              align={turn.role === "user" ? "right" : "left"}
                              badge={turn.role === "user" ? "You" : "Companion"}
                              text={turn.text}
                              timestamp={
                                turn.role === "user"
                                  ? formatDateTime(turn.created_at)
                                  : null
                              }
                            />
                          ))
                        )}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          </div>
        </div>

        <div className="order-1">
          <div className="flex min-h-[78vh] flex-col overflow-hidden rounded-[1.85rem] border border-white/45 bg-white/58 shadow-[0_30px_80px_rgba(73,87,81,0.14)] xl:h-[calc(100vh-7rem)]">
            <div className="border-b border-white/50 px-5 py-4 md:px-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="max-w-md">
                  <p className="text-xs uppercase tracking-[0.24em] text-[#7E9F8B]">
                    Today&apos;s conversation
                  </p>
                  <h2 className="mt-2 text-lg font-semibold text-[#2F3E36]">
                    Send a message
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-[#2F3E36]/58">
                    The conversation stays central. Mood stays in the background.
                  </p>
                </div>
                <div className="rounded-full bg-[#FDFBF7]/82 px-3 py-1.5 text-xs text-[#2F3E36]/60">
                  {history.length} exchanges
                </div>
              </div>

              {pageError ? (
                <p className="mt-4 rounded-[1rem] bg-[#F7E9E2] px-4 py-3 text-sm text-[#8b4e3d]">
                  {pageStatus === "error"
                    ? pageError
                    : `Some parts of this space are unavailable right now: ${pageError}`}
                </p>
              ) : null}
            </div>

            <div
              ref={threadViewportRef}
              className="min-h-0 flex-1 overflow-y-auto bg-[linear-gradient(180deg,rgba(248,245,238,0.76),rgba(255,255,255,0.44))] px-4 py-4 md:px-5"
            >
              <div className="space-y-4">
                {pageStatus === "loading" && recentHistory.length === 0 && !preview ? (
                  <div className="rounded-[1.5rem] border border-dashed border-white/45 bg-white/32 p-5 text-sm leading-6 text-[#2F3E36]/68">
                    Loading your recent check-ins...
                  </div>
                ) : recentHistory.length === 0 && !preview ? (
                  <div className="rounded-[1.5rem] border border-dashed border-white/45 bg-white/32 p-5 text-sm leading-6 text-[#2F3E36]/68">
                    Begin with a few lines. Your message and the reflection it receives will appear here in one conversation thread.
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
                  const isTranscriptExcerptFallback =
                    !detail?.transcript_text && Boolean(item.transcript_excerpt)
                  const isResponseExcerptFallback =
                    !detail?.ai_response && Boolean(item.ai_response_excerpt)

                  return (
                    <div key={item.id} className="space-y-2.5">
                      {showSeparator ? (
                        <div className="flex items-center gap-3 py-1">
                          <div className="h-px flex-1 bg-white/55" />
                          <p className="text-[0.68rem] uppercase tracking-[0.22em] text-[#2F3E36]/42">
                            {currentLabel}
                          </p>
                          <div className="h-px flex-1 bg-white/55" />
                        </div>
                      ) : null}

                      <div className="space-y-2">
                        {transcriptText ? (
                          <ThreadBubble
                            align="right"
                            badge="You"
                            text={transcriptText}
                            note={isTranscriptExcerptFallback ? "Saved message excerpt" : null}
                            timestamp={formatDateTime(item.created_at)}
                          />
                        ) : null}

                        {assistantResponse ? (
                          <ThreadBubble
                            badge="Companion"
                            meta={
                              index === 0
                                ? `${normalizeLabel(item.primary_label)}${
                                    item.stress_score != null
                                      ? ` · stress ${formatPercent(item.stress_score)}`
                                      : ""
                                  }`
                                : normalizeLabel(item.primary_label)
                            }
                            text={assistantResponse}
                            note={isResponseExcerptFallback ? "Saved response excerpt" : null}
                            footer={
                              detail?.follow_up_question || detail?.gentle_suggestion ? (
                                <>
                                  {detail.follow_up_question ? (
                                    <p className="text-[#2F3E36]/66">
                                      {detail.follow_up_question}
                                    </p>
                                  ) : null}
                                  {detail.gentle_suggestion ? (
                                    <p className="text-xs tracking-[0.02em] text-[#6A8375]">
                                      {detail.gentle_suggestion}
                                    </p>
                                  ) : null}
                                </>
                              ) : null
                            }
                          />
                        ) : null}
                      </div>
                    </div>
                  )
                })}

                {preview && text.trim() ? (
                  <div className="space-y-2.5 rounded-[1.4rem] border border-dashed border-[#C9D6C8] bg-[linear-gradient(180deg,rgba(255,255,255,0.72),rgba(248,245,238,0.88))] px-3 py-3 shadow-[0_10px_24px_rgba(126,159,139,0.08)] sm:px-4">
                    <ThreadBubble
                      align="right"
                      badge="Current message"
                      text={text.trim()}
                    />
                    <ThreadBubble
                      badge="Companion"
                      meta={`${normalizeLabel(preview.emotion_analysis.primary_label)}${
                        preview.emotion_analysis.stress_score != null
                          ? ` · stress ${formatPercent(preview.emotion_analysis.stress_score)}`
                          : ""
                      }`}
                      text={preview.ai_response}
                      footer={
                        <>
                          {preview.follow_up_question ? (
                            <p className="text-[#2F3E36]/66">
                              {preview.follow_up_question}
                            </p>
                          ) : null}
                          {preview.gentle_suggestion ? (
                            <p className="text-xs tracking-[0.02em] text-[#6A8375]">
                              {preview.gentle_suggestion}
                            </p>
                          ) : null}
                        </>
                      }
                    />
                  </div>
                ) : null}
                <div ref={threadBottomRef} />
              </div>
            </div>

            <div className="sticky bottom-0 border-t border-white/50 bg-[linear-gradient(180deg,rgba(255,255,255,0.82),rgba(253,251,247,0.98))] px-4 py-4 backdrop-blur-sm md:px-5">
              <p className="text-[0.68rem] uppercase tracking-[0.2em] text-[#7E9F8B]/78">
                Your next turn
              </p>
              <textarea
                value={text}
                onChange={(event) => {
                  setText(event.target.value)
                  setPreview(null)
                }}
                className="mt-3 min-h-28 w-full rounded-[1.35rem] border border-white/50 bg-white/82 p-4 text-sm leading-7 text-[#2F3E36] outline-none"
                placeholder="Write what today feels like..."
              />

              <div className="mt-4 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => void handlePreview()}
                  disabled={isPreviewing || isSubmitting || text.trim().length === 0}
                  className="rounded-full border border-white/50 bg-white/62 px-5 py-2.5 text-sm text-[#2F3E36] transition-colors hover:bg-white/82 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isPreviewing ? "Preparing reflection..." : "Reflect first"}
                </button>
                <button
                  type="button"
                  onClick={() => void handleSubmit()}
                  disabled={isSubmitting || text.trim().length === 0}
                  className="rounded-full bg-[#7E9F8B] px-5 py-2.5 text-sm text-white transition-colors hover:bg-[#6D8D7A] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? "Saving..." : "Save this exchange"}
                </button>
                <span className="text-sm text-[#2F3E36]/50">
                  Prefer speaking? Use the mic for the same flow.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
