import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react"

type MoodTone = "Calm" | "Reflective" | "Stressed" | "Hopeful"
type ThemeName = "forest-dawn"

type TimelineEntry = {
  id: string
  day: string
  time: string
  mood: MoodTone
  moodColor: string
  summary: string
  quote: string
}

type AnalysisResult = {
  mood: MoodTone
  intensity: number
  transcript: string
  quote: string
  recordedAt: string
}

type SoulForestContextValue = {
  currentMood: MoodTone
  intensity: number
  theme: ThemeName
  timeline: TimelineEntry[]
  lastQuote: string
  addVoiceReflection: (result: AnalysisResult) => void
}

const initialTimeline: TimelineEntry[] = [
  {
    id: "1",
    day: "Today",
    time: "8:10 AM",
    mood: "Calm",
    moodColor: "#81B29A",
    summary: "A quiet start after stretching and tea.",
    quote: "Small soft mornings can carry the whole day.",
  },
  {
    id: "2",
    day: "Yesterday",
    time: "9:42 PM",
    mood: "Reflective",
    moodColor: "#A8C3D8",
    summary: "Processed a hard conversation and noticed relief settling in.",
    quote: "Understanding often arrives after the storm has passed.",
  },
  {
    id: "3",
    day: "Tuesday",
    time: "1:25 PM",
    mood: "Stressed",
    moodColor: "#E07A5F",
    summary: "Work felt loud, but naming that pressure helped release it.",
    quote: "Pressure softens when it is witnessed with honesty.",
  },
  {
    id: "4",
    day: "Monday",
    time: "7:00 PM",
    mood: "Hopeful",
    moodColor: "#7E9F8B",
    summary: "Finished the day with more space in the body than expected.",
    quote: "Hope grows in the places we keep tending.",
  },
]

const SoulForestContext = createContext<SoulForestContextValue | null>(null)

export function SoulForestProvider({ children }: { children: ReactNode }) {
  const [currentMood, setCurrentMood] = useState<MoodTone>("Calm")
  const [intensity, setIntensity] = useState(42)
  const [timeline, setTimeline] = useState<TimelineEntry[]>(initialTimeline)
  const [lastQuote, setLastQuote] = useState(
    "Your roots already know how to hold what today brought."
  )

  const value = useMemo<SoulForestContextValue>(
    () => ({
      currentMood,
      intensity,
      theme: "forest-dawn",
      timeline,
      lastQuote,
      addVoiceReflection(result) {
        const moodColors: Record<MoodTone, string> = {
          Calm: "#81B29A",
          Reflective: "#A8C3D8",
          Stressed: "#E07A5F",
          Hopeful: "#7E9F8B",
        }

        setCurrentMood(result.mood)
        setIntensity(result.intensity)
        setLastQuote(result.quote)
        setTimeline((previous) => [
          {
            id: crypto.randomUUID(),
            day: "Today",
            time: result.recordedAt,
            mood: result.mood,
            moodColor: moodColors[result.mood],
            summary: result.transcript,
            quote: result.quote,
          },
          ...previous,
        ])
      },
    }),
    [currentMood, intensity, lastQuote, timeline]
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
