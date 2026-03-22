import { useEffect, useState } from "react"

import { useAuth } from "~/context/auth-context"
import { useSoulForest } from "~/context/soul-forest-context"
import { api } from "~/lib/api"
import type {
  CalendarDayItem,
  JournalHistoryItem,
  RespondPreviewResponse,
  UserSummaryResponse,
  WrapupSnapshotResponse,
} from "~/lib/contracts"
import { formatEmotionLabel, isSoulEmotion } from "~/lib/emotions"

type WrapupKind = "weekly" | "monthly"

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

function formatPercent(value: number | null | undefined) {
  if (typeof value !== "number") {
    return "n/a"
  }

  return `${Math.round(value * 100)}%`
}

function normalizeLabel(value: string | null | undefined) {
  return value && isSoulEmotion(value) ? formatEmotionLabel(value) : "Neutral"
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

export default function JournalPage() {
  const { token, user } = useAuth()
  const { refreshHome, syncCheckinResult } = useSoulForest()
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

  return (
    <section className="space-y-5 p-4 md:p-6">
      <div className="rounded-[2rem] border border-white/45 bg-gradient-to-br from-[#A8C3D8]/16 via-white/44 to-[#7E9F8B]/14 p-6">
        <p className="text-sm uppercase tracking-[0.3em] text-[#7E9F8B]">
          Journal
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-[#2F3E36]">
          A quiet place to check in with yourself
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-[#2F3E36]/72">
          Start with what feels most present right now. Your recent reflections
          and longer patterns sit nearby when you want perspective, not pressure.
        </p>
      </div>

      <div className="rounded-[2rem] border border-white/45 bg-white/40 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
              Today&apos;s check-in
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-[#2F3E36]">
              Write what this moment feels like
            </h2>
            <p className="mt-3 text-sm leading-7 text-[#2F3E36]/70">
              You can preview the reflection first, then save it when it feels right.
            </p>
          </div>
          <span className="rounded-full bg-white/58 px-4 py-2 text-sm text-[#2F3E36]/68">
            Text journaling first
          </span>
        </div>

        <textarea
          value={text}
          onChange={(event) => {
            setText(event.target.value)
            setPreview(null)
          }}
          className="mt-5 min-h-44 w-full rounded-[1.6rem] border border-white/50 bg-[#FDFBF7]/78 p-5 text-sm leading-7 text-[#2F3E36] outline-none"
          placeholder="Write what today felt like..."
        />

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => void handlePreview()}
            disabled={isPreviewing || isSubmitting || text.trim().length === 0}
            className="rounded-full border border-white/50 bg-white/48 px-5 py-2.5 text-sm text-[#2F3E36] transition-colors hover:bg-white/72 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isPreviewing ? "Preparing preview..." : "Preview reflection"}
          </button>
          <button
            type="button"
            onClick={() => void handleSubmit()}
            disabled={isSubmitting || text.trim().length === 0}
            className="rounded-full bg-[#7E9F8B] px-5 py-2.5 text-sm text-white transition-colors hover:bg-[#6D8D7A] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Saving..." : "Save check-in"}
          </button>
        </div>

        {pageError ? (
          <p className="mt-4 rounded-[1rem] bg-[#F7E9E2] px-4 py-3 text-sm text-[#8b4e3d]">
            {pageStatus === "error"
              ? pageError
              : `Some parts of your journal are unavailable right now: ${pageError}`}
          </p>
        ) : null}

        {preview ? (
          <div className="mt-5 rounded-[1.6rem] border border-white/45 bg-[#FDFBF7]/72 p-5">
            <div className="flex flex-wrap items-center gap-2 text-xs text-[#2F3E36]/62">
              <span className="rounded-full bg-white/75 px-3 py-1">
                {normalizeLabel(preview.emotion_analysis.primary_label)}
              </span>
              <span className="rounded-full bg-white/75 px-3 py-1">
                stress {formatPercent(preview.emotion_analysis.stress_score)}
              </span>
              {preview.topic_tags.slice(0, 4).map((tag) => (
                <span key={tag} className="rounded-full bg-white/75 px-3 py-1">
                  {tag}
                </span>
              ))}
            </div>

            <p className="mt-4 text-lg leading-8 font-medium text-[#2F3E36]">
              {preview.ai_response}
            </p>

            {preview.follow_up_question ? (
              <p className="mt-4 text-sm leading-7 text-[#2F3E36]/70">
                Consider next: {preview.follow_up_question}
              </p>
            ) : null}

            {preview.gentle_suggestion ? (
              <p className="mt-2 text-sm leading-7 text-[#2F3E36]/70">
                Gentle support: {preview.gentle_suggestion}
              </p>
            ) : null}
          </div>
        ) : (
          <div className="mt-5 rounded-[1.5rem] border border-dashed border-white/50 bg-white/24 p-4 text-sm leading-6 text-[#2F3E36]/64">
            Preview a reflection when you want a gentle read on what you&apos;ve written before saving it.
          </div>
        )}
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-5">
          <div className="rounded-[2rem] border border-white/45 bg-white/40 p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                  Recent reflections
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-[#2F3E36]">
                  A readable history of what you&apos;ve been carrying
                </h2>
              </div>
              <span className="rounded-full bg-white/58 px-4 py-2 text-sm text-[#2F3E36]/68">
                {history.length} saved
              </span>
            </div>

            <div className="mt-5 space-y-4">
              {pageStatus === "loading" ? (
                <p className="text-sm leading-6 text-[#2F3E36]/68">
                  Loading your recent reflections...
                </p>
              ) : history.length === 0 ? (
                <p className="rounded-[1.5rem] border border-dashed border-white/45 bg-white/24 p-5 text-sm leading-6 text-[#2F3E36]/68">
                  Your first saved check-in will appear here with the feeling it carried and the response it received.
                </p>
              ) : (
                history.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-[1.5rem] border border-white/45 bg-[#FDFBF7]/74 p-5"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full bg-white/80 px-3 py-1 text-xs text-[#2F3E36]/68">
                          {normalizeLabel(item.primary_label)}
                        </span>
                        {item.stress_score != null ? (
                          <span className="rounded-full bg-white/80 px-3 py-1 text-xs text-[#2F3E36]/68">
                            stress {formatPercent(item.stress_score)}
                          </span>
                        ) : null}
                      </div>
                      <p className="text-xs text-[#2F3E36]/56">
                        {formatDateTime(item.created_at)}
                      </p>
                    </div>

                    <p className="mt-4 text-sm leading-7 text-[#2F3E36]/76">
                      {item.transcript_excerpt ||
                        "A reflection was saved for this moment."}
                    </p>

                    <div className="mt-4 rounded-[1.25rem] bg-white/72 px-4 py-3">
                      <p className="text-xs uppercase tracking-[0.2em] text-[#7E9F8B]">
                        Response
                      </p>
                      <p className="mt-2 text-sm leading-6 text-[#2F3E36]/68">
                        {item.ai_response_excerpt ||
                          "A supportive response was saved with this entry."}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="rounded-[2rem] border border-white/45 bg-white/40 p-6">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                  Wrapup
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-[#2F3E36]">
                  Your latest {wrapupKind} reflection
                </h2>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setWrapupKind("weekly")}
                  className={`rounded-full px-3 py-1.5 text-xs ${
                    wrapupKind === "weekly"
                      ? "bg-[#7E9F8B] text-white"
                      : "bg-white/58 text-[#2F3E36]/70"
                  }`}
                >
                  Weekly
                </button>
                <button
                  type="button"
                  onClick={() => setWrapupKind("monthly")}
                  className={`rounded-full px-3 py-1.5 text-xs ${
                    wrapupKind === "monthly"
                      ? "bg-[#7E9F8B] text-white"
                      : "bg-white/58 text-[#2F3E36]/70"
                  }`}
                >
                  Monthly
                </button>
              </div>
            </div>

            {wrapup ? (
              <div className="mt-5 space-y-4">
                <p className="text-sm leading-7 text-[#2F3E36]/74">
                  {wrapup.payload.summary_text || wrapup.payload.closing_message}
                </p>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                  <div className="rounded-[1.25rem] bg-[#FDFBF7]/74 p-4">
                    <p className="text-xs uppercase tracking-[0.24em] text-[#7E9F8B]">
                      Period
                    </p>
                    <p className="mt-2 text-sm text-[#2F3E36]">
                      {wrapup.payload.period_start} to {wrapup.payload.period_end}
                    </p>
                  </div>
                  <div className="rounded-[1.25rem] bg-[#FDFBF7]/74 p-4">
                    <p className="text-xs uppercase tracking-[0.24em] text-[#7E9F8B]">
                      High stress
                    </p>
                    <p className="mt-2 text-sm text-[#2F3E36]">
                      {formatPercent(wrapup.payload.high_stress_frequency)}
                    </p>
                  </div>
                </div>

                {wrapup.payload.insight_cards.slice(0, 2).map((card) => (
                  <div
                    key={`${card.kind}-${card.title}`}
                    className="rounded-[1.25rem] bg-[#FDFBF7]/74 p-4"
                  >
                    <p className="text-sm font-medium text-[#2F3E36]">
                      {card.title}
                    </p>
                    <p className="mt-2 text-sm leading-6 text-[#2F3E36]/70">
                      {card.summary}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-5 rounded-[1.5rem] border border-dashed border-white/45 bg-white/24 p-5 text-sm leading-6 text-[#2F3E36]/68">
                A wrapup will appear here once enough recent check-ins have been gathered.
              </p>
            )}
          </div>

          <div className="rounded-[2rem] border border-white/45 bg-white/40 p-6">
            <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
              Recent patterns
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-[#2F3E36]">
              What your last 30 days suggest
            </h2>

            {summary ? (
              <div className="mt-5 space-y-4">
                <p className="text-sm leading-7 text-[#2F3E36]/74">
                  {summary.summary_text || "More summary details will appear here as you keep checking in."}
                </p>
                <div className="flex flex-wrap gap-2 text-xs text-[#2F3E36]/68">
                  <span className="rounded-full bg-[#FDFBF7]/74 px-3 py-1">
                    {summary.total_entries} entries
                  </span>
                  <span className="rounded-full bg-[#FDFBF7]/74 px-3 py-1">
                    {formatPercent(summary.high_stress_frequency)} high stress
                  </span>
                  <span className="rounded-full bg-[#FDFBF7]/74 px-3 py-1">
                    {summary.emotional_direction_trend}
                  </span>
                </div>
                {summary.recurring_triggers.slice(0, 3).map((trigger) => (
                  <p
                    key={trigger}
                    className="rounded-[1.1rem] bg-[#FDFBF7]/74 px-4 py-3 text-sm leading-6 text-[#2F3E36]/68"
                  >
                    {trigger}
                  </p>
                ))}
              </div>
            ) : (
              <p className="mt-5 rounded-[1.5rem] border border-dashed border-white/45 bg-white/24 p-5 text-sm leading-6 text-[#2F3E36]/68">
                Your longer-view patterns will appear here after more check-ins are saved.
              </p>
            )}
          </div>

          <div className="rounded-[2rem] border border-white/45 bg-white/40 p-6">
            <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
              Recent check-in days
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-[#2F3E36]">
              A gentle view of recent rhythm
            </h2>

            <div className="mt-5 space-y-3">
              {calendar.length === 0 ? (
                <p className="rounded-[1.5rem] border border-dashed border-white/45 bg-white/24 p-5 text-sm leading-6 text-[#2F3E36]/68">
                  Recent days will show up here once you&apos;ve checked in.
                </p>
              ) : (
                calendar.slice(0, 6).map((day) => (
                  <div
                    key={day.date}
                    className="flex items-center justify-between gap-3 rounded-[1.25rem] bg-[#FDFBF7]/74 p-4"
                  >
                    <div>
                      <p className="text-sm font-medium text-[#2F3E36]">{day.date}</p>
                      <p className="mt-1 text-xs text-[#2F3E36]/62">
                        {normalizeLabel(day.primary_emotion_label)} · {day.entry_count} entries
                      </p>
                    </div>
                    <span className="rounded-full bg-white/75 px-3 py-1 text-xs text-[#2F3E36]/72">
                      {formatPercent(day.average_stress_score)} stress
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
