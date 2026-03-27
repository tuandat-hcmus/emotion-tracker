import type {
  AIContract,
  AuthUser,
  CalendarResponse,
  CanonicalEmotion,
  CheckinDetail,
  ConversationSessionListResponse,
  ConversationSessionResponse,
  ConversationTurnListResponse,
  ConversationTurnResponse,
  EmotionAnalysis,
  HomeResponse,
  JournalHistoryItem,
  JournalHistoryResponse,
  LoginResponse,
  RegisterRequest,
  RespondPreviewResponse,
  ResponsePlan,
  ResponseQuote,
  UserSummaryResponse,
  WrapupSnapshotResponse,
} from "~/lib/contracts"

const MOCK_DB_STORAGE_KEY = "emotion-webapp-mock-db"
const MOCK_TOKEN_PREFIX = "mock-session:"
const EMOTIONS: CanonicalEmotion[] = [
  "anger",
  "disgust",
  "fear",
  "joy",
  "neutral",
  "sadness",
  "surprise",
]

type MockUserRecord = {
  user: AuthUser
  password: string
  checkins: CheckinDetail[]
  conversationSessions: ConversationSessionResponse[]
  conversationTurns: Record<string, ConversationTurnResponse[]>
}

type MockDatabase = {
  users: Record<string, MockUserRecord>
}

type ResponsePackage = {
  ai: AIContract
  aiResponse: string
  emotion: EmotionAnalysis
  followUpQuestion: string | null
  gentleSuggestion: string | null
  quote: ResponseQuote | null
  riskFlags: string[]
  riskLevel: string
  topicTags: string[]
}

const EMOTION_KEYWORDS: Record<CanonicalEmotion, string[]> = {
  anger: ["angry", "annoyed", "frustrated", "furious", "resentful", "irritated"],
  disgust: ["drained", "gross", "numb", "off", "sick", "stuck"],
  fear: ["afraid", "anxious", "nervous", "overwhelmed", "panic", "worried"],
  joy: ["calm", "excited", "good", "grateful", "happy", "proud", "relieved"],
  neutral: [],
  sadness: ["down", "empty", "lonely", "sad", "tired", "upset"],
  surprise: ["caught off guard", "shocked", "suddenly", "surprised", "unexpected"],
}

const TOPIC_MATCHERS = [
  { tag: "work", keywords: ["boss", "deadline", "meeting", "project", "work"] },
  { tag: "study", keywords: ["class", "exam", "homework", "school", "study"] },
  { tag: "family", keywords: ["dad", "family", "mom", "parent", "sister"] },
  { tag: "friends", keywords: ["friend", "friends", "hangout", "roommate"] },
  { tag: "rest", keywords: ["break", "rest", "sleep"] },
  { tag: "confidence", keywords: ["confidence", "doubt", "proud", "self"] },
] as const

function normalizeEmail(email: string) {
  return email.trim().toLowerCase()
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null
}

function createId(prefix: string) {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `${prefix}-${crypto.randomUUID()}`
  }

  return `${prefix}-${Math.random().toString(36).slice(2, 10)}-${Date.now()}`
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function startOfDay(value: Date) {
  const copy = new Date(value)
  copy.setHours(0, 0, 0, 0)
  return copy
}

function addDays(value: Date, amount: number) {
  const copy = new Date(value)
  copy.setDate(copy.getDate() + amount)
  return copy
}

function addHours(value: Date, amount: number) {
  const copy = new Date(value)
  copy.setHours(copy.getHours() + amount)
  return copy
}

function toIso(value: Date) {
  return value.toISOString()
}

function sortCheckinsDescending(checkins: CheckinDetail[]) {
  return [...checkins].sort((left, right) =>
    right.created_at.localeCompare(left.created_at)
  )
}

function countKeywordHits(text: string, keywords: string[]) {
  return keywords.reduce((count, keyword) => {
    return count + (text.includes(keyword) ? 1 : 0)
  }, 0)
}

function buildDisplayName(email: string) {
  const localPart = normalizeEmail(email).split("@")[0] ?? "demo"
  return localPart
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ")
}

function createMockToken(email: string) {
  return `${MOCK_TOKEN_PREFIX}${encodeURIComponent(normalizeEmail(email))}`
}

export function isMockToken(token: string | null | undefined) {
  return Boolean(token?.startsWith(MOCK_TOKEN_PREFIX))
}

function getEmailFromToken(token: string) {
  if (!isMockToken(token)) {
    return null
  }

  return decodeURIComponent(token.slice(MOCK_TOKEN_PREFIX.length))
}

function readDatabase(): MockDatabase {
  if (typeof window === "undefined") {
    return { users: {} }
  }

  const raw = window.localStorage.getItem(MOCK_DB_STORAGE_KEY)

  if (!raw) {
    return { users: {} }
  }

  try {
    const parsed = JSON.parse(raw) as unknown

    if (!isRecord(parsed) || !isRecord(parsed.users)) {
      return { users: {} }
    }

    return parsed as MockDatabase
  } catch {
    return { users: {} }
  }
}

