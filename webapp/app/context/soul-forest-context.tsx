import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import {
  INITIAL_TREE_SCORE,
  calculateEmotionDelta,
  clampTreeScore,
  getEmotionColor,
  type SoulEmotion,
} from "~/lib/emotions"

type ThemeName = "forest-dawn"

type TimelineEntry = {
  id: string
  day: string
  time: string
  mood: SoulEmotion
  moodColor: string
  summary: string
  quote: string
}

type AnalysisResult = {
  emotionScores?: Partial<Record<SoulEmotion, number>>
  intensity: number
  mood: SoulEmotion
  quote: string
  recordedAt: string
  transcript: string
}

type SoulForestContextValue = {
  currentMood: SoulEmotion
  intensity: number
  lastQuote: string
  theme: ThemeName
  timeline: TimelineEntry[]
  treeScore: number
  addVoiceReflection: (result: AnalysisResult) => void
  setEmotion: (emotion: SoulEmotion) => void
}

const initialTimeline: TimelineEntry[] = [
  {
    id: "1",
    day: "Today",
    time: "8:10 AM",
    mood: "joy",
    moodColor: getEmotionColor("joy"),
    summary: "A light morning opened the day with a clear breath.",
    quote: "Small soft mornings can carry the whole day.",
  },
  {
    id: "2",
    day: "Yesterday",
    time: "9:42 PM",
    mood: "sadness",
    moodColor: getEmotionColor("sadness"),
    summary: "A difficult conversation left the canopy quieter than usual.",
    quote: "Understanding often arrives after the storm has passed.",
  },
  {
    id: "3",
    day: "Tuesday",
    time: "1:25 PM",
    mood: "anxiety",
    moodColor: getEmotionColor("anxiety"),
    summary: "The afternoon felt tense, crowded, and hard to hold.",
    quote: "Pressure softens when it is witnessed with honesty.",
  },
  {
    id: "4",
    day: "Monday",
    time: "7:00 PM",
    mood: "surprise",
    moodColor: getEmotionColor("surprise"),
    summary: "A small unexpected win lifted the end of the day.",
    quote: "Hope grows in the places we keep tending.",
  },
]

function getInitialTreeScore() {
  const totalDelta = initialTimeline.reduce((sum, entry) => {
    return sum + calculateEmotionDelta({ [entry.mood]: 1 })
  }, 0)

  return clampTreeScore(INITIAL_TREE_SCORE + totalDelta)
}

const SoulForestContext = createContext<SoulForestContextValue | null>(null)

export function SoulForestProvider({ children }: { children: ReactNode }) {
  const [currentMood, setCurrentMood] = useState<SoulEmotion>("neutral")
  const [intensity, setIntensity] = useState(42)
  const [timeline, setTimeline] = useState<TimelineEntry[]>(initialTimeline)
  const [treeScore, setTreeScore] = useState(getInitialTreeScore)
  const [lastQuote, setLastQuote] = useState(
    "Your roots already know how to hold what today brought."
  )

  const value = useMemo<SoulForestContextValue>(
    () => ({
      currentMood,
      intensity,
      lastQuote,
      theme: "forest-dawn",
      timeline,
      treeScore,
      setEmotion(emotion) {
        setCurrentMood(emotion)
        setTreeScore((previous) =>
          clampTreeScore(previous + calculateEmotionDelta({ [emotion]: 1 }))
        )
      },
      addVoiceReflection(result) {
        const scoreDelta = calculateEmotionDelta(
          result.emotionScores ?? { [result.mood]: 1 }
        )

        setCurrentMood(result.mood)
        setIntensity(result.intensity)
        setLastQuote(result.quote)
        setTreeScore((previous) => clampTreeScore(previous + scoreDelta))
        setTimeline((previous) => [
          {
            id: crypto.randomUUID(),
            day: "Today",
            time: result.recordedAt,
            mood: result.mood,
            moodColor: getEmotionColor(result.mood),
            summary: result.transcript,
            quote: result.quote,
          },
          ...previous,
        ])
      },
    }),
    [currentMood, intensity, lastQuote, timeline, treeScore]
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
