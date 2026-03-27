export type CanonicalEmotion =
  | "anger"
  | "disgust"
  | "fear"
  | "joy"
  | "neutral"
  | "sadness"
  | "surprise"

export type AuthUser = {
  id: string
  email: string
  display_name: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export type LoginResponse = {
  access_token: string
  token_type: string
  user: AuthUser
}

export type RegisterRequest = {
  email: string
  password: string
  display_name?: string | null
}

export type EmotionAnalysis = {
  primary_label: string | null
  secondary_labels: string[]
  all_labels: string[]
  scores: Record<string, number>
  threshold: number | null
  confidence: number | null
  provider_name: string | null
  source: string | null
  language: string | null
  valence_score: number | null
  energy_score: number | null
  stress_score: number | null
  social_need_score: number | null
  response_mode: string | null
  dominant_signals: string[]
  context_tags: string[]
  enrichment_notes: string[]
}

export type ResponsePlan = {
  opening_style: string
  acknowledgment_focus: string
  suggestion_allowed: boolean
  suggestion_style: string
  suggestion_family: string | null
  quote_allowed: boolean
  avoid_advice: boolean
  tone: string
  max_sentences: number
  follow_up_question_allowed: boolean
  response_variant: string | null
  response_mode: string | null
  evidence_bound: boolean
}

export type ResponseQuote = {
  short_text: string
  tone: string
  source_type: string
}

export type AIContract = {
  emotion?: EmotionAnalysis
  state?: {
    primary_label?: string | null
    secondary_labels?: string[]
    stress_score?: number | null
    response_mode?: string | null
    risk_level?: string | null
  }
  risk?: {
    level?: string | null
    flags?: string[]
  }
  topics?: {
    tags?: string[]
  }
  response?: {
    empathetic_text?: string | null
    follow_up_question?: string | null
    suggestion_text?: string | null
    composed_text?: string | null
    quote?: ResponseQuote | null
  }
  memory?: {
    recurring_triggers?: string[]
    dominant_positive_patterns?: string[]
  }
}

export type CheckinDetail = {
  entry_id: string
  status: string
  user_id: string
  session_type: string
  source_type: string
  audio_path: string | null
  transcript_text: string | null
  transcript_confidence: number | null
  transcript_source: string | null
  transcript_provider: string | null
  ai_analysis_complete: boolean
  latest_attempt_status: string | null
  processing_started_at: string | null
  processing_finished_at: string | null
  ai_response: string | null
  primary_label: string | null
  secondary_labels: string[]
  all_labels: string[]
  scores: Record<string, number>
  threshold: number | null
  valence_score: number | null
  energy_score: number | null
  stress_score: number | null
  social_need_score: number | null
  confidence: number | null
  dominant_signals: string[]
  context_tags: string[]
  enrichment_notes: string[]
  response_mode: string | null
  language: string | null
  source: string | null
  provider_name: string | null
  empathetic_response: string | null
  follow_up_question: string | null
  gentle_suggestion: string | null
  quote_text: string | null
  response_metadata: Record<string, unknown> | null
  topic_tags: string[]
  risk_level: string | null
  risk_flags: string[]
  ai: AIContract
  created_at: string
}

export type TranscribeAudioResponse = {
  transcript: string
  confidence: number | null
  provider: string
}

export type RespondPreviewResponse = {
  emotion_analysis: EmotionAnalysis
  topic_tags: string[]
  risk_level: string
  risk_flags: string[]
  response_plan: ResponsePlan
  empathetic_response: string
  follow_up_question: string | null
  gentle_suggestion: string | null
  quote: ResponseQuote | null
  ai_response: string
  ai: AIContract
}

export type JournalHistoryItem = {
  id: string
  entry_id: string
  status: string
  session_type: string
  source_type: string
  local_date: string
  transcript_excerpt: string | null
  ai_response_excerpt: string | null
  primary_label: string | null
  secondary_labels: string[]
  stress_score: number | null
  created_at: string
  updated_at: string
}

export type JournalHistoryResponse = {
  user_id: string
  total: number
  limit: number
  offset: number
  items: JournalHistoryItem[]
}

export type JournalMonthResponse = {
  period: {
    year: number
    month: number
    label: string
    date_from: string
    date_to: string
  }
  calendar_items: CalendarDayItem[]
  entries: JournalHistoryItem[]
  monthly_wrapup: WrapupSnapshotResponse | null
}

export type UserSummaryResponse = {
  user_id: string
  days: number
  total_entries: number
  emotion_counts: Record<string, number>
  average_valence_score: number | null
  average_energy_score: number | null
  average_stress_score: number | null
  top_topics: string[]
  risk_counts: Record<string, number>
  latest_entry_at: string | null
  dominant_emotional_patterns: string[]
  recurring_triggers: string[]
  workload_deadline_patterns: string[]
  positive_anchors: string[]
  emotional_direction_trend: string
  high_stress_frequency: number
  summary_text: string | null
}

export type HomeResponse = {
  user: {
    id: string
    email: string
    display_name: string | null
  }
  preferences_summary: {
    quote_opt_in: boolean
    reminder_enabled: boolean
    reminder_time: string | null
    preferred_tree_type: string
    checkin_goal_per_day: number
  }
  today: {
    date: string
    has_morning_checkin: boolean
    has_evening_checkin: boolean
    total_entries: number
    session_types_present: string[]
    latest_entry_id: string | null
    latest_emotion_label: string | null
    latest_risk_level: string | null
    total_entries_today: number
  }
  tree: {
    vitality_score: number
    streak_days: number
    current_stage: string | null
    leaf_state: string | null
    weather_state: string | null
    last_checkin_date: string | null
  }
  recent_trend: {
    last_7_days_average_valence: number | null
    last_7_days_average_stress: number | null
    entries_last_7_days: number
  }
  quote: ResponseQuote | null
  latest_wrapup_meta: {
    latest_weekly_wrapup_at: string | null
    latest_monthly_wrapup_at: string | null
  }
}

export type CalendarDayItem = {
  date: string
  entry_count: number
  has_morning_checkin: boolean
  has_evening_checkin: boolean
  primary_emotion_label: string | null
  average_valence_score: number | null
  average_stress_score: number | null
  max_risk_level: string | null
  topic_tags_top: string[]
  mood_color_token: string
}

export type CalendarResponse = {
  user_id: string
  days: number
  items: CalendarDayItem[]
}

export type WrapupInsightCard = {
  kind: string
  title: string
  summary: string
  emphasis: string | null
  items: string[]
}

export type WrapupSnapshotResponse = {
  id: string
  user_id: string
  period_type: string
  period_start: string
  period_end: string
  generated_at: string
  created_at: string
  updated_at: string
  payload: {
    period_type: string
    period_start: string
    period_end: string
    total_entries: number
    total_checkin_days: number
    emotion_counts: Record<string, number>
    average_valence_score: number | null
    average_stress_score: number | null
    top_topics: string[]
    strongest_positive_day: {
      date: string
      average_valence_score: number | null
      average_stress_score: number | null
      dominant_emotion_label: string | null
      risk_level: string | null
    } | null
    heaviest_day: {
      date: string
      average_valence_score: number | null
      average_stress_score: number | null
      dominant_emotion_label: string | null
      risk_level: string | null
    } | null
    streak_highlight: {
      longest_streak_days: number
      current_streak_days: number
    }
    checkin_consistency: {
      completed_days: number
      total_days: number
      ratio: number
    }
    notable_shift: string
    dominant_emotional_patterns: string[]
    recurring_triggers: string[]
    workload_deadline_patterns: string[]
    positive_anchors: string[]
    emotional_direction_trend: string
    high_stress_frequency: number
    summary_text: string | null
    insight_cards: WrapupInsightCard[]
    trend_block: {
      emotional_direction_trend: string
      high_stress_frequency: number
      high_stress_entry_count: number
      workload_pattern_detected: boolean
      positive_anchor_count: number
      recurring_trigger_count: number
    } | null
    closing_message: string
  }
}

export type MonthlyWrapupHeadlineCard = {
  id: string
  title: string
  subtitle: string | null
  value: string | number | null
  supporting_text: string | null
  icon_key: string
  color_token: string
  priority: number
  source_type: string
}

export type MonthlyWrapupPatternItem = {
  label: string
  count: number
  weight: number | null
  icon_key: string
  color_token: string
}

export type MonthlyWrapupWeeklyMetric = {
  week_label: string
  date_from: string
  date_to: string
  avg_stress_score: number | null
  count: number
}

export type MonthlyWrapupDetailResponse = {
  period: {
    year: number
    month: number
    label: string
    date_from: string
    date_to: string
  }
  overview: {
    summary_text: string | null
    dominant_emotion: string | null
    emotional_direction_trend: string
    overall_checkin_count: number
    high_stress_frequency: number
  }
  headline_cards: MonthlyWrapupHeadlineCard[]
  stats: {
    total_checkins: number
    active_days: number
    avg_stress_score: number | null
    top_emotion: string | null
    top_trigger: string | null
    top_positive_anchor: string | null
    longest_gap_days: number | null
    best_streak_days: number | null
  }
  distributions: {
    emotion_distribution: Array<{
      label: string
      count: number
      percent: number
    }>
    weekly_stress_trend: MonthlyWrapupWeeklyMetric[]
    weekly_checkin_counts: MonthlyWrapupWeeklyMetric[]
  }
  pattern_lists: {
    recurring_triggers: MonthlyWrapupPatternItem[]
    positive_anchors: MonthlyWrapupPatternItem[]
    workload_deadline_patterns: MonthlyWrapupPatternItem[]
    dominant_emotional_patterns: MonthlyWrapupPatternItem[]
  }
  visual_hints: {
    month_mood_color: string
    month_theme_icon: string
    intensity_level: string
  }
}

export type ConversationSessionResponse = {
  id: string
  user_id: string
  status: string
  started_at: string
  ended_at: string | null
}

export type ConversationSessionListResponse = {
  user_id: string
  total: number
  limit: number
  offset: number
  items: ConversationSessionResponse[]
}

export type ConversationTurnResponse = {
  id: string
  session_id: string
  role: string
  text: string
  audio_path: string | null
  emotion_snapshot: Record<string, unknown> | null
  state_snapshot: Record<string, unknown> | null
  created_at: string
}

export type ConversationTurnListResponse = {
  session_id: string
  total: number
  limit: number
  offset: number
  items: ConversationTurnResponse[]
}

export type ConversationTurnResult = {
  session_id: string
  user_turn: {
    id: string
    session_id: string
    role: string
    text: string
    created_at: string
  }
  assistant_turn: {
    id: string
    session_id: string
    role: string
    text: string
    created_at: string
  }
  final_transcript: string
  assistant_response: string
  emotion_analysis: EmotionAnalysis
  response_plan: ResponsePlan
  ai: AIContract
}