function writeDatabase(database: MockDatabase) {
  if (typeof window === "undefined") {
    return
  }

  window.localStorage.setItem(MOCK_DB_STORAGE_KEY, JSON.stringify(database))
}

function withDatabase<T>(mutate: (database: MockDatabase) => T) {
  const database = readDatabase()
  const result = mutate(database)
  writeDatabase(database)
  return result
}

function buildScores(primary: CanonicalEmotion, secondary: CanonicalEmotion[]) {
  const scores = Object.fromEntries(EMOTIONS.map((emotion) => [emotion, 0.04])) as Record<
    CanonicalEmotion,
    number
  >

  scores[primary] = 0.62
  secondary.slice(0, 2).forEach((emotion, index) => {
    scores[emotion] = index === 0 ? 0.18 : 0.1
  })

  return scores
}

function inferTopics(text: string) {
  const lowerText = text.toLowerCase()
  const matches = TOPIC_MATCHERS.filter((item) =>
    item.keywords.some((keyword) => lowerText.includes(keyword))
  ).map((item) => item.tag)

  return matches.length > 0 ? matches : ["daily life"]
}

function inferEmotion(text: string, preferredEmotion?: CanonicalEmotion) {
  if (preferredEmotion) {
    return preferredEmotion
  }

  const lowerText = text.toLowerCase()
  let winningEmotion: CanonicalEmotion = "neutral"
  let winningScore = 0

  EMOTIONS.forEach((emotion) => {
    const score = countKeywordHits(lowerText, EMOTION_KEYWORDS[emotion])

    if (score > winningScore) {
      winningEmotion = emotion
      winningScore = score
    }
  })

  return winningEmotion
}

