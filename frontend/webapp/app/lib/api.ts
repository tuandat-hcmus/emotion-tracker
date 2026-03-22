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
  LoginResponse,
  RegisterRequest,
  RespondPreviewResponse,
  UserSummaryResponse,
  WrapupSnapshotResponse,
} from "~/lib/contracts"

const AUTH_STORAGE_KEY = "emotion-webapp-auth"
const AUTH_INVALIDATED_EVENT = "emotion-auth-invalidated"

type RequestOptions = {
  body?: BodyInit | null
  headers?: HeadersInit
  method?: string
  token?: string | null
}

type ApiErrorPayload = {
  detail?: string
  message?: string
}

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
  const headers = new Headers(options.headers)
  headers.set("Accept", "application/json")

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`)
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body,
  })

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

  return (await response.json()) as T
}

export { AUTH_INVALIDATED_EVENT, AUTH_STORAGE_KEY }

export const api = {
  login(email: string, password: string) {
    return requestJson<LoginResponse>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
  },
  register(payload: RegisterRequest) {
    return requestJson("/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  getAuthMe(token: string) {
    return requestJson<AuthUser>("/v1/auth/me", { token })
  },
  getHome(token: string) {
    return requestJson<HomeResponse>("/v1/me/home", { token })
  },
  createTextCheckin(
    token: string,
    payload: {
      text: string
      session_type?: string
    }
  ) {
    return requestJson<CheckinDetail>("/v1/checkins/text", {
      method: "POST",
      token,
      body: JSON.stringify(payload),
    })
  },
  getHistory(token: string, userId: string, limit = 20, offset = 0) {
    return requestJson<JournalHistoryResponse>(
      `/v1/users/${userId}/entries?limit=${limit}&offset=${offset}`,
      { token }
    )
  },
  getUserSummary(token: string, userId: string, days = 30) {
    return requestJson<UserSummaryResponse>(
      `/v1/users/${userId}/summary?days=${days}`,
      { token }
    )
  },
  getCalendar(token: string, days = 30) {
    return requestJson<CalendarResponse>(`/v1/me/calendar?days=${days}`, { token })
  },
  getLatestWeeklyWrapup(token: string) {
    return requestJson<WrapupSnapshotResponse>("/v1/me/wrapups/weekly/latest", {
      token,
    })
  },
  getLatestMonthlyWrapup(token: string) {
    return requestJson<WrapupSnapshotResponse>("/v1/me/wrapups/monthly/latest", {
      token,
    })
  },
  getRespondPreview(
    token: string,
    payload: {
      transcript: string
      session_type?: string | null
    }
  ) {
    return requestJson<RespondPreviewResponse>("/v1/me/respond-preview", {
      method: "POST",
      token,
      body: JSON.stringify(payload),
    })
  },
  createConversationSession(token: string) {
    return requestJson<ConversationSessionResponse>("/v1/conversations/sessions", {
      method: "POST",
      token,
    })
  },
  getConversationSessions(token: string, limit = 20, offset = 0) {
    return requestJson<ConversationSessionListResponse>(
      `/v1/conversations/sessions?limit=${limit}&offset=${offset}`,
      { token }
    )
  },
  getConversationSession(token: string, sessionId: string) {
    return requestJson<ConversationSessionResponse>(
      `/v1/conversations/sessions/${sessionId}`,
      { token }
    )
  },
  getConversationSessionTurns(
    token: string,
    sessionId: string,
    limit = 50,
    offset = 0
  ) {
    return requestJson<ConversationTurnListResponse>(
      `/v1/conversations/sessions/${sessionId}/turns?limit=${limit}&offset=${offset}`,
      { token }
    )
  },
  endConversationSession(token: string, sessionId: string) {
    return requestJson<ConversationSessionResponse>(
      `/v1/conversations/sessions/${sessionId}/end`,
      {
        method: "POST",
        token,
      }
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
