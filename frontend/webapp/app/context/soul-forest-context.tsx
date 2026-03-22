import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import { useAuth } from "~/context/auth-context"
import { api } from "~/lib/api"
import type { CheckinDetail, HomeResponse, JournalHistoryItem } from "~/lib/contracts"
import {
  INITIAL_TREE_SCORE,
  SOUL_EMOTIONS,
  calculateEmotionDelta,
  clampTreeScore,
  getEmotionColor,
  type SoulEmotion,
} from "~/lib/emotions"

type ThemeName = "forest-dawn"

export type TimelineEntry = {
  id: string
  day: string
  time: string
  mood: SoulEmotion
  moodColor: string
  summary: string
  quote: string
  createdAt: string
  entryId?: string
  stressScore?: number | null
}

const EMPTY_TIMELINE: TimelineEntry[] = []

type SoulForestContextValue = {
  currentMood: SoulEmotion
  home: HomeResponse | null
  homeError: string | null
  homeStatus: "idle" | "loading" | "ready" | "error"
  intensity: number
  lastQuote: string
  theme: ThemeName
  timeline: TimelineEntry[]
  treeScore: number
  latestCheckin: CheckinDetail | null
  refreshHome: () => Promise<void>
  syncCheckinResult: (result: CheckinDetail) => void
  setEmotion: (emotion: SoulEmotion) => void
}

const SoulForestContext = createContext<SoulForestContextValue | null>(null)

function startOfToday(value: Date) {
  const copy = new Date(value)
  copy.setHours(0, 0, 0, 0)
  return copy
}

function formatTimelineDay(isoString: string) {
  const value = new Date(isoString)
  const now = new Date()
  const today = startOfToday(now).getTime()
  const date = startOfToday(value).getTime()
  const diffDays = Math.round((today - date) / 86400000)

  if (diffDays <= 0) {
    return "Today"
  }

  if (diffDays === 1) {
    return "Yesterday"
  }

  return value.toLocaleDateString([], { weekday: "long" })
}

function formatTimelineTime(isoString: string) {
  return new Date(isoString).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  })
}

function coerceMood(value: string | null | undefined): SoulEmotion {
  if (!value) {
    return "neutral"
  }

  return SOUL_EMOTIONS.includes(value as SoulEmotion)
    ? (value as SoulEmotion)
    : "neutral"
}

function buildQuoteFromCheckin(result: CheckinDetail) {
  return (
    result.ai_response ||
    result.empathetic_response ||
    result.follow_up_question ||
    result.gentle_suggestion ||
    result.quote_text ||
    "Your roots already know how to hold what today brought."
  )
}

function mapHistoryItemToTimelineEntry(item: JournalHistoryItem): TimelineEntry {
  const mood = coerceMood(item.primary_label)

  return {
    id: item.id,
    entryId: item.entry_id,
    day: formatTimelineDay(item.created_at),
    time: formatTimelineTime(item.created_at),
    mood,
    moodColor: getEmotionColor(mood),
    summary:
      item.transcript_excerpt ||
      item.ai_response_excerpt ||
      "A check-in was recorded.",
    quote: item.ai_response_excerpt || "A response was saved for this moment.",
    createdAt: item.created_at,
    stressScore: item.stress_score,
  }
}

function mapCheckinToTimelineEntry(result: CheckinDetail): TimelineEntry {
  const mood = coerceMood(result.primary_label)

  return {
    id: result.entry_id,
    entryId: result.entry_id,
    day: formatTimelineDay(result.created_at),
    time: formatTimelineTime(result.created_at),
    mood,
    moodColor: getEmotionColor(mood),
    summary: result.transcript_text || "A reflection was captured.",
    quote: buildQuoteFromCheckin(result),
    createdAt: result.created_at,
    stressScore: result.stress_score,
  }
}