function buildResponsePackage(
  text: string,
  preferredEmotion?: CanonicalEmotion
): ResponsePackage {
  const primaryEmotion = inferEmotion(text, preferredEmotion)
  const topics = inferTopics(text)
  const secondaryLabels =
    primaryEmotion === "fear"
      ? ["sadness"]
      : primaryEmotion === "sadness"
        ? ["fear"]
        : primaryEmotion === "joy"
          ? ["surprise"]
          : primaryEmotion === "anger"
            ? ["disgust"]
            : ["neutral"]
  const secondary = secondaryLabels.filter(
    (emotion): emotion is CanonicalEmotion =>
      EMOTIONS.includes(emotion as CanonicalEmotion) &&
      emotion !== primaryEmotion
  )
  const baseStress =
    primaryEmotion === "fear"
      ? 0.76
      : primaryEmotion === "anger"
        ? 0.72
        : primaryEmotion === "sadness"
          ? 0.64
          : primaryEmotion === "joy"
            ? 0.24
            : 0.38
  const lowerText = text.toLowerCase()
  const extraStress =
    countKeywordHits(lowerText, ["deadline", "overwhelmed", "panic", "stuck"]) * 0.04
  const stressScore = clamp(baseStress + extraStress, 0.14, 0.94)
  const valenceScore =
    primaryEmotion === "joy"
      ? 0.72
      : primaryEmotion === "surprise"
        ? 0.2
        : primaryEmotion === "neutral"
          ? 0.08
          : primaryEmotion === "sadness"
            ? -0.48
            : -0.58
  const energyScore =
    primaryEmotion === "anger"
      ? 0.74
      : primaryEmotion === "fear"
        ? 0.68
        : primaryEmotion === "joy"
          ? 0.63
          : primaryEmotion === "sadness"
            ? 0.28
            : 0.42
  const socialNeedScore =
    primaryEmotion === "sadness" || primaryEmotion === "fear" ? 0.67 : 0.38
  const riskLevel = stressScore >= 0.82 ? "moderate" : "low"
  const riskFlags = stressScore >= 0.82 ? ["high_stress"] : []

  const empatheticResponseByEmotion: Record<CanonicalEmotion, string> = {
    anger:
      "That sounds like a lot to carry at once. Your frustration makes sense, especially if you have been holding it in all day.",
    disgust:
      "Something about this day felt draining or off, and it makes sense that your system is reacting to that.",
    fear:
      "It sounds like your mind has been bracing for impact. You do not have to solve everything before this moment deserves care.",
    joy:
      "There is something steady and encouraging in what you noticed. It is worth letting that moment land fully.",
    neutral:
      "You are naming the day as it is, and that kind of honest noticing still counts as real progress.",
    sadness:
      "That feels heavy. You do not need to tidy the feeling up before it gets to be held with some gentleness.",
    surprise:
      "That sounds like it caught you off guard. It makes sense that your body is still trying to catch up with the moment.",
  }

  const followUpByEmotion: Record<CanonicalEmotion, string> = {
    anger: "What part of this felt most unfair or exhausting?",
    disgust: "What would help you create a little distance from what felt draining?",
    fear: "What would make the next hour feel a little more manageable?",
    joy: "What helped this feel a little lighter than usual?",
    neutral: "If you zoom in on one part of today, what stands out most clearly?",
    sadness: "What feels most in need of kindness right now?",
    surprise: "What part of the moment are you still processing?",
  }

  const suggestionByEmotion: Record<CanonicalEmotion, string> = {
    anger: "Try giving the feeling a short name before deciding what to do next.",
    disgust: "A tiny reset like water, fresh air, or a short walk may help your system unclench.",
    fear: "Shrink the next step until it feels possible, not impressive.",
    joy: "If you can, mark what helped so it is easier to return to later.",
    neutral: "A few more honest lines may reveal what has been sitting underneath the surface.",
    sadness: "Choose the smallest comforting action you would not argue with right now.",
    surprise: "Pause long enough to notice what your body is doing before you ask it for a plan.",
  }

  const quoteByEmotion: Record<CanonicalEmotion, ResponseQuote> = {
    anger: {
      short_text: "You can be clear without abandoning your softness.",
      tone: "grounding",
      source_type: "mock-fallback",
    },
    disgust: {
      short_text: "Rest is still movement when your system needs repair.",
      tone: "grounding",
      source_type: "mock-fallback",
    },
    fear: {
      short_text: "The next gentle step is enough for now.",
      tone: "grounding",
      source_type: "mock-fallback",
    },
    joy: {
      short_text: "A steadier moment still deserves to be noticed.",
      tone: "uplifting",
      source_type: "mock-fallback",
    },
    neutral: {
      short_text: "Naming the moment is already a form of care.",
      tone: "grounding",
      source_type: "mock-fallback",
    },
    sadness: {
      short_text: "You are allowed to move slowly with what hurts.",
      tone: "grounding",
      source_type: "mock-fallback",
    },
    surprise: {
      short_text: "Give the unexpected a little room before you judge it.",
      tone: "grounding",
      source_type: "mock-fallback",
    },
  }

  const emotion: EmotionAnalysis = {
    primary_label: primaryEmotion,
    secondary_labels: secondary,
    all_labels: [primaryEmotion, ...secondary],
    scores: buildScores(primaryEmotion, secondary),
    threshold: 0.5,
    confidence: 0.78,
    provider_name: "fallback-mock-engine",
    source: "local-fallback",
    language: "en",
    valence_score: valenceScore,
    energy_score: energyScore,
    stress_score: stressScore,
    social_need_score: socialNeedScore,
    response_mode: "supportive_reflection",
    dominant_signals: secondary.length > 0 ? [primaryEmotion, ...secondary] : [primaryEmotion],
    context_tags: topics,
    enrichment_notes: ["Generated locally so the webapp can run without the backend."],
  }

  const aiResponse = `${empatheticResponseByEmotion[primaryEmotion]} ${
    suggestionByEmotion[primaryEmotion]
  }`

  return {
    ai: {
      emotion,
      state: {
        primary_label: primaryEmotion,
        secondary_labels: secondary,
        stress_score: stressScore,
        response_mode: "supportive_reflection",
        risk_level: riskLevel,
      },
      risk: {
        level: riskLevel,
        flags: riskFlags,
      },
      topics: {
        tags: topics,
      },
      response: {
        empathetic_text: empatheticResponseByEmotion[primaryEmotion],
        follow_up_question: followUpByEmotion[primaryEmotion],
        suggestion_text: suggestionByEmotion[primaryEmotion],
        composed_text: aiResponse,
        quote: quoteByEmotion[primaryEmotion],
      },
      memory: {
        recurring_triggers: topics,
        dominant_positive_patterns:
          primaryEmotion === "joy" ? ["positive momentum"] : ["honest reflection"],
      },
    },
    aiResponse,
    emotion,
    followUpQuestion: followUpByEmotion[primaryEmotion],
    gentleSuggestion: suggestionByEmotion[primaryEmotion],
    quote: quoteByEmotion[primaryEmotion],
    riskFlags,
    riskLevel,
    topicTags: topics,
  }
}

function buildResponsePlan(primaryEmotion: string | null): ResponsePlan {
  return {
    opening_style: "warm",
    acknowledgment_focus: primaryEmotion ?? "neutral",
    suggestion_allowed: true,
    suggestion_style: "gentle",
    suggestion_family: "grounding",
    quote_allowed: true,
    avoid_advice: false,
    tone: "supportive",
    max_sentences: 4,
    follow_up_question_allowed: true,
    response_variant: "fallback-preview",
    response_mode: "supportive_reflection",
    evidence_bound: false,
  }
}

