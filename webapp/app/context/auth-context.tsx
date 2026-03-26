import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import { AUTH_INVALIDATED_EVENT, AUTH_STORAGE_KEY, api } from "~/lib/api"
import type { AuthUser } from "~/lib/contracts"

type StoredAuth = {
  token: string
  user: AuthUser
}

type AuthContextValue = {
  isAuthenticated: boolean
  isReady: boolean
  token: string | null
  user: AuthUser | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  register: (payload: {
    display_name?: string | null
    email: string
    password: string
  }) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function readStoredAuth(): StoredAuth | null {
  if (typeof window === "undefined") {
    return null
  }

  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)

  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as StoredAuth
  } catch {
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
    return null
  }
}

function writeStoredAuth(payload: StoredAuth | null) {
  if (typeof window === "undefined") {
    return
  }

  if (!payload) {
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
    return
  }

  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(payload))
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isReady, setIsReady] = useState(false)
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<AuthUser | null>(null)

  function clearAuthState() {
    setToken(null)
    setUser(null)
    writeStoredAuth(null)
  }

  useEffect(() => {
    let cancelled = false

    async function hydrateAuth() {
      const stored = readStoredAuth()

      if (!stored) {
        if (!cancelled) {
          setIsReady(true)
        }
        return
      }

      try {
        const verifiedUser = await api.getAuthMe(stored.token)

        if (cancelled) {
          return
        }

        const nextState = {
          token: stored.token,
          user: verifiedUser,
        }

        setToken(nextState.token)
        setUser(nextState.user)
        writeStoredAuth(nextState)
      } catch {
        if (cancelled) {
          return
        }

        setToken(null)
        setUser(null)
        writeStoredAuth(null)
      } finally {
        if (!cancelled) {
          setIsReady(true)
        }
      }
    }

    void hydrateAuth()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (typeof window === "undefined") {
      return
    }

    function handleStorage(event: StorageEvent) {
      if (event.key !== null && event.key !== AUTH_STORAGE_KEY) {
        return
      }

      const nextState = readStoredAuth()
      setToken(nextState?.token ?? null)
      setUser(nextState?.user ?? null)
    }

    function handleAuthInvalidated() {
      clearAuthState()
    }

    window.addEventListener("storage", handleStorage)
    window.addEventListener(AUTH_INVALIDATED_EVENT, handleAuthInvalidated)

    return () => {
      window.removeEventListener("storage", handleStorage)
      window.removeEventListener(AUTH_INVALIDATED_EVENT, handleAuthInvalidated)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: Boolean(token && user),
      isReady,
      token,
      user,
      async login(email, password) {
        const response = await api.login(email, password)
        const nextState = {
          token: response.access_token,
          user: response.user,
        }

        setToken(nextState.token)
        setUser(nextState.user)
        writeStoredAuth(nextState)
      },
      logout() {
        clearAuthState()
      },
      async register(payload) {
        await api.register(payload)
        const response = await api.login(payload.email, payload.password)
        const nextState = {
          token: response.access_token,
          user: response.user,
        }

        setToken(nextState.token)
        setUser(nextState.user)
        writeStoredAuth(nextState)
      },
    }),
    [isReady, token, user]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider")
  }

  return context
}
