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
    <section className="space-y-5 p-4 md:p-5">
      <div className="rounded-[1.75rem] border border-white/45 bg-gradient-to-br from-[#A8C3D8]/16 to-[#7E9F8B]/14 p-5">
        <p className="text-sm uppercase tracking-[0.3em] text-[#7E9F8B]">
          Journal
        </p>
        <h2 className="mt-3 text-3xl font-semibold text-[#2F3E36]">
          Text check-in, history, and wrap-up
        </h2>
        <p className="mt-3 text-sm leading-6 text-[#2F3E36]/72">
          This screen now uses the backend check-in, history, summary, calendar,
          and wrapup contracts without changing the broader app layout.
        </p>
      </div>

      <div className="rounded-[1.75rem] border border-white/45 bg-white/35 p-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
              Text check-in
            </p>
            <h3 className="mt-2 text-xl font-semibold text-[#2F3E36]">
              Submit a journal entry
            </h3>
          </div>
          <span className="rounded-full bg-white/50 px-3 py-1 text-xs text-[#2F3E36]/72">
            `POST /v1/checkins/text`
          </span>
        </div>

        <textarea
          value={text}
          onChange={(event) => {
            setText(event.target.value)
            setPreview(null)
          }}
          className="mt-4 min-h-36 w-full rounded-[1.5rem] border border-white/50 bg-[#FDFBF7]/75 p-4 text-sm leading-7 text-[#2F3E36] outline-none"
          placeholder="Write what today felt like..."
        />

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => void handlePreview()}
            disabled={isPreviewing || isSubmitting || text.trim().length === 0}
            className="rounded-full border border-white/50 bg-white/45 px-4 py-2 text-sm text-[#2F3E36] transition-colors hover:bg-white/70 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isPreviewing ? "Previewing..." : "Preview backend response"}
          </button>
          <button
            type="button"
            onClick={() => void handleSubmit()}
            disabled={isSubmitting || text.trim().length === 0}
            className="rounded-full bg-[#7E9F8B] px-4 py-2 text-sm text-white transition-colors hover:bg-[#6D8D7A] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Saving check-in..." : "Save check-in"}
          </button>
        </div>

        {pageError ? (
          <p className="mt-4 rounded-[1rem] bg-[#f4ddd4] px-4 py-3 text-sm text-[#8b4e3d]">
            {pageStatus === "error"
              ? pageError
              : `Partial data warning: ${pageError}`}
          </p>
        ) : null}

        {preview ? (
          <div className="mt-4 rounded-[1.5rem] border border-white/45 bg-[#FDFBF7]/70 p-4">
            <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
              Preview from `POST /v1/me/respond-preview`
            </p>
            <p className="mt-3 text-lg font-semibold text-[#2F3E36]">
              {normalizeLabel(preview.emotion_analysis.primary_label)} · risk{" "}
              {preview.risk_level}
            </p>
            <p className="mt-2 text-sm leading-6 text-[#2F3E36]/78">
              {preview.ai_response}
            </p>
            {preview.follow_up_question ? (
              <p className="mt-3 text-sm text-[#2F3E36]/72">
                Follow-up: {preview.follow_up_question}
              </p>
            ) : null}
            {preview.gentle_suggestion ? (
              <p className="mt-2 text-sm text-[#2F3E36]/72">
                Suggestion: {preview.gentle_suggestion}
              </p>
            ) : null}
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-[#2F3E36]/68">
              <span className="rounded-full bg-white/70 px-3 py-1">
                stress {formatPercent(preview.emotion_analysis.stress_score)}
              </span>
              {preview.topic_tags.map((tag) => (
                <span key={tag} className="rounded-full bg-white/70 px-3 py-1">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-5">
          <div className="rounded-[1.75rem] border border-white/45 bg-white/35 p-5">
            <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
              History
            </p>
            <h3 className="mt-2 text-xl font-semibold text-[#2F3E36]">
              Recent timeline
            </h3>

            <div className="mt-4 space-y-3">
              {pageStatus === "loading" ? (
                <p className="text-sm text-[#2F3E36]/68">Loading history...</p>
              ) : history.length === 0 ? (
                <p className="text-sm text-[#2F3E36]/68">
                  No history returned by the backend yet.
                </p>
              ) : (
                history.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-[1.4rem] border border-white/45 bg-[#FDFBF7]/72 p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-sm font-medium text-[#2F3E36]">
                        {normalizeLabel(item.primary_label)}
                      </p>
                      <p className="text-xs text-[#2F3E36]/56">
                        {formatDateTime(item.created_at)}
                      </p>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-[#2F3E36]/74">
                      {item.transcript_excerpt || "No transcript excerpt"}
                    </p>
                    <p className="mt-2 text-xs text-[#2F3E36]/60">
                      Response: {item.ai_response_excerpt || "No response excerpt"}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-[1.75rem] border border-white/45 bg-white/35 p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                  Wrapup
                </p>
                <h3 className="mt-2 text-xl font-semibold text-[#2F3E36]">
                  Latest {wrapupKind} wrapup
                </h3>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setWrapupKind("weekly")}
                  className={`rounded-full px-3 py-1.5 text-xs ${
                    wrapupKind === "weekly"
                      ? "bg-[#7E9F8B] text-white"
                      : "bg-white/50 text-[#2F3E36]/70"
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
                      : "bg-white/50 text-[#2F3E36]/70"
                  }`}
                >
                  Monthly
                </button>
              </div>
            </div>

            {wrapup ? (
              <div className="mt-4 space-y-4">
                <p className="text-sm leading-6 text-[#2F3E36]/74">
                  {wrapup.payload.summary_text || wrapup.payload.closing_message}
                </p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-[1.25rem] bg-[#FDFBF7]/72 p-4">
                    <p className="text-xs uppercase tracking-[0.24em] text-[#7E9F8B]">
                      Period
                    </p>
                    <p className="mt-2 text-sm text-[#2F3E36]">
                      {wrapup.payload.period_start} to {wrapup.payload.period_end}
                    </p>
                  </div>
                  <div className="rounded-[1.25rem] bg-[#FDFBF7]/72 p-4">
                    <p className="text-xs uppercase tracking-[0.24em] text-[#7E9F8B]">
                      High stress
                    </p>
                    <p className="mt-2 text-sm text-[#2F3E36]">
                      {formatPercent(wrapup.payload.high_stress_frequency)}
                    </p>
                  </div>
                </div>
                {wrapup.payload.insight_cards.slice(0, 3).map((card) => (
                  <div
                    key={`${card.kind}-${card.title}`}
                    className="rounded-[1.25rem] bg-[#FDFBF7]/72 p-4"
                  >
                    <p className="text-sm font-medium text-[#2F3E36]">{card.title}</p>
                    <p className="mt-2 text-sm leading-6 text-[#2F3E36]/72">
                      {card.summary}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-sm text-[#2F3E36]/68">
                No wrapup payload loaded.
              </p>
            )}
          </div>
        </div>

        <div className="space-y-5">
          <div className="rounded-[1.75rem] border border-white/45 bg-white/35 p-5">
            <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
              Summary
            </p>
            <h3 className="mt-2 text-xl font-semibold text-[#2F3E36]">
              30-day backend summary
            </h3>

            {summary ? (
              <div className="mt-4 space-y-3">
                <p className="text-sm leading-6 text-[#2F3E36]/74">
                  {summary.summary_text || "No summary text returned yet."}
                </p>
                <div className="flex flex-wrap gap-2 text-xs text-[#2F3E36]/68">
                  <span className="rounded-full bg-[#FDFBF7]/72 px-3 py-1">
                    entries {summary.total_entries}
                  </span>
                  <span className="rounded-full bg-[#FDFBF7]/72 px-3 py-1">
                    stress {formatPercent(summary.high_stress_frequency)}
                  </span>
                  <span className="rounded-full bg-[#FDFBF7]/72 px-3 py-1">
                    trend {summary.emotional_direction_trend}
                  </span>
                </div>
                {summary.recurring_triggers.slice(0, 4).map((trigger) => (
                  <p key={trigger} className="rounded-full bg-[#FDFBF7]/72 px-3 py-2 text-xs">
                    {trigger}
                  </p>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-sm text-[#2F3E36]/68">
                No summary payload loaded.
              </p>
            )}
          </div>

          <div className="rounded-[1.75rem] border border-white/45 bg-white/35 p-5">
            <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
              Calendar
            </p>
            <h3 className="mt-2 text-xl font-semibold text-[#2F3E36]">
              Recent check-in days
            </h3>

            <div className="mt-4 space-y-3">
              {calendar.length === 0 ? (
                <p className="text-sm text-[#2F3E36]/68">
                  No calendar data loaded.
                </p>
              ) : (
                calendar.slice(0, 8).map((day) => (
                  <div
                    key={day.date}
                    className="flex items-center justify-between gap-3 rounded-[1.25rem] bg-[#FDFBF7]/72 p-4"
                  >
                    <div>
                      <p className="text-sm font-medium text-[#2F3E36]">{day.date}</p>
                      <p className="mt-1 text-xs text-[#2F3E36]/62">
                        {normalizeLabel(day.primary_emotion_label)} · {day.entry_count} entries
                      </p>
                    </div>
                    <span className="rounded-full bg-white/70 px-3 py-1 text-xs text-[#2F3E36]/72">
                      stress {formatPercent(day.average_stress_score)}
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