function buildCheckinDetail(args: {
  createdAt: string
  preferredEmotion?: CanonicalEmotion
  sessionType?: string
  text: string
  userId: string
}) {
  const responsePackage = buildResponsePackage(args.text, args.preferredEmotion)

  return {
    entry_id: createId("entry"),
    status: "completed",
    user_id: args.userId,
    session_type: args.sessionType ?? "free",
    source_type: "text",
    audio_path: null,
    transcript_text: args.text,
    transcript_confidence: 0.99,
    transcript_source: "manual_input",
    transcript_provider: "fallback-local",
    ai_analysis_complete: true,
    latest_attempt_status: "completed",
    processing_started_at: args.createdAt,
    processing_finished_at: args.createdAt,
    ai_response: responsePackage.aiResponse,
    primary_label: responsePackage.emotion.primary_label,
    secondary_labels: responsePackage.emotion.secondary_labels,
    all_labels: responsePackage.emotion.all_labels,
    scores: responsePackage.emotion.scores,
    threshold: responsePackage.emotion.threshold,
    valence_score: responsePackage.emotion.valence_score,
    energy_score: responsePackage.emotion.energy_score,
    stress_score: responsePackage.emotion.stress_score,
    social_need_score: responsePackage.emotion.social_need_score,
    confidence: responsePackage.emotion.confidence,
    dominant_signals: responsePackage.emotion.dominant_signals,
    context_tags: responsePackage.emotion.context_tags,
    enrichment_notes: responsePackage.emotion.enrichment_notes,
    response_mode: responsePackage.emotion.response_mode,
    language: responsePackage.emotion.language,
    source: responsePackage.emotion.source,
    provider_name: responsePackage.emotion.provider_name,
    empathetic_response: responsePackage.ai.response?.empathetic_text ?? null,
    follow_up_question: responsePackage.followUpQuestion,
    gentle_suggestion: responsePackage.gentleSuggestion,
    quote_text: responsePackage.quote?.short_text ?? null,
    response_metadata: {
      mode: "fallback-local",
    },
    topic_tags: responsePackage.topicTags,
    risk_level: responsePackage.riskLevel,
    risk_flags: responsePackage.riskFlags,
    ai: responsePackage.ai,
    created_at: args.createdAt,
  } satisfies CheckinDetail
}

function buildHistoryItem(item: CheckinDetail): JournalHistoryItem {
  return {
    id: item.entry_id,
    entry_id: item.entry_id,
    status: item.status,
    session_type: item.session_type,
    source_type: item.source_type,
    local_date: item.created_at.slice(0, 10),
    transcript_excerpt: item.transcript_text,
    ai_response_excerpt: item.ai_response,
    primary_label: item.primary_label,
    secondary_labels: item.secondary_labels,
    stress_score: item.stress_score,
    created_at: item.created_at,
    updated_at: item.created_at,
  }
}

function calculateEmotionCounts(checkins: CheckinDetail[]) {
  return checkins.reduce<Record<string, number>>((counts, checkin) => {
    const key = checkin.primary_label ?? "neutral"
    counts[key] = (counts[key] ?? 0) + 1
    return counts
  }, {})
}

function average(values: Array<number | null | undefined>) {
  const valid = values.filter((value): value is number => typeof value === "number")

  if (valid.length === 0) {
    return null
  }

  return valid.reduce((sum, value) => sum + value, 0) / valid.length
}

function getCurrentStreakDays(checkins: CheckinDetail[]) {
  const uniqueDates = Array.from(
    new Set(checkins.map((item) => item.created_at.slice(0, 10)))
  ).sort((left, right) => right.localeCompare(left))

  if (uniqueDates.length === 0) {
    return 0
  }

  let streak = 0
  let cursor = startOfDay(new Date())

  for (const date of uniqueDates) {
    const isoDate = cursor.toISOString().slice(0, 10)

    if (date !== isoDate) {
      if (streak === 0) {
        cursor = addDays(cursor, -1)
        if (date !== cursor.toISOString().slice(0, 10)) {
          break
        }
      } else {
        break
      }
    }

    streak += 1
    cursor = addDays(cursor, -1)
  }

  return streak
}

function getCurrentStage(vitalityScore: number) {
  if (vitalityScore >= 80) {
    return "Steady growth"
  }

  if (vitalityScore >= 60) {
    return "Growing gently"
  }

  return "Taking root"
}

function getWeatherState(stress: number | null) {
  if (stress == null) {
    return "clear"
  }

  if (stress >= 0.75) {
    return "misty"
  }

  if (stress >= 0.5) {
    return "cloudy"
  }

  return "clear"
}

function getLeafState(vitalityScore: number) {
  if (vitalityScore >= 80) {
    return "lush"
  }

  if (vitalityScore >= 60) {
    return "steady"
  }

  return "sprouting"
}

