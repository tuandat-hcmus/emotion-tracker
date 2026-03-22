export const SOUL_EMOTIONS = [
  "joy",
  "surprise",
  "neutral",
  "sadness",
  "disgust",
  "anxiety",
  "anger",
] as const

export type SoulEmotion = (typeof SOUL_EMOTIONS)[number]

export type EmotionScoreMap = Record<SoulEmotion, number>

export type EmotionResponsePayload = {
  ai?: {
    emotion?: {
      primary_label?: string
      scores?: Partial<Record<string, number>>
    }
  }
  emotion_analysis?: {
    primary_label?: string
    scores?: Partial<Record<string, number>>
  }
}

export const TREE_SCORE_MIN = 0
export const TREE_SCORE_MAX = 100
export const INITIAL_TREE_SCORE = 50

export const EMOTION_WEIGHTS: Record<SoulEmotion, number> = {
  joy: 3,
  surprise: 2,
  neutral: 0,
  sadness: -1,
  disgust: -2,
  anxiety: -2,
  anger: -2,
}

export const EMOTION_META: Record<
  SoulEmotion,
  {
    color: string
    description: string
    gemColor: string
    label: string
    weight: number
  }
> = {
  joy: {
    color: "#FFD400",
    description: "Bright, open, and sunlit.",
    gemColor: "#FFF09B",
    label: "Joy",
    weight: EMOTION_WEIGHTS.joy,
  },
  surprise: {
    color: "#FF3E9B",
    description: "Sparked, awake, and suddenly alive.",
    gemColor: "#FF8C00",
    label: "Surprise",
    weight: EMOTION_WEIGHTS.surprise,
  },
  neutral: {
    color: "#6FAF4F",
    description: "Grounded, steady, and gently restored.",
    gemColor: "#D7F0C4",
    label: "Neutral",
    weight: EMOTION_WEIGHTS.neutral,
  },
  sadness: {
    color: "#78B7E8",
    description: "Soft, blue, and carrying rain.",
    gemColor: "#CFE8FF",
    label: "Sadness",
    weight: EMOTION_WEIGHTS.sadness,
  },
  disgust: {
    color: "#A9AEB8",
    description: "Cold, resistant, and pulling away from what feels wrong.",
    gemColor: "#D9DDE4",
    label: "Disgust",
    weight: EMOTION_WEIGHTS.disgust,
  },
  anxiety: {
    color: "#FF7A59",
    description: "Buzzing, restless, and high-strung at the edges.",
    gemColor: "#FFD400",
    label: "Anxiety",
    weight: EMOTION_WEIGHTS.anxiety,
  },
  anger: {
    color: "#D62828",
    description: "Hot, sharp, and ready to protect a boundary.",
    gemColor: "#FF8C00",
    label: "Anger",
    weight: EMOTION_WEIGHTS.anger,
  },
}

function normalizeIncomingEmotionKey(value: string) {
  if (value === "fear") {
    return "anxiety"
  }

  return value
}

export function isSoulEmotion(value: string): value is SoulEmotion {
  return SOUL_EMOTIONS.includes(normalizeIncomingEmotionKey(value) as SoulEmotion)
}

export function formatEmotionLabel(emotion: SoulEmotion) {
  return EMOTION_META[emotion].label
}

export function getEmotionColor(emotion: SoulEmotion) {
  return EMOTION_META[emotion].color
}

export function clampTreeScore(score: number) {
  return Math.min(TREE_SCORE_MAX, Math.max(TREE_SCORE_MIN, score))
}

export function normalizeEmotionScores(
  scores: Partial<Record<string, number>>
): EmotionScoreMap {
  return SOUL_EMOTIONS.reduce<EmotionScoreMap>(
    (accumulator, emotion) => {
      if (emotion === "anxiety") {
        const anxietyScore = scores.anxiety ?? scores.fear
        accumulator[emotion] =
          typeof anxietyScore === "number" ? anxietyScore : 0
        return accumulator
      }

      const value = scores[emotion]
      accumulator[emotion] = typeof value === "number" ? value : 0
      return accumulator
    },
    {
      joy: 0,
      surprise: 0,
      neutral: 0,
      sadness: 0,
      disgust: 0,
      anxiety: 0,
      anger: 0,
    }
  )
}

export function calculateEmotionDelta(scores: Partial<Record<string, number>>) {
  const normalizedScores = normalizeEmotionScores(scores)
  const totalScore = Object.values(normalizedScores).reduce(
    (sum, value) => sum + value,
    0
  )

  if (totalScore <= 0) {
    return 0
  }

  return SOUL_EMOTIONS.reduce((totalDelta, emotion) => {
    const weightedShare =
      (normalizedScores[emotion] / totalScore) * EMOTION_WEIGHTS[emotion]

    return totalDelta + weightedShare
  }, 0)
}

export function getEmotionScoresFromResponse(payload: EmotionResponsePayload) {
  return normalizeEmotionScores(
    payload.emotion_analysis?.scores ?? payload.ai?.emotion?.scores ?? {}
  )
}

export function getPrimaryEmotionFromResponse(
  payload: EmotionResponsePayload,
  fallback: SoulEmotion = "neutral"
) {
  const rawPrimary =
    payload.emotion_analysis?.primary_label ?? payload.ai?.emotion?.primary_label

  if (rawPrimary) {
    const normalizedPrimary = normalizeIncomingEmotionKey(rawPrimary)

    if (isSoulEmotion(normalizedPrimary)) {
      return normalizedPrimary
    }
  }

  const scores = getEmotionScoresFromResponse(payload)

  let strongestEmotion = fallback
  let strongestScore = scores[fallback]

  for (const emotion of SOUL_EMOTIONS) {
    if (scores[emotion] > strongestScore) {
      strongestEmotion = emotion
      strongestScore = scores[emotion]
    }
  }

  return strongestEmotion
}

export function calculateEmotionDeltaFromResponse(
  payload: EmotionResponsePayload
) {
  return calculateEmotionDelta(getEmotionScoresFromResponse(payload))
}