export function SoulForestProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, isReady, token, user } = useAuth()
  const [currentMoodOverride, setCurrentMoodOverride] =
    useState<SoulEmotion | null>(null)
  const [currentMood, setCurrentMood] = useState<SoulEmotion>("neutral")
  const [home, setHome] = useState<HomeResponse | null>(null)
  const [homeError, setHomeError] = useState<string | null>(null)
  const [homeStatus, setHomeStatus] = useState<"idle" | "loading" | "ready" | "error">(
    "idle"
  )
  const [intensity, setIntensity] = useState(42)
  const [timeline, setTimeline] = useState<TimelineEntry[]>(EMPTY_TIMELINE)
  const [treeScore, setTreeScore] = useState(INITIAL_TREE_SCORE)
  const [latestCheckin, setLatestCheckin] = useState<CheckinDetail | null>(null)
  const [lastQuote, setLastQuote] = useState(
    "Your roots already know how to hold what today brought."
  )

  useEffect(() => {
    if (!isReady || !isAuthenticated || !token || !user) {
      if (isReady && !isAuthenticated) {
        setHome(null)
        setHomeError(null)
        setHomeStatus("idle")
        setTimeline(EMPTY_TIMELINE)
        setCurrentMood("neutral")
        setCurrentMoodOverride(null)
        setTreeScore(INITIAL_TREE_SCORE)
        setLatestCheckin(null)
      }
      return
    }

    const accessToken = token
    const currentUser = user
    let cancelled = false

    async function loadHome() {
      setHomeStatus("loading")
      setHomeError(null)

      try {
        const [homeResponse, historyResponse] = await Promise.all([
          api.getHome(accessToken),
          api.getHistory(accessToken, currentUser.id, 12, 0),
        ])

        if (cancelled) {
          return
        }

        const mappedTimeline =
          historyResponse.items.length > 0
            ? historyResponse.items.map(mapHistoryItemToTimelineEntry)
            : EMPTY_TIMELINE
        const latestTimelineEntry = mappedTimeline[0]
        const mood = coerceMood(
          homeResponse.today.latest_emotion_label ?? latestTimelineEntry?.mood
        )

        setHome(homeResponse)
        setTimeline(mappedTimeline)
        setCurrentMood(mood)
        setTreeScore(clampTreeScore(homeResponse.tree.vitality_score))
        setIntensity(
          Math.round((latestTimelineEntry?.stressScore ?? 0.42) * 100)
        )
        setLastQuote(
          homeResponse.quote?.short_text ??
            latestTimelineEntry?.quote ??
            "Your roots already know how to hold what today brought."
        )
        setHomeStatus("ready")
      } catch (error) {
        if (cancelled) {
          return
        }

        setHomeStatus("error")
        setHomeError(
          error instanceof Error ? error.message : "Failed to load dashboard data."
        )
      }
    }

    void loadHome()

    return () => {
      cancelled = true
    }
  }, [isAuthenticated, isReady, token, user])

  useEffect(() => {
    if (currentMoodOverride) {
      setCurrentMood(currentMoodOverride)
      return
    }

    const homeMood = coerceMood(home?.today.latest_emotion_label)
    if (homeMood !== "neutral" || home?.today.latest_emotion_label) {
      setCurrentMood(homeMood)
      return
    }

    const latestEntry = timeline[0]
    setCurrentMood(latestEntry?.mood ?? "neutral")
  }, [currentMoodOverride, home?.today.latest_emotion_label, timeline])

  const value = useMemo<SoulForestContextValue>(
    () => ({
      currentMood,
      home,
      homeError,
      homeStatus,
      intensity,
      lastQuote,
      theme: "forest-dawn",
      timeline,
      treeScore,
      latestCheckin,
      async refreshHome() {
        if (!token || !user) {
          return
        }

        const accessToken = token
        const currentUser = user
        setHomeStatus("loading")
        setHomeError(null)

        try {
          const [homeResponse, historyResponse] = await Promise.all([
            api.getHome(accessToken),
            api.getHistory(accessToken, currentUser.id, 12, 0),
          ])

          const mappedTimeline =
            historyResponse.items.length > 0
              ? historyResponse.items.map(mapHistoryItemToTimelineEntry)
              : EMPTY_TIMELINE

          setHome(homeResponse)
          setTimeline(mappedTimeline)
          setCurrentMood(
            coerceMood(
              homeResponse.today.latest_emotion_label ?? mappedTimeline[0]?.mood
            )
          )
          setTreeScore(clampTreeScore(homeResponse.tree.vitality_score))
          setLastQuote(
            homeResponse.quote?.short_text ??
              mappedTimeline[0]?.quote ??
              "Your roots already know how to hold what today brought."
          )
          setHomeStatus("ready")
        } catch (error) {
          setHomeStatus("error")
          setHomeError(
            error instanceof Error
              ? error.message
              : "Failed to refresh dashboard data."
          )
        }
      },
      setEmotion(emotion) {
        setCurrentMoodOverride(emotion)
        setTreeScore((previous) =>
          clampTreeScore(previous + calculateEmotionDelta({ [emotion]: 1 }))
        )
      },
      syncCheckinResult(result) {
        const nextEntry = mapCheckinToTimelineEntry(result)

        setLatestCheckin(result)
        setCurrentMoodOverride(null)
        setCurrentMood(nextEntry.mood)
        setIntensity(Math.round((result.stress_score ?? 0) * 100))
        setLastQuote(buildQuoteFromCheckin(result))
        setTreeScore((previous) =>
          clampTreeScore(
            result.ai_analysis_complete
              ? previous + calculateEmotionDelta(result.scores)
              : previous
          )
        )
        setTimeline((previous) => [
          nextEntry,
          ...previous.filter((item) => item.id !== nextEntry.id),
        ])
      },
    }),
    [
      currentMood,
      home,
      homeError,
      homeStatus,
      intensity,
      lastQuote,
      latestCheckin,
      timeline,
      token,
      treeScore,
      user,
    ]
  )

  return (
    <SoulForestContext.Provider value={value}>
      {children}
    </SoulForestContext.Provider>
  )
}

export function useSoulForest() {
  const context = useContext(SoulForestContext)

  if (!context) {
    throw new Error("useSoulForest must be used within SoulForestProvider")
  }

  return context
}