function buildHome(record: MockUserRecord): HomeResponse {
  const sorted = sortCheckinsDescending(record.checkins)
  const todayKey = new Date().toISOString().slice(0, 10)
  const todayCheckins = sorted.filter((item) => item.created_at.startsWith(todayKey))
  const entriesLast7Days = sorted.filter((item) => {
    const diff =
      (startOfDay(new Date()).getTime() - startOfDay(new Date(item.created_at)).getTime()) /
      86400000
    return diff >= 0 && diff < 7
  })
  const averageStress7 = average(entriesLast7Days.map((item) => item.stress_score))
  const averageValence7 = average(entriesLast7Days.map((item) => item.valence_score))
  const streakDays = getCurrentStreakDays(sorted)
  const vitalityScore = clamp(
    48 +
      sorted.length * 4 +
      streakDays * 6 +
      (averageValence7 ?? 0) * 22 -
      (averageStress7 ?? 0.35) * 18,
    24,
    96
  )
  const latest = sorted[0]

  return {
    user: {
      id: record.user.id,
      email: record.user.email,
      display_name: record.user.display_name,
    },
    preferences_summary: {
      quote_opt_in: true,
      reminder_enabled: true,
      reminder_time: "08:30",
      preferred_tree_type: "forest-dawn",
      checkin_goal_per_day: 1,
    },
    today: {
      date: todayKey,
      has_morning_checkin: todayCheckins.some((item) => item.session_type == "morning"),
      has_evening_checkin: todayCheckins.some((item) => item.session_type == "evening"),
      total_entries: todayCheckins.length,
      session_types_present: Array.from(new Set(todayCheckins.map((item) => item.session_type))),
      latest_entry_id: todayCheckins[0]?.entry_id ?? latest?.entry_id ?? null,
      latest_emotion_label: todayCheckins[0]?.primary_label ?? latest?.primary_label ?? null,
      latest_risk_level: todayCheckins[0]?.risk_level ?? latest?.risk_level ?? null,
      total_entries_today: todayCheckins.length,
    },
    tree: {
      vitality_score: vitalityScore,
      streak_days: streakDays,
      current_stage: getCurrentStage(vitalityScore),
      leaf_state: getLeafState(vitalityScore),
      weather_state: getWeatherState(averageStress7),
      last_checkin_date: latest?.created_at.slice(0, 10) ?? null,
    },
    recent_trend: {
      last_7_days_average_valence: averageValence7,
      last_7_days_average_stress: averageStress7,
      entries_last_7_days: entriesLast7Days.length,
    },
    quote: latest?.quote_text
      ? {
          short_text: latest.quote_text,
          tone: "grounding",
          source_type: "mock-fallback",
        }
      : {
          short_text: "Naming the moment is already a form of care.",
          tone: "grounding",
          source_type: "mock-fallback",
        },
    latest_wrapup_meta: {
      latest_weekly_wrapup_at: latest?.created_at ?? null,
      latest_monthly_wrapup_at: latest?.created_at ?? null,
    },
  }
}

function buildUserSummary(record: MockUserRecord, days: number): UserSummaryResponse {
  const cutoff = addDays(startOfDay(new Date()), -(days - 1)).getTime()
  const relevant = sortCheckinsDescending(record.checkins).filter(
    (item) => new Date(item.created_at).getTime() >= cutoff
  )
  const emotionCounts = calculateEmotionCounts(relevant)
  const topicFrequency = relevant.reduce<Record<string, number>>((accumulator, item) => {
    item.topic_tags.forEach((tag) => {
      accumulator[tag] = (accumulator[tag] ?? 0) + 1
    })
    return accumulator
  }, {})
  const topTopics = Object.entries(topicFrequency)
    .sort((left, right) => right[1] - left[1])
    .slice(0, 4)
    .map(([tag]) => tag)
  const highStressCount = relevant.filter((item) => (item.stress_score ?? 0) >= 0.75).length
  const latest = relevant[0]

  return {
    user_id: record.user.id,
    days,
    total_entries: relevant.length,
    emotion_counts: emotionCounts,
    average_valence_score: average(relevant.map((item) => item.valence_score)),
    average_energy_score: average(relevant.map((item) => item.energy_score)),
    average_stress_score: average(relevant.map((item) => item.stress_score)),
    top_topics: topTopics,
    risk_counts: {
      low: relevant.filter((item) => item.risk_level === "low").length,
      moderate: relevant.filter((item) => item.risk_level === "moderate").length,
    },
    latest_entry_at: latest?.created_at ?? null,
    dominant_emotional_patterns: Object.entries(emotionCounts)
      .sort((left, right) => right[1] - left[1])
      .slice(0, 3)
      .map(([label]) => label),
    recurring_triggers: topTopics,
    workload_deadline_patterns: topTopics.includes("work")
      ? ["Work pressure shows up alongside higher stress."]
      : [],
    positive_anchors: relevant
      .filter((item) => item.primary_label === "joy")
      .slice(0, 2)
      .map((item) => item.quote_text ?? "A steadier moment was noticed."),
    emotional_direction_trend:
      (average(relevant.map((item) => item.valence_score)) ?? 0) >= 0
        ? "stabilizing"
        : "tender",
    high_stress_frequency: relevant.length > 0 ? highStressCount / relevant.length : 0,
    summary_text:
      relevant.length > 0
        ? `Over the last ${days} days, ${record.user.display_name ?? "you"} returned most often to ${Object.keys(emotionCounts)[0] ?? "neutral"} moments, with ${topTopics[0] ?? "daily life"} showing up as a common theme.`
        : "No entries have been captured yet in fallback mode.",
  }
}

