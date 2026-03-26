import { AnimatePresence, motion } from "framer-motion"
import { useEffect, useMemo, useState } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import {
  ArrowLeft01Icon,
  ArrowRight01Icon,
  Cancel01Icon,
  Leaf02Icon,
  SparklesIcon,
} from "@hugeicons/core-free-icons"

import { DeferredSoulTree } from "~/components/home/deferred-soul-tree"
import { useAuth } from "~/context/auth-context"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "~/components/ui/dialog"
import { api } from "~/lib/api"
import type {
  CalendarDayItem,
  CheckinDetail,
  JournalHistoryItem,
  WrapupSnapshotResponse,
} from "~/lib/contracts"
import {
  clampTreeScore,
  formatEmotionLabel,
  getEmotionColor,
  isSoulEmotion,
  type SoulEmotion,
} from "~/lib/emotions"

const WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const

function startOfMonth(value: Date) {
  return new Date(value.getFullYear(), value.getMonth(), 1)
}

function addMonths(value: Date, amount: number) {
  return new Date(value.getFullYear(), value.getMonth() + amount, 1)
}

function formatMonthLabel(value: Date) {
  return value.toLocaleDateString([], { month: "long", year: "numeric" })
}

function getMonthKey(value: Date | string) {
  if (typeof value === "string") {
    return value.slice(0, 7)
  }

  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}`
}

function formatMonthSummaryLabel(value: Date) {
  return value.toLocaleDateString([], { month: "long" })
}

function formatDateLabel(value: string) {
  return new Date(value).toLocaleDateString([], {
    weekday: "long",
    month: "long",
    day: "numeric",
  })
}

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  })
}

function formatPercent(value: number | null | undefined) {
  if (typeof value !== "number") {
    return "n/a"
  }

  return `${Math.round(value * 100)}%`
}

function resolveMood(value: string | null | undefined): SoulEmotion {
  return value && isSoulEmotion(value) ? value : "neutral"
}

type CalendarCell = {
  date: string
  dayNumber: number
  entry: CalendarDayItem | null
  isCurrentMonth: boolean
}

function buildMonthCells(
  monthDate: Date,
  calendarMap: Map<string, CalendarDayItem>
): CalendarCell[] {
  const firstDay = startOfMonth(monthDate)
  const firstWeekday = firstDay.getDay()
  const gridStart = new Date(firstDay)
  gridStart.setDate(firstDay.getDate() - firstWeekday)

  return Array.from({ length: 42 }).map((_, index) => {
    const date = new Date(gridStart)
    date.setDate(gridStart.getDate() + index)
    const isoDate = date.toISOString().slice(0, 10)

    return {
      date: isoDate,
      dayNumber: date.getDate(),
      entry: calendarMap.get(isoDate) ?? null,
      isCurrentMonth: date.getMonth() === monthDate.getMonth(),
    }
  })
}

function buildDayScore(day: CalendarDayItem | null) {
  if (!day) {
    return 50
  }

  return clampTreeScore(
    54 +
      (day.average_valence_score ?? 0) * 24 -
      (day.average_stress_score ?? 0.35) * 16 +
      day.entry_count * 4
  )
}

type MonthRecapCard = {
  id: string
  accent: SoulEmotion
  eyebrow: string
  title: string
  summary: string
  stat: string
  footnote: string
  highlights: string[]
  ranking?: Array<{
    emotion: SoulEmotion
    count: number
  }>
}

function getTopEmotionLabel(counts: Record<string, number>) {
  const [label] =
    Object.entries(counts).sort((left, right) => right[1] - left[1])[0] ?? []
  return label ?? null
}

function differenceInDays(left: string, right: string) {
  const leftDate = new Date(`${left}T00:00:00`)
  const rightDate = new Date(`${right}T00:00:00`)

  return Math.round((leftDate.getTime() - rightDate.getTime()) / 86_400_000)
}

function getLongestStreak(monthCalendar: CalendarDayItem[]) {
  const dates = [...monthCalendar]
    .filter((item) => item.entry_count > 0)
    .map((item) => item.date)
    .sort()

  let longest = 0
  let current = 0
  let previousDate: string | null = null

  dates.forEach((date) => {
    if (previousDate && differenceInDays(date, previousDate) === 1) {
      current += 1
    } else {
      current = 1
    }

    if (current > longest) {
      longest = current
    }

    previousDate = date
  })

  return longest
}

function buildEmotionRanking({
  monthCalendar,
  monthEntries,
  monthlyWrapup,
}: {
  monthCalendar: CalendarDayItem[]
  monthEntries: JournalHistoryItem[]
  monthlyWrapup: WrapupSnapshotResponse | null
}) {
  const counts = new Map<SoulEmotion, number>()

  if (monthlyWrapup) {
    Object.entries(monthlyWrapup.payload.emotion_counts).forEach(([label, count]) => {
      const emotion = resolveMood(label)
      counts.set(emotion, (counts.get(emotion) ?? 0) + count)
    })
  } else if (monthEntries.length > 0) {
    monthEntries.forEach((item) => {
      const emotion = resolveMood(item.primary_label)
      counts.set(emotion, (counts.get(emotion) ?? 0) + 1)
    })
  } else {
    monthCalendar.forEach((item) => {
      const emotion = resolveMood(item.primary_emotion_label)
      counts.set(emotion, (counts.get(emotion) ?? 0) + Math.max(1, item.entry_count))
    })
  }

  return [...counts.entries()]
    .sort((left, right) => right[1] - left[1])
    .map(([emotion, count]) => ({ emotion, count }))
}

function buildMonthRecapCards({
  activeMonth,
  monthCalendar,
  monthEntries,
  monthlyWrapup,
}: {
  activeMonth: Date
  monthCalendar: CalendarDayItem[]
  monthEntries: JournalHistoryItem[]
  monthlyWrapup: WrapupSnapshotResponse | null
}) {
  const monthLabel = formatMonthSummaryLabel(activeMonth)
  const totalEntries =
    monthlyWrapup?.payload.total_entries ??
    monthEntries.length ??
    monthCalendar.reduce((total, item) => total + item.entry_count, 0)
  const activeDays =
    monthlyWrapup?.payload.total_checkin_days ??
    monthCalendar.filter((item) => item.entry_count > 0).length
  const consistencyRatio =
    monthlyWrapup?.payload.checkin_consistency.ratio ??
    (monthCalendar.length > 0 ? activeDays / monthCalendar.length : 0)
  const longestStreak =
    monthlyWrapup?.payload.streak_highlight.longest_streak_days ?? getLongestStreak(monthCalendar)
  const emotionRanking = buildEmotionRanking({
    monthCalendar,
    monthEntries,
    monthlyWrapup,
  })
  const dominantMood = emotionRanking[0]?.emotion ?? "neutral"
  const dominantCount = emotionRanking[0]?.count ?? 0
  const totalEmotionCount = emotionRanking.reduce((total, item) => total + item.count, 0)
  const dominantShare =
    totalEmotionCount > 0 ? Math.round((dominantCount / totalEmotionCount) * 100) : 0
  const runnerUp = emotionRanking[1]

  const cards: MonthRecapCard[] = [
    {
      id: "streak",
      accent: dominantMood,
      eyebrow: `${monthLabel} recap`,
      title: longestStreak > 0 ? `${longestStreak}-day longest streak` : "Your first streak starts here",
      summary:
        longestStreak > 0
          ? `You kept the habit alive and came back for ${longestStreak} days in a row.`
          : `Start checking in and your ${monthLabel} streak will appear here.`,
      stat: `${activeDays} active days`,
      footnote: `${Math.round(consistencyRatio * 100)}% consistency`,
      highlights: [
        `${totalEntries} total entries logged`,
        monthlyWrapup?.payload.streak_highlight.current_streak_days
          ? `${monthlyWrapup.payload.streak_highlight.current_streak_days}-day current streak`
          : "Streak updates as you check in",
        `${monthLabel} kept your momentum visible`,
      ],
    },
    {
      id: "ranking",
      accent: dominantMood,
      eyebrow: "Ranking",
      title: "Emotion ranking",
      summary: `These feelings showed up the most across ${monthLabel}.`,
      stat: `${emotionRanking.length || 0} emotions tracked`,
      footnote:
        emotionRanking.length > 0
          ? `${formatEmotionLabel(emotionRanking[0].emotion)} led the month`
          : "Your ranking will appear after the first check-in",
      highlights: [
        `${emotionRanking[0]?.count ?? 0} check-ins for the top emotion`,
        runnerUp
          ? `${formatEmotionLabel(runnerUp.emotion)} came in second`
          : "Second place will appear once more emotions are tracked",
        `${totalEntries} entries fed this ranking`,
      ],
      ranking: emotionRanking.slice(0, 5),
    },
    {
      id: "dominant",
      accent: dominantMood,
      eyebrow: "Top emotion",
      title: formatEmotionLabel(dominantMood),
      summary:
        dominantCount > 0
          ? `This emotion appeared more than any other during ${monthLabel}.`
          : `Your top emotion will appear once the month has more entries.`,
      stat: dominantCount > 0 ? `${dominantCount} check-ins` : "No data yet",
      footnote:
        dominantCount > 0
          ? `${dominantShare}% of tracked emotions`
          : "Keep adding entries to unlock this card",
      highlights: [
        runnerUp
          ? `${formatEmotionLabel(runnerUp.emotion)} followed right behind`
          : "A runner-up will appear with more entries",
        monthlyWrapup?.payload.notable_shift || "Monthly shifts will appear once patterns emerge",
        `${monthLabel} kept your emotional pattern easy to spot`,
      ],
    },
  ]

  return {
    cards,
    dominantMood,
    monthLabel,
    subtitle:
      totalEntries > 0
        ? `${activeDays} active days and ${totalEntries} total entries`
        : "No entries yet for this month",
  }
}

function MonthRecapTeaser({
  cardsCount,
  dominantMood,
  label,
  onOpen,
  subtitle,
}: {
  cardsCount: number
  dominantMood: SoulEmotion
  label: string
  onOpen: () => void
  subtitle: string
}) {
  const moodColor = getEmotionColor(dominantMood)

  return (
    <div className="mt-4 flex w-full items-center justify-between gap-4 rounded-[1.8rem] border border-[#DDF5EA] bg-[linear-gradient(135deg,#F2FFF8,#FFFFFF)] p-4 text-left shadow-[0_16px_44px_rgba(17,70,62,0.06)]">
      <div className="min-w-0 flex-1">
        <p className="text-xs uppercase tracking-[0.22em] text-[var(--brand-primary-muted)]">
          Monthly recap
        </p>
        <h3 className="mt-2 text-lg font-semibold text-[#163D33]">{label}</h3>
        <p className="mt-1 text-sm text-[#648078]">{subtitle}</p>
        <button
          type="button"
          onClick={onOpen}
          className="mt-4 inline-flex items-center rounded-full bg-[var(--brand-primary)] px-4 py-2 text-sm font-medium text-[var(--brand-on-primary)] transition-colors hover:bg-[var(--brand-primary-strong)]"
        >
          View recap
        </button>
      </div>

      <div className="shrink-0 text-right">
        <span
          className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl"
          style={{
            backgroundColor: `${moodColor}1f`,
            color: moodColor,
          }}
        >
          <HugeiconsIcon icon={SparklesIcon} size={20} strokeWidth={1.8} />
        </span>
        <p className="mt-2 text-xs text-[#648078]">{cardsCount} cards</p>
      </div>
    </div>
  )
}

function DayDetails({
  pageStatus,
  selectedDate,
  selectedDay,
  selectedDetails,
  selectedEntries,
}: {
  pageStatus: "idle" | "loading" | "ready" | "error"
  selectedDate: string
  selectedDay: CalendarDayItem | null
  selectedDetails: Record<string, CheckinDetail>
  selectedEntries: JournalHistoryItem[]
}) {
  const selectedMood = resolveMood(selectedDay?.primary_emotion_label)
  const selectedMoodColor = getEmotionColor(selectedMood)
  const selectedTreeScore = buildDayScore(selectedDay)

  return (
    <div className="space-y-4">
      <div className="rounded-[2rem] bg-white/88 p-5 shadow-[0_18px_60px_rgba(17,70,62,0.08)]">
        <p className="text-xs uppercase tracking-[0.22em] text-[var(--brand-primary-muted)]">
          Selected day
        </p>
        <h2 className="mt-2 text-xl font-semibold text-[#163D33]">
          {formatDateLabel(selectedDate)}
        </h2>

        <div className="mt-4 rounded-[1.6rem] bg-[linear-gradient(180deg,#F4FFF9,#FFFFFF)] p-4">
          <DeferredSoulTree
            emotion={selectedMood}
            score={selectedTreeScore}
            deferMs={80}
            className="h-56 rounded-[1.4rem] border-0 bg-transparent shadow-none"
          />
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="rounded-[1.35rem] bg-[#F2FFF8] p-4">
            <div className="flex items-center gap-3">
              <span
                className="flex h-10 w-10 items-center justify-center rounded-2xl"
                style={{
                  backgroundColor: `${selectedMoodColor}22`,
                  color: selectedMoodColor,
                }}
              >
                <HugeiconsIcon icon={Leaf02Icon} size={18} strokeWidth={1.8} />
              </span>
              <div>
                <p className="text-sm text-[#648078]">Mood</p>
                <p className="text-base font-semibold text-[#163D33]">
                  {selectedDay ? formatEmotionLabel(selectedMood) : "No data"}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-[1.35rem] bg-[#EEFFF7] p-4">
            <p className="text-sm text-[#648078]">Entries</p>
            <p className="mt-2 text-2xl font-semibold text-[#163D33]">
              {selectedDay?.entry_count ?? 0}
            </p>
          </div>
        </div>

        <div className="mt-3 grid grid-cols-2 gap-3">
          <div className="rounded-[1.35rem] bg-[#FFF7DB] p-4">
            <p className="text-sm text-[#8C6800]">Stress</p>
            <p className="mt-2 text-lg font-semibold text-[#6F5100]">
              {formatPercent(selectedDay?.average_stress_score)}
            </p>
          </div>
          <div className="rounded-[1.35rem] bg-[#EDF8FF] p-4">
            <p className="text-sm text-[#24678A]">Valence</p>
            <p className="mt-2 text-lg font-semibold text-[#164A66]">
              {formatPercent(selectedDay?.average_valence_score)}
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-[2rem] bg-white/88 p-5 shadow-[0_18px_60px_rgba(17,70,62,0.08)]">
        <div className="flex items-center gap-2">
          <HugeiconsIcon
            icon={SparklesIcon}
            size={18}
            strokeWidth={1.8}
            className="text-[var(--brand-primary-muted)]"
          />
          <p className="text-sm font-semibold text-[#163D33]">Timeline</p>
        </div>

        <div className="mt-4 space-y-3">
          {pageStatus === "loading" ? (
            <p className="text-sm text-[#648078]">Loading...</p>
          ) : selectedEntries.length === 0 ? (
            <p className="text-sm text-[#648078]">No entries for this day.</p>
          ) : (
            selectedEntries.map((item) => {
              const detail = selectedDetails[item.entry_id]
              const mood = resolveMood(detail?.primary_label ?? item.primary_label)
              const moodColor = getEmotionColor(mood)
              const transcript =
                detail?.transcript_text ||
                item.transcript_excerpt ||
                "No transcript saved for this entry."

              return (
                <div key={item.id} className="rounded-[1.35rem] bg-[#F8FFFC] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span
                        className="rounded-full px-3 py-1 text-xs"
                        style={{
                          backgroundColor: `${moodColor}20`,
                          color: moodColor,
                        }}
                      >
                        {formatEmotionLabel(mood)}
                      </span>
                      <span className="text-xs text-[#648078]">
                        {item.source_type === "text" ? "Text" : "Voice"}
                      </span>
                    </div>
                    <span className="text-xs text-[#648078]">
                      {formatTime(item.created_at)}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-[#234640]">{transcript}</p>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}

export default function JournalPage() {
  const { token, user } = useAuth()
  const [calendar, setCalendar] = useState<CalendarDayItem[]>([])
  const [history, setHistory] = useState<JournalHistoryItem[]>([])
  const [latestMonthlyWrapup, setLatestMonthlyWrapup] = useState<WrapupSnapshotResponse | null>(
    null
  )
  const [selectedDetails, setSelectedDetails] = useState<Record<string, CheckinDetail>>({})
  const [pageStatus, setPageStatus] = useState<"idle" | "loading" | "ready" | "error">(
    "idle"
  )
  const [pageError, setPageError] = useState<string | null>(null)
  const [isMobileDetailsOpen, setIsMobileDetailsOpen] = useState(false)
  const [isRecapOpen, setIsRecapOpen] = useState(false)
  const [monthOffset, setMonthOffset] = useState(0)
  const [recapIndex, setRecapIndex] = useState(0)
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().slice(0, 10))

  useEffect(() => {
    if (!token || !user) {
      setCalendar([])
      setHistory([])
      setLatestMonthlyWrapup(null)
      setSelectedDetails({})
      return
    }

    const accessToken = token
    const currentUser = user
    let cancelled = false

    async function loadJournal() {
      setPageStatus("loading")
      setPageError(null)

      try {
        const [calendarResult, historyResult, monthlyWrapupResult] = await Promise.allSettled([
          api.getCalendar(accessToken, 120),
          api.getHistory(accessToken, currentUser.id, 120, 0),
          api.getLatestMonthlyWrapup(accessToken),
        ])

        if (calendarResult.status !== "fulfilled") {
          throw calendarResult.reason
        }

        if (historyResult.status !== "fulfilled") {
          throw historyResult.reason
        }

        if (cancelled) {
          return
        }

        setCalendar(calendarResult.value.items)
        setHistory(historyResult.value.items)
        setLatestMonthlyWrapup(
          monthlyWrapupResult.status === "fulfilled" ? monthlyWrapupResult.value : null
        )
        setPageStatus("ready")
      } catch (error) {
        if (cancelled) {
          return
        }

        setPageStatus("error")
        setPageError(error instanceof Error ? error.message : "Unable to load the journal.")
      }
    }

    void loadJournal()

    return () => {
      cancelled = true
    }
  }, [token, user])

  const activeMonth = useMemo(
    () => addMonths(startOfMonth(new Date()), monthOffset),
    [monthOffset]
  )
  const activeMonthKey = useMemo(() => getMonthKey(activeMonth), [activeMonth])
  const calendarMap = useMemo(
    () => new Map(calendar.map((item) => [item.date, item])),
    [calendar]
  )
  const monthCells = useMemo(
    () => buildMonthCells(activeMonth, calendarMap),
    [activeMonth, calendarMap]
  )

  useEffect(() => {
    const hasSelectedDateInMonth = monthCells.some((cell) => cell.date === selectedDate)

    if (!hasSelectedDateInMonth) {
      const firstCurrentMonthCell = monthCells.find((cell) => cell.isCurrentMonth)
      if (firstCurrentMonthCell) {
        setSelectedDate(firstCurrentMonthCell.date)
      }
    }
  }, [monthCells, selectedDate])

  const selectedEntries = useMemo(
    () =>
      history
        .filter((item) => item.created_at.slice(0, 10) === selectedDate)
        .sort((left, right) => left.created_at.localeCompare(right.created_at)),
    [history, selectedDate]
  )
  const monthCalendar = useMemo(
    () => calendar.filter((item) => getMonthKey(item.date) === activeMonthKey),
    [activeMonthKey, calendar]
  )
  const monthEntries = useMemo(
    () => history.filter((item) => getMonthKey(item.created_at) === activeMonthKey),
    [activeMonthKey, history]
  )
  const activeMonthWrapup = useMemo(() => {
    if (!latestMonthlyWrapup) {
      return null
    }

    return getMonthKey(latestMonthlyWrapup.period_start) === activeMonthKey
      ? latestMonthlyWrapup
      : null
  }, [activeMonthKey, latestMonthlyWrapup])
  const monthRecap = useMemo(
    () =>
      buildMonthRecapCards({
        activeMonth,
        monthCalendar,
        monthEntries,
        monthlyWrapup: activeMonthWrapup,
      }),
    [activeMonth, activeMonthWrapup, monthCalendar, monthEntries]
  )

  useEffect(() => {
    if (!token || selectedEntries.length === 0) {
      setSelectedDetails({})
      return
    }

    const accessToken = token
    let cancelled = false

    async function loadSelectedDetails() {
      const results = await Promise.allSettled(
        selectedEntries.map((item) => api.getCheckin(accessToken, item.entry_id))
      )

      if (cancelled) {
        return
      }

      const nextDetails: Record<string, CheckinDetail> = {}

      results.forEach((result, index) => {
        const entryId = selectedEntries[index]?.entry_id

        if (!entryId || result.status !== "fulfilled") {
          return
        }

        nextDetails[entryId] = result.value
      })

      setSelectedDetails(nextDetails)
    }

    void loadSelectedDetails()

    return () => {
      cancelled = true
    }
  }, [selectedEntries, token])

  useEffect(() => {
    setRecapIndex(0)
  }, [activeMonthKey, isRecapOpen])

  const selectedDay = calendarMap.get(selectedDate) ?? null
  const activeRecapCard = monthRecap.cards[recapIndex] ?? monthRecap.cards[0]
  const recapTreeEmotion = monthRecap.dominantMood
  const recapTreeScore = clampTreeScore(
    60 + monthEntries.length * 2 + monthCalendar.filter((item) => item.entry_count > 0).length * 3
  )
  const recapBackdropColor = getEmotionColor(recapTreeEmotion)

  return (
    <section className="min-h-[calc(100vh-8rem)] p-4 md:p-6">
      <div className="mx-auto max-w-6xl space-y-4">
        <div className="rounded-[2.2rem] bg-[linear-gradient(135deg,#E7FFF4,#F8FFFB)] p-6 shadow-[0_24px_60px_rgba(17,70,62,0.08)]">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--brand-primary-muted)]">Journal</p>
              <h1 className="mt-2 text-3xl font-semibold text-[#163D33]">Mood calendar</h1>
            </div>

            <div className="flex items-center gap-2 rounded-full bg-white/88 p-1">
              <button
                type="button"
                onClick={() => setMonthOffset((current) => current - 1)}
                className="rounded-full px-3 py-2 text-[#163D33] transition-colors hover:bg-[#F0FFF7]"
                aria-label="Previous month"
              >
                <HugeiconsIcon icon={ArrowLeft01Icon} size={18} strokeWidth={1.8} />
              </button>
              <span className="min-w-36 px-2 text-center text-sm font-medium text-[#163D33]">
                {formatMonthLabel(activeMonth)}
              </span>
              <button
                type="button"
                onClick={() => setMonthOffset((current) => current + 1)}
                className="rounded-full px-3 py-2 text-[#163D33] transition-colors hover:bg-[#F0FFF7]"
                aria-label="Next month"
              >
                <HugeiconsIcon icon={ArrowRight01Icon} size={18} strokeWidth={1.8} />
              </button>
            </div>
          </div>

          {pageError ? (
            <p className="mt-4 rounded-[1rem] bg-[#FFF1ED] px-4 py-3 text-sm text-[#A34F38]">
              {pageError}
            </p>
          ) : null}
        </div>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.75fr)]">
          <div className="space-y-4">
            <div className="min-w-0 rounded-[2rem] bg-white/88 p-3 shadow-[0_18px_60px_rgba(17,70,62,0.08)] sm:p-4 md:p-5">
              <div className="mb-3 grid grid-cols-7 gap-1 sm:mb-4 sm:gap-2">
                {WEEKDAY_LABELS.map((label) => (
                  <div
                    key={label}
                    className="px-1 py-1 text-center text-[0.62rem] uppercase tracking-[0.12em] text-[#6A8780] sm:px-2 sm:text-[0.7rem] sm:tracking-[0.18em]"
                  >
                    {label}
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-7 gap-1 sm:gap-2">
                {monthCells.map((cell) => {
                  const mood = resolveMood(cell.entry?.primary_emotion_label)
                  const moodColor = getEmotionColor(mood)
                  const isSelected = cell.date === selectedDate

                  return (
                    <button
                      key={cell.date}
                      type="button"
                      onClick={() => {
                        setSelectedDate(cell.date)
                        if (typeof window !== "undefined" && window.innerWidth < 1280) {
                          setIsMobileDetailsOpen(true)
                        }
                      }}
                      className={`aspect-square min-w-0 rounded-[1rem] border p-1.5 text-left transition-transform hover:-translate-y-0.5 sm:rounded-[1.35rem] sm:p-2 ${
                        isSelected
                          ? "border-[var(--brand-primary)] shadow-[0_12px_30px_rgba(18,199,127,0.14)]"
                          : "border-[#DDF5EA]"
                      } ${cell.isCurrentMonth ? "bg-white" : "bg-[#FBFFFD]"}`}
                      style={{
                        background:
                          cell.entry && cell.isCurrentMonth
                            ? `linear-gradient(180deg, ${moodColor}22, #ffffff)`
                            : undefined,
                      }}
                    >
                      <div className="flex h-full flex-col justify-between">
                        <div className="flex items-center justify-between">
                          <span
                            className={`text-[0.72rem] font-medium sm:text-sm ${
                              cell.isCurrentMonth ? "text-[#163D33]" : "text-[#A4BBB4]"
                            }`}
                          >
                            {cell.dayNumber}
                          </span>
                          <span
                            className="flex h-6 w-6 items-center justify-center rounded-lg sm:h-8 sm:w-8 sm:rounded-xl"
                            style={{
                              backgroundColor: cell.entry ? `${moodColor}22` : "#F2FBF7",
                              color: cell.entry ? moodColor : "#A4BBB4",
                            }}
                          >
                            <HugeiconsIcon
                              icon={Leaf02Icon}
                              size={12}
                              strokeWidth={1.8}
                              className="sm:size-[15px]"
                            />
                          </span>
                        </div>
                        <p className="text-[0.58rem] text-[#648078] sm:text-[0.68rem]">
                          {cell.entry?.entry_count ?? 0}
                        </p>
                      </div>
                    </button>
                  )
                })}
              </div>

              <MonthRecapTeaser
                cardsCount={monthRecap.cards.length}
                dominantMood={monthRecap.dominantMood}
                label={`${monthRecap.monthLabel} stories`}
                onOpen={() => {
                  setRecapIndex(0)
                  setIsRecapOpen(true)
                }}
                subtitle={monthRecap.subtitle}
              />
            </div>
          </div>

          <aside className="hidden xl:block">
            <div className="max-h-[calc(100svh-12rem)] overflow-y-auto overscroll-contain pr-1">
              <DayDetails
                pageStatus={pageStatus}
                selectedDate={selectedDate}
                selectedDay={selectedDay}
                selectedDetails={selectedDetails}
                selectedEntries={selectedEntries}
              />
            </div>
          </aside>
        </div>

        <Dialog open={isMobileDetailsOpen} onOpenChange={setIsMobileDetailsOpen}>
          <DialogContent className="flex h-[88svh] w-[min(94vw,36rem)] flex-col overflow-hidden rounded-[1.8rem] p-0 xl:hidden">
            <DialogHeader className="border-b border-[#DDF5EA] bg-[linear-gradient(135deg,#F2FFF8,#FFFFFF)] p-5">
              <div className="flex justify-end">
                <DialogClose className="flex h-10 w-10 items-center justify-center rounded-full bg-white text-[#163D33] transition-colors hover:bg-[#F2FFF8]">
                  <HugeiconsIcon icon={Cancel01Icon} size={18} strokeWidth={1.8} />
                  <span className="sr-only">Close details</span>
                </DialogClose>
              </div>
              <DialogTitle className="text-[#163D33]">Day details</DialogTitle>
              <DialogDescription>{formatDateLabel(selectedDate)}</DialogDescription>
            </DialogHeader>
            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4">
              <DayDetails
                pageStatus={pageStatus}
                selectedDate={selectedDate}
                selectedDay={selectedDay}
                selectedDetails={selectedDetails}
                selectedEntries={selectedEntries}
              />
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={isRecapOpen} onOpenChange={setIsRecapOpen}>
          <DialogContent className="h-[84svh] w-[min(92vw,26rem)] overflow-hidden rounded-[2rem] border-0 p-0">
            <DialogTitle className="sr-only">{monthRecap.monthLabel} recap</DialogTitle>
            <DialogDescription className="sr-only">
              A compact monthly story, one card at a time.
            </DialogDescription>

            <div className="relative h-full overflow-hidden bg-[#08150f]">
              <motion.div
                aria-hidden="true"
                className="absolute -left-12 top-10 h-40 w-40 rounded-full bg-[#1ed760]/35 blur-3xl"
                animate={{ x: [-10, 24, -10], y: [0, 18, 0], scale: [1, 1.18, 1] }}
                transition={{ duration: 12, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
              />
              <motion.div
                aria-hidden="true"
                className="absolute right-[-2rem] top-1/3 h-56 w-56 rounded-full bg-[#40c9ff]/28 blur-3xl"
                animate={{ x: [0, -26, 0], y: [0, -12, 0], scale: [1.05, 0.95, 1.05] }}
                transition={{ duration: 14, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
              />
              <motion.div
                aria-hidden="true"
                className="absolute bottom-[-3rem] left-1/3 h-48 w-48 rounded-full bg-[#ffd84d]/18 blur-3xl"
                animate={{ x: [0, 18, 0], y: [0, -24, 0], scale: [0.95, 1.1, 0.95] }}
                transition={{ duration: 16, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
              />

              <div className="absolute inset-x-3 top-3 z-20 rounded-[1.35rem] border border-white/12 bg-black/18 p-3 text-white shadow-[0_18px_40px_rgba(0,0,0,0.2)] backdrop-blur-xl">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[0.68rem] uppercase tracking-[0.22em] text-white/62">
                      Monthly recap
                    </p>
                    <p className="mt-1 truncate text-lg font-semibold text-white">
                      {monthRecap.monthLabel}
                    </p>
                  </div>
                  <DialogClose className="flex h-9 w-9 items-center justify-center rounded-full bg-white/12 text-white transition-colors hover:bg-white/20">
                    <HugeiconsIcon icon={Cancel01Icon} size={18} strokeWidth={1.8} />
                    <span className="sr-only">Close recap</span>
                  </DialogClose>
                </div>

                <div className="mt-3 flex gap-2">
                  {monthRecap.cards.map((card, index) => (
                    <button
                      key={card.id}
                      type="button"
                      onClick={() => setRecapIndex(index)}
                      className="h-1.5 flex-1 rounded-full transition-opacity"
                      style={{
                        backgroundColor:
                          index === recapIndex ? "#ffffff" : "rgba(255,255,255,0.28)",
                        opacity: index === recapIndex ? 1 : 0.75,
                      }}
                      aria-label={`Open recap card ${index + 1}`}
                    />
                  ))}
                </div>
              </div>

              <div className="absolute inset-x-3 bottom-3 z-20 rounded-[1.35rem] border border-white/12 bg-black/18 p-3 text-white shadow-[0_18px_40px_rgba(0,0,0,0.2)] backdrop-blur-xl">
                <div className="flex items-center justify-between gap-3">
                  <button
                    type="button"
                    onClick={() => setRecapIndex((current) => Math.max(0, current - 1))}
                    disabled={recapIndex === 0}
                    className="flex items-center gap-2 rounded-full border border-white/14 bg-white/8 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-white/14 disabled:cursor-not-allowed disabled:opacity-45"
                  >
                    <HugeiconsIcon icon={ArrowLeft01Icon} size={16} strokeWidth={1.8} />
                    Previous
                  </button>

                  <p className="text-sm text-white/70">
                    {recapIndex + 1} / {monthRecap.cards.length}
                  </p>

                  <button
                    type="button"
                    onClick={() =>
                      setRecapIndex((current) =>
                        Math.min(monthRecap.cards.length - 1, current + 1)
                      )
                    }
                    disabled={recapIndex === monthRecap.cards.length - 1}
                    className="flex items-center gap-2 rounded-full bg-[var(--brand-primary)] px-4 py-2 text-sm font-medium text-[var(--brand-on-primary)] transition-colors hover:bg-[var(--brand-primary-strong)] disabled:cursor-not-allowed disabled:opacity-45"
                  >
                    Next
                    <HugeiconsIcon icon={ArrowRight01Icon} size={16} strokeWidth={1.8} />
                  </button>
                </div>
              </div>

              <div className="relative z-10 flex h-full items-center justify-center px-3 pb-20 pt-20">
                <div className="pointer-events-none absolute inset-[0.75rem] z-0 overflow-hidden rounded-[1.75rem] border border-white/12 bg-black/18 shadow-[0_30px_80px_rgba(0,0,0,0.28)] backdrop-blur-xl">
                  <DeferredSoulTree
                    emotion={recapTreeEmotion}
                    score={recapTreeScore}
                    deferMs={0}
                    className="h-full rounded-[1.75rem] border-0 bg-transparent opacity-45 shadow-none"
                  />
                  <div
                    className="absolute inset-0 rounded-[1.75rem]"
                    style={{
                      background: `linear-gradient(160deg, ${recapBackdropColor}cc, rgba(8,21,15,0.82) 52%, rgba(8,21,15,0.94) 100%)`,
                    }}
                  />
                </div>

                <AnimatePresence mode="wait">
                  {activeRecapCard ? (
                    <motion.div
                      key={activeRecapCard.id}
                      initial={{ opacity: 0, x: 48, scale: 0.96 }}
                      animate={{ opacity: 1, x: 0, scale: 1 }}
                      exit={{ opacity: 0, x: -48, scale: 0.96 }}
                      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                      className="relative z-10 w-full rounded-[1.75rem] p-4 text-white md:p-4"
                    >
                      <div className="grid gap-4">
                        <div className="min-w-0">
                          <p className="text-[0.68rem] uppercase tracking-[0.24em] text-white/70">
                            {activeRecapCard.eyebrow}
                          </p>
                          <h3 className="mt-3 text-[1.9rem] font-semibold leading-tight">
                            {activeRecapCard.title}
                          </h3>
                          <p className="mt-3 text-sm leading-6 text-white/84">
                            {activeRecapCard.summary}
                          </p>
                        </div>

                        <div className="mt-3 grid gap-3">
                          <div className="rounded-[1.35rem] bg-white/14 p-4">
                            <p className="text-[0.68rem] uppercase tracking-[0.22em] text-white/66">
                              Highlight
                            </p>
                            <p className="mt-2 text-xl font-semibold">
                              {activeRecapCard.stat}
                            </p>
                          </div>
                          <div className="rounded-[1.35rem] bg-white/10 p-4">
                            <p className="text-[0.68rem] uppercase tracking-[0.22em] text-white/66">
                              Note
                            </p>
                            <p className="mt-2 text-sm leading-6 text-white/90">
                              {activeRecapCard.footnote}
                            </p>
                          </div>
                        </div>

                        {activeRecapCard.ranking && activeRecapCard.ranking.length > 0 ? (
                          <div className="mt-1 space-y-2">
                            {activeRecapCard.ranking.map((item, index) => (
                              <div
                                key={`${item.emotion}-${index}`}
                                className="flex items-center justify-between rounded-[1.15rem] bg-black/18 px-4 py-3"
                              >
                                <div className="flex items-center gap-3">
                                  <span className="w-5 text-sm text-white/62">{index + 1}</span>
                                  <span
                                    className="h-3 w-3 rounded-full"
                                    style={{ backgroundColor: getEmotionColor(item.emotion) }}
                                  />
                                  <span className="text-sm font-medium text-white/92">
                                    {formatEmotionLabel(item.emotion)}
                                  </span>
                                </div>
                                <span className="text-sm text-white/72">{item.count}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="mt-1 grid gap-3">
                            {activeRecapCard.highlights.map((item) => (
                              <div
                                key={item}
                                className="rounded-[1.15rem] bg-black/18 p-4 text-sm leading-6 text-white/90"
                              >
                                {item}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ) : null}
                </AnimatePresence>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </section>
  )
}
