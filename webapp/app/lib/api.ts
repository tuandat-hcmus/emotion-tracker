import type {
  AuthUser,
  CalendarResponse,
  CheckinDetail,
  ConversationSessionListResponse,
  ConversationSessionResponse,
  ConversationTurnListResponse,
  ConversationTurnResult,
  HomeResponse,
  JournalHistoryResponse,
  JournalMonthResponse,
  LoginResponse,
  MonthlyWrapupDetailResponse,
  RegisterRequest,
  RespondPreviewResponse,
  TranscribeAudioResponse,
  UserSummaryResponse,
  WrapupSnapshotResponse,
} from "~/lib/contracts"
import { isMockToken, mockApi } from "~/lib/mock-api"

const AUTH_STORAGE_KEY = "emotion-webapp-auth"
const AUTH_INVALIDATED_EVENT = "emotion-auth-invalidated"

type RequestOptions = {
  body?: BodyInit | null
  headers?: HeadersInit
  method?: string
  signal?: AbortSignal
  token?: string | null
}

type ApiErrorPayload = {
  detail?: string
  message?: string
}

let runtimeMockModeActive = false

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

export function getApiBaseUrl() {
  return (
    import.meta.env.VITE_API_BASE_URL?.trim() ||
    "http://127.0.0.1:8000"
  )
}

function isFallbackForced() {
  return import.meta.env.VITE_ENABLE_API_FALLBACK?.trim() === "true"
}

function setRuntimeMockModeActive(nextValue: boolean) {
  runtimeMockModeActive = nextValue
}

export function isMockApiModeActive(token?: string | null) {
  return isFallbackForced() || runtimeMockModeActive || isMockToken(token)
}

function canAutoFallbackToMock(token?: string | null) {
  if (isFallbackForced() || isMockToken(token)) {
    return true
  }

  return !token
}

export function getWebSocketBaseUrl() {
  const baseUrl = getApiBaseUrl()

  if (baseUrl.startsWith("https://")) {
    return `wss://${baseUrl.slice("https://".length)}`
  }

  if (baseUrl.startsWith("http://")) {
    return `ws://${baseUrl.slice("http://".length)}`
  }

  return baseUrl
}

async function requestJson<T>(path: string, options: RequestOptions = {}) {
  return requestJsonWithFallback<T>(path, options)
}