function buildCalendar(record: MockUserRecord, days: number): CalendarResponse {
  const sorted = sortCheckinsDescending(record.checkins)
  const items = Array.from({ length: days }).map((_, index) => {
    const currentDate = addDays(startOfDay(new Date()), -index)
    const dateKey = currentDate.toISOString().slice(0, 10)
    const dayEntries = sorted.filter((item) => item.created_at.startsWith(dateKey))
    const dominantEmotion = dayEntries[0]?.primary_label ?? null

    return {
      date: dateKey,
      entry_count: dayEntries.length,
      has_morning_checkin: dayEntries.some((item) => item.session_type == "morning"),
      has_evening_checkin: dayEntries.some((item) => item.session_type == "evening"),
      primary_emotion_label: dominantEmotion,
      average_valence_score: average(dayEntries.map((item) => item.valence_score)),
      average_stress_score: average(dayEntries.map((item) => item.stress_score)),
      max_risk_level: dayEntries.some((item) => item.risk_level === "moderate")
        ? "moderate"
        : dayEntries.length > 0
          ? "low"
          : null,
      topic_tags_top: Array.from(new Set(dayEntries.flatMap((item) => item.topic_tags))).slice(
        0,
        3
      ),
      mood_color_token: dominantEmotion ?? "neutral",
    }
  })

  return {
    user_id: record.user.id,
    days,
    items,
  }
}

function buildWrapup(
  record: MockUserRecord,
  periodType: "weekly" | "monthly"
): WrapupSnapshotResponse {
  const days = periodType === "weekly" ? 7 : 30
  const periodEnd = startOfDay(new Date())
  const periodStart = addDays(periodEnd, -(days - 1))
  const relevant = sortCheckinsDescending(record.checkins).filter((item) => {
    const timestamp = new Date(item.created_at).getTime()
    return timestamp >= periodStart.getTime() && timestamp <= addDays(periodEnd, 1).getTime()
  })
  const emotionCounts = calculateEmotionCounts(relevant)
  const groupedByDay = Array.from(
    relevant.reduce((accumulator, item) => {
      const key = item.created_at.slice(0, 10)
      const items = accumulator.get(key) ?? []
      items.push(item)
      accumulator.set(key, items)
      return accumulator
    }, new Map<string, CheckinDetail[]>())
  )
  const dailySnapshots = groupedByDay.map(([date, items]) => ({
    date,
    average_valence_score: average(items.map((item) => item.valence_score)),
    average_stress_score: average(items.map((item) => item.stress_score)),
    dominant_emotion_label: items[0]?.primary_label ?? null,
    risk_level: items.some((item) => item.risk_level === "moderate") ? "moderate" : "low",
  }))
  const strongestPositiveDay = [...dailySnapshots].sort(
    (left, right) =>
      (right.average_valence_score ?? Number.NEGATIVE_INFINITY) -
      (left.average_valence_score ?? Number.NEGATIVE_INFINITY)
  )[0] ?? null
  const heaviestDay = [...dailySnapshots].sort(
    (left, right) =>
      (right.average_stress_score ?? Number.NEGATIVE_INFINITY) -
      (left.average_stress_score ?? Number.NEGATIVE_INFINITY)
  )[0] ?? null
  const highStressEntryCount = relevant.filter((item) => (item.stress_score ?? 0) >= 0.75).length
  const topTopics = Object.entries(
    relevant.reduce<Record<string, number>>((accumulator, item) => {
      item.topic_tags.forEach((tag) => {
        accumulator[tag] = (accumulator[tag] ?? 0) + 1
      })
      return accumulator
    }, {})
  )
    .sort((left, right) => right[1] - left[1])
    .slice(0, 4)
    .map(([tag]) => tag)

  return {
    id: createId(`${periodType}-wrapup`),
    user_id: record.user.id,
    period_type: periodType,
    period_start: toIso(periodStart),
    period_end: toIso(periodEnd),
    generated_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    payload: {
      period_type: periodType,
      period_start: toIso(periodStart),
      period_end: toIso(periodEnd),
      total_entries: relevant.length,
      total_checkin_days: groupedByDay.length,
      emotion_counts: emotionCounts,
      average_valence_score: average(relevant.map((item) => item.valence_score)),
      average_stress_score: average(relevant.map((item) => item.stress_score)),
      top_topics: topTopics,
      strongest_positive_day: strongestPositiveDay,
      heaviest_day: heaviestDay,
      streak_highlight: {
        longest_streak_days: getCurrentStreakDays(sortCheckinsDescending(record.checkins)),
        current_streak_days: getCurrentStreakDays(sortCheckinsDescending(record.checkins)),
      },
      checkin_consistency: {
        completed_days: groupedByDay.length,
        total_days: days,
        ratio: days > 0 ? groupedByDay.length / days : 0,
      },
      notable_shift:
        relevant[0]?.primary_label === "joy"
          ? "Recent entries suggest a little more steadiness than before."
          : "The tone of recent entries still asks for gentleness and pacing.",
      dominant_emotional_patterns: Object.entries(emotionCounts)
        .sort((left, right) => right[1] - left[1])
        .slice(0, 3)
        .map(([label]) => label),
      recurring_triggers: topTopics,
      workload_deadline_patterns: topTopics.includes("work")
        ? ["Pressure tends to rise around work-heavy entries."]
        : [],
      positive_anchors: relevant
        .filter((item) => item.primary_label === "joy")
        .slice(0, 3)
        .map((item) => item.quote_text ?? "A calmer moment appeared."),
      emotional_direction_trend:
        (average(relevant.map((item) => item.valence_score)) ?? 0) >= 0
          ? "stabilizing"
          : "mixed",
      high_stress_frequency: relevant.length > 0 ? highStressEntryCount / relevant.length : 0,
      summary_text:
        relevant.length > 0
          ? `This ${periodType} snapshot is running locally with fallback data. It still shows a believable pattern of ${topTopics[0] ?? "daily life"} and ${Object.keys(emotionCounts)[0] ?? "neutral"} moments so you can test the UI.`
          : `This ${periodType} snapshot will become richer once more mock check-ins are saved.`,
      insight_cards: [
        {
          kind: "pattern",
          title: "Dominant tone",
          summary: `Most entries leaned toward ${Object.keys(emotionCounts)[0] ?? "neutral"}.`,
          emphasis: "primary",
          items: Object.entries(emotionCounts)
            .sort((left, right) => right[1] - left[1])
            .slice(0, 3)
            .map(([label, count]) => `${label}: ${count}`),
        },
        {
          kind: "topics",
          title: "Common themes",
          summary: "These themes surfaced most often in recent reflections.",
          emphasis: null,
          items: topTopics.length > 0 ? topTopics : ["daily life"],
        },
      ],
      trend_block: {
        emotional_direction_trend:
          (average(relevant.map((item) => item.valence_score)) ?? 0) >= 0
            ? "stabilizing"
            : "mixed",
        high_stress_frequency: relevant.length > 0 ? highStressEntryCount / relevant.length : 0,
        high_stress_entry_count: highStressEntryCount,
        workload_pattern_detected: topTopics.includes("work"),
        positive_anchor_count: relevant.filter((item) => item.primary_label === "joy").length,
        recurring_trigger_count: topTopics.length,
      },
      closing_message:
        "Fallback mode is active, but your saved local entries still let the journal, calendar, and wrapups stay testable.",
    },
  }
}

function createSeedCheckins(userId: string) {
  const now = new Date()

  return [
    {
      createdAt: toIso(addHours(addDays(now, -5), -2)),
      preferredEmotion: "fear" as CanonicalEmotion,
      sessionType: "morning",
      text: "I spent most of the afternoon worrying about a deadline and I could feel the pressure building in my chest.",
    },
    {
      createdAt: toIso(addHours(addDays(now, -3), -4)),
      preferredEmotion: "sadness" as CanonicalEmotion,
      sessionType: "evening",
      text: "I felt more tired than I expected today and it was hard to shake the sense that I was falling behind.",
    },
    {
      createdAt: toIso(addHours(addDays(now, -2), -1)),
      preferredEmotion: "anger" as CanonicalEmotion,
      text: "A meeting left me frustrated because I felt like I had to carry everyone else's stress too.",
    },
    {
      createdAt: toIso(addHours(addDays(now, -1), -6)),
      preferredEmotion: "neutral" as CanonicalEmotion,
      sessionType: "morning",
      text: "Today was busy but manageable. I mostly noticed how much I needed a quiet hour to reset.",
    },
    {
      createdAt: toIso(addHours(now, -7)),
      preferredEmotion: "joy" as CanonicalEmotion,
      text: "I finally finished a piece of work I had been putting off and felt relieved after the conversation went better than expected.",
    },
  ].map((item) =>
    buildCheckinDetail({
      createdAt: item.createdAt,
      preferredEmotion: item.preferredEmotion,
      sessionType: item.sessionType,
      text: item.text,
      userId,
    })
  )
}

function createUserRecord(email: string, password: string, displayName?: string | null) {
  const normalizedEmail = normalizeEmail(email)
  const timestamp = new Date().toISOString()
  const user: AuthUser = {
    id: createId("user"),
    email: normalizedEmail,
    display_name: displayName?.trim() || buildDisplayName(normalizedEmail),
    is_active: true,
    created_at: timestamp,
    updated_at: timestamp,
  }
  const seedCheckins = createSeedCheckins(user.id)

  return {
    user,
    password,
    checkins: seedCheckins,
    conversationSessions: [],
    conversationTurns: {},
  } satisfies MockUserRecord
}

function ensureUserRecord(args: {
  displayName?: string | null
  email: string
  password?: string
}) {
  return withDatabase((database) => {
    const normalizedEmail = normalizeEmail(args.email)
    let record = database.users[normalizedEmail]

    if (!record) {
      record = createUserRecord(
        normalizedEmail,
        args.password ?? "demo-password",
        args.displayName
      )
      database.users[normalizedEmail] = record
      return record
    }

    if (args.password) {
      record.password = args.password
    }

    if (args.displayName?.trim()) {
      record.user.display_name = args.displayName.trim()
      record.user.updated_at = new Date().toISOString()
    }

    return record
  })
}

function getRecordByToken(token: string) {
  const email = getEmailFromToken(token)

  if (!email) {
    throw new Error("Your local demo session is no longer available.")
  }

  return ensureUserRecord({ email })
}