async function requestJsonWithFallback<T>(
  path: string,
  options: RequestOptions = {},
  fallback?: (() => Promise<T> | T) | null
) {
  const allowFallback = Boolean(fallback && canAutoFallbackToMock(options.token))
  const fallbackHandler = allowFallback ? fallback : null

  if (allowFallback && isMockApiModeActive(options.token)) {
    return await fallbackHandler!()
  }

  const headers = new Headers(options.headers)
  headers.set("Accept", "application/json")

  const isFormData =
    typeof FormData !== "undefined" && options.body instanceof FormData

  if (options.body && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`)
  }

  let response: Response

  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body,
      signal: options.signal,
    })
  } catch (error) {
    if (allowFallback) {
      setRuntimeMockModeActive(true)
      return await fallbackHandler!()
    }

    throw error
  }

  if (!response.ok) {
    let payload: ApiErrorPayload | null = null

    try {
      payload = (await response.json()) as ApiErrorPayload
    } catch {
      payload = null
    }

    if (response.status === 401 && options.token && typeof window !== "undefined") {
      window.localStorage.removeItem(AUTH_STORAGE_KEY)
      window.dispatchEvent(new Event(AUTH_INVALIDATED_EVENT))
    }

    throw new ApiError(
      payload?.detail || payload?.message || `Request failed with ${response.status}`,
      response.status
    )
  }

  if (!isFallbackForced() && !isMockToken(options.token)) {
    setRuntimeMockModeActive(false)
  }

  return (await response.json()) as T
}

export { AUTH_INVALIDATED_EVENT, AUTH_STORAGE_KEY }

export const api = {
  login(email: string, password: string) {
    return requestJsonWithFallback<LoginResponse>(
      "/v1/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      },
      () => {
        setRuntimeMockModeActive(true)
        return mockApi.login(email, password)
      }
    )
  },
  register(payload: RegisterRequest) {
    return requestJsonWithFallback(
      "/v1/auth/register",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      () => {
        setRuntimeMockModeActive(true)
        return mockApi.register(payload)
      }
    )
  },
  getAuthMe(token: string) {
    return requestJsonWithFallback<AuthUser>("/v1/auth/me", { token }, () =>
      mockApi.getAuthMe(token)
    )
  },
  getHome(token: string) {
    return requestJsonWithFallback<HomeResponse>("/v1/me/home", { token }, () =>
      mockApi.getHome(token)
    )
  },
  createTextCheckin(
    token: string,
    payload: {
      text: string
      session_type?: string
    }
  ) {
    return requestJsonWithFallback<CheckinDetail>(
      "/v1/checkins/text",
      {
        method: "POST",
        token,
        body: JSON.stringify(payload),
      },
      () => mockApi.createTextCheckin(token, payload)
    )
  },
  transcribeCheckinAudio(token: string, file: File, signal?: AbortSignal) {
    const formData = new FormData()
    formData.append("file", file)

    return requestJson<TranscribeAudioResponse>("/v1/checkins/transcribe", {
      method: "POST",
      signal,
      token,
      body: formData,
    })
  },
  getCheckin(token: string, entryId: string) {
    return requestJsonWithFallback<CheckinDetail>(
      `/v1/checkins/${entryId}`,
      { token },
      () => mockApi.getCheckin(token, entryId)
    )
  },
  getHistory(token: string, userId: string, limit = 20, offset = 0) {
    return requestJsonWithFallback<JournalHistoryResponse>(
      `/v1/users/${userId}/entries?limit=${limit}&offset=${offset}`,
      { token },
      () => mockApi.getHistory(token, userId, limit, offset)
    )
  },
  getUserSummary(token: string, userId: string, days = 30) {
    return requestJsonWithFallback<UserSummaryResponse>(
      `/v1/users/${userId}/summary?days=${days}`,
      { token },
      () => mockApi.getUserSummary(token, userId, days)
    )
  },
  getCalendar(token: string, days = 30) {
    return requestJsonWithFallback<CalendarResponse>(
      `/v1/me/calendar?days=${days}`,
      { token },
      () => mockApi.getCalendar(token, days)
    )
  },
  getLatestWeeklyWrapup(token: string) {
    return requestJsonWithFallback<WrapupSnapshotResponse>(
      "/v1/me/wrapups/weekly/latest",
      {
        token,
      },
      () => mockApi.getLatestWeeklyWrapup(token)
    )
  },
  getLatestMonthlyWrapup(token: string) {
    return requestJsonWithFallback<WrapupSnapshotResponse>(
      "/v1/me/wrapups/monthly/latest",
      {
        token,
      },
      () => mockApi.getLatestMonthlyWrapup(token)
    )
  },
  getJournalMonth(token: string, year: number, month: number) {
    return requestJsonWithFallback<JournalMonthResponse>(
      `/v1/me/journal/month?year=${year}&month=${month}`,
      { token },
      async () => {
        const [calendar, history, monthlyWrapup] = await Promise.all([
          mockApi.getCalendar(token, 31),
          mockApi.getHistory(token, "mock-user", 120, 0),
          mockApi.getLatestMonthlyWrapup(token),
        ])
        return {
          period: {
            year,
            month,
            label: new Date(year, month - 1, 1).toLocaleDateString([], {
              month: "long",
              year: "numeric",
            }),
            date_from: new Date(year, month - 1, 1).toISOString().slice(0, 10),
            date_to: new Date(year, month, 0).toISOString().slice(0, 10),
          },
          calendar_items: calendar.items.filter((item) => item.date.startsWith(`${year}-${String(month).padStart(2, "0")}`)),
          entries: history.items
            .map((item) => ({
              ...item,
              local_date: item.created_at.slice(0, 10),
            }))
            .filter((item) => item.local_date.startsWith(`${year}-${String(month).padStart(2, "0")}`)),
          monthly_wrapup: monthlyWrapup.period_start.startsWith(`${year}-${String(month).padStart(2, "0")}`)
            ? monthlyWrapup
            : null,
        }
      }
    )
  },
  getLatestMonthlyWrapupDetail(token: string) {
    return requestJson<MonthlyWrapupDetailResponse>(
      "/v1/me/wrapups/monthly/latest/detail",
      {
        token,
      }
    )
  },
  getMonthlyWrapupDetail(token: string, year: number, month: number) {
    return requestJson<MonthlyWrapupDetailResponse>(
      `/v1/me/wrapups/monthly/${year}/${month}`,
      {
        token,
      }
    )
  },
  getRespondPreview(
    token: string,
    payload: {
      transcript: string
      session_type?: string | null
    }
  ) {
    return requestJsonWithFallback<RespondPreviewResponse>(
      "/v1/me/respond-preview",
      {
        method: "POST",
        token,
        body: JSON.stringify(payload),
      },
      () => mockApi.getRespondPreview(token, payload)
    )
  },
  createConversationSession(token: string) {
    return requestJsonWithFallback<ConversationSessionResponse>(
      "/v1/conversations/sessions",
      {
        method: "POST",
        token,
      },
      () => mockApi.createConversationSession()
    )
  },
  getConversationSessions(token: string, limit = 20, offset = 0) {
    return requestJsonWithFallback<ConversationSessionListResponse>(
      `/v1/conversations/sessions?limit=${limit}&offset=${offset}`,
      { token },
      () => mockApi.getConversationSessions(token, limit, offset)
    )
  },
  getConversationSession(token: string, sessionId: string) {
    return requestJsonWithFallback<ConversationSessionResponse>(
      `/v1/conversations/sessions/${sessionId}`,
      { token },
      () => mockApi.getConversationSession(token, sessionId)
    )
  },
  getConversationSessionTurns(
    token: string,
    sessionId: string,
    limit = 50,
    offset = 0
  ) {
    return requestJsonWithFallback<ConversationTurnListResponse>(
      `/v1/conversations/sessions/${sessionId}/turns?limit=${limit}&offset=${offset}`,
      { token },
      () => mockApi.getConversationSessionTurns(token, sessionId, limit, offset)
    )
  },
  endConversationSession(token: string, sessionId: string) {
    return requestJsonWithFallback<ConversationSessionResponse>(
      `/v1/conversations/sessions/${sessionId}/end`,
      {
        method: "POST",
        token,
      },
      () => mockApi.endConversationSession(token, sessionId)
    )
  },
}

export type ConversationSocketEvent =
  | {
      type: "partial_transcript"
      text: string
    }
  | {
      type: "final_transcript"
      text: string
      confidence: number | null
      audio_path: string | null
    }
  | {
      type: "assistant_response"
      payload: ConversationTurnResult
    }
  | {
      type: "error"
      message: string
    }