export const mockApi = {
  login(email: string, password: string): LoginResponse {
    if (!normalizeEmail(email) || !password.trim()) {
      throw new Error("Please enter both email and password.")
    }

    const record = ensureUserRecord({ email, password })

    return {
      access_token: createMockToken(record.user.email),
      token_type: "bearer",
      user: record.user,
    }
  },

  register(payload: RegisterRequest) {
    if (!normalizeEmail(payload.email) || !payload.password.trim()) {
      throw new Error("A valid email and password are required.")
    }

    ensureUserRecord({
      displayName: payload.display_name ?? null,
      email: payload.email,
      password: payload.password,
    })

    return { ok: true }
  },

  getAuthMe(token: string) {
    return getRecordByToken(token).user
  },

  getHome(token: string) {
    return buildHome(getRecordByToken(token))
  },

  createTextCheckin(
    token: string,
    payload: {
      session_type?: string
      text: string
    }
  ) {
    if (!payload.text.trim()) {
      throw new Error("Write something before saving a check-in.")
    }

    return withDatabase((database) => {
      const email = getEmailFromToken(token)

      if (!email) {
        throw new Error("Your local demo session is no longer available.")
      }

      const record = database.users[email] ?? createUserRecord(email, "demo-password")
      database.users[email] = record

      const createdAt = new Date().toISOString()
      const detail = buildCheckinDetail({
        createdAt,
        sessionType: payload.session_type ?? "free",
        text: payload.text.trim(),
        userId: record.user.id,
      })

      record.checkins = sortCheckinsDescending([detail, ...record.checkins])
      record.user.updated_at = createdAt

      return detail
    })
  },

  getCheckin(token: string, entryId: string) {
    const record = getRecordByToken(token)
    const match = record.checkins.find((item) => item.entry_id === entryId)

    if (!match) {
      throw new Error("That local fallback entry could not be found.")
    }

    return match
  },

  getHistory(token: string, userId: string, limit = 20, offset = 0): JournalHistoryResponse {
    const record = getRecordByToken(token)
    const items = sortCheckinsDescending(record.checkins)
      .filter((item) => item.user_id === userId)
      .map(buildHistoryItem)

    return {
      user_id: record.user.id,
      total: items.length,
      limit,
      offset,
      items: items.slice(offset, offset + limit),
    }
  },

  getUserSummary(token: string, _userId: string, days = 30) {
    return buildUserSummary(getRecordByToken(token), days)
  },

  getCalendar(token: string, days = 30) {
    return buildCalendar(getRecordByToken(token), days)
  },

  getLatestWeeklyWrapup(token: string) {
    return buildWrapup(getRecordByToken(token), "weekly")
  },

  getLatestMonthlyWrapup(token: string) {
    return buildWrapup(getRecordByToken(token), "monthly")
  },

  getRespondPreview(
    _token: string,
    payload: {
      session_type?: string | null
      transcript: string
    }
  ): RespondPreviewResponse {
    if (!payload.transcript.trim()) {
      throw new Error("Write something before asking for a reflection.")
    }

    const responsePackage = buildResponsePackage(payload.transcript.trim())

    return {
      emotion_analysis: responsePackage.emotion,
      topic_tags: responsePackage.topicTags,
      risk_level: responsePackage.riskLevel,
      risk_flags: responsePackage.riskFlags,
      response_plan: buildResponsePlan(responsePackage.emotion.primary_label),
      empathetic_response: responsePackage.ai.response?.empathetic_text ?? responsePackage.aiResponse,
      follow_up_question: responsePackage.followUpQuestion,
      gentle_suggestion: responsePackage.gentleSuggestion,
      quote: responsePackage.quote,
      ai_response: responsePackage.aiResponse,
      ai: responsePackage.ai,
    }
  },

  createConversationSession() {
    throw new Error(
      "Voice conversation stays backend-only for now. Text journal fallback is enabled."
    )
  },

  getConversationSessions(
    token: string,
    limit = 20,
    offset = 0
  ): ConversationSessionListResponse {
    const record = getRecordByToken(token)
    const items = [...record.conversationSessions].sort((left, right) =>
      right.started_at.localeCompare(left.started_at)
    )

    return {
      user_id: record.user.id,
      total: items.length,
      limit,
      offset,
      items: items.slice(offset, offset + limit),
    }
  },

  getConversationSession(token: string, sessionId: string) {
    const record = getRecordByToken(token)
    const session = record.conversationSessions.find((item) => item.id === sessionId)

    if (!session) {
      throw new Error("That fallback conversation could not be found.")
    }

    return session
  },

  getConversationSessionTurns(
    token: string,
    sessionId: string,
    limit = 50,
    offset = 0
  ): ConversationTurnListResponse {
    const record = getRecordByToken(token)
    const items = record.conversationTurns[sessionId] ?? []

    return {
      session_id: sessionId,
      total: items.length,
      limit,
      offset,
      items: items.slice(offset, offset + limit),
    }
  },

  endConversationSession(token: string, sessionId: string) {
    const record = getRecordByToken(token)
    const session = record.conversationSessions.find((item) => item.id === sessionId)

    if (!session) {
      return {
        id: sessionId,
        user_id: record.user.id,
        status: "completed",
        started_at: new Date().toISOString(),
        ended_at: new Date().toISOString(),
      }
    }

    return {
      ...session,
      status: "completed",
      ended_at: session.ended_at ?? new Date().toISOString(),
    }
  },
}
