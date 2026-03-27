import { AnimatePresence, motion } from "framer-motion"
import { Cancel01Icon, NoteIcon, SparklesIcon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router"

import { useAuth } from "~/context/auth-context"
import { useSoulForest } from "~/context/soul-forest-context"
import { isMockApiModeActive } from "~/lib/api"
import type { HomeResponse } from "~/lib/contracts"

type ReminderSessionType = "morning" | "evening"

type ReminderDescriptor = {
  ctaLabel: string
  message: string
  sessionType: ReminderSessionType
}

const DISMISSED_REMINDER_STORAGE_KEY = "emotion-checkin-reminder-dismissed"

function buildDismissKey(date: string, sessionType: ReminderSessionType) {
  return `${DISMISSED_REMINDER_STORAGE_KEY}:${date}:${sessionType}`
}

function buildReminder(
  home: HomeResponse | null,
  options?: {
    isMockMode?: boolean
  }
): ReminderDescriptor | null {
  if (!home?.preferences_summary.reminder_enabled) {
    return null
  }

  const currentHour = new Date().getHours()
  const isMockMode = options?.isMockMode ?? false

  if (currentHour < 11 && !isMockMode) {
    return null
  }

  if (currentHour >= 17) {
    if (home.today.has_evening_checkin) {
      return null
    }

    if (home.today.total_entries_today > 0) {
      return {
        sessionType: "evening",
        message: "Add a quick evening check-in.",
        ctaLabel: "Write now",
      }
    }

    return {
      sessionType: "evening",
      message: "Log today's feelings before the day ends.",
      ctaLabel: "Write now",
    }
  }

  if (home.today.has_morning_checkin) {
    return null
  }

  return {
    sessionType: "morning",
    message: "You have not logged your morning check-in yet.",
    ctaLabel: "Log now",
  }
}

export function CheckinReminderBanner() {
  const { token } = useAuth()
  const { home, homeStatus } = useSoulForest()
  const reminder = useMemo(
    () =>
      buildReminder(home, {
        isMockMode: isMockApiModeActive(token),
      }),
    [home, token]
  )
  const dismissKey = reminder ? buildDismissKey(home?.today.date ?? "", reminder.sessionType) : null
  const [isDismissed, setIsDismissed] = useState(false)

  useEffect(() => {
    if (!dismissKey || typeof window === "undefined") {
      setIsDismissed(false)
      return
    }

    setIsDismissed(window.localStorage.getItem(dismissKey) === "1")
  }, [dismissKey])

  const isVisible = homeStatus === "ready" && Boolean(reminder) && !isDismissed
  const accentColor = reminder?.sessionType === "morning" ? "#F59E0B" : "#12A96E"
  const panelBackground =
    reminder?.sessionType === "morning"
      ? "linear-gradient(135deg, rgba(255,247,219,0.96), rgba(255,255,255,0.95))"
      : "linear-gradient(135deg, rgba(233,255,244,0.98), rgba(255,255,255,0.94))"

  function handleDismiss() {
    if (!dismissKey || typeof window === "undefined") {
      setIsDismissed(true)
      return
    }

    window.localStorage.setItem(dismissKey, "1")
    setIsDismissed(true)
  }

  return (
    <AnimatePresence>
      {isVisible && reminder ? (
        <motion.div
          initial={{ opacity: 0, y: -24, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -18, scale: 0.98 }}
          transition={{ duration: 0.28, ease: "easeOut" }}
          className="pointer-events-none fixed inset-x-3 top-[calc(0.85rem+env(safe-area-inset-top))] z-40 md:inset-x-auto md:top-auto md:bottom-6 md:right-6 md:w-[min(29rem,calc(100vw-4rem))]"
        >
          <div
            className="pointer-events-auto overflow-hidden rounded-[1.75rem] border border-white/70 shadow-[0_22px_60px_rgba(22,68,61,0.16)] backdrop-blur-xl"
            style={{ background: panelBackground }}
          >
            <div className="flex items-start gap-3 p-4 md:p-5">
              <span
                className="mt-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl"
                style={{
                  backgroundColor: `${accentColor}1f`,
                  color: accentColor,
                }}
              >
                <HugeiconsIcon
                  icon={reminder.sessionType === "morning" ? SparklesIcon : NoteIcon}
                  size={20}
                  strokeWidth={1.8}
                />
              </span>

              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-3">
                  <p className="min-w-0 pr-2 text-sm font-medium leading-6 text-[#163D33] md:text-[0.95rem]">
                    {reminder.message}
                  </p>

                  <button
                    type="button"
                    onClick={handleDismiss}
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/70 text-[#49665D] transition-colors hover:bg-white"
                    aria-label="Dismiss reminder"
                  >
                    <HugeiconsIcon icon={Cancel01Icon} size={18} strokeWidth={1.8} />
                  </button>
                </div>

                <div className="mt-3 flex justify-start">
                  <Link
                    to={`/app/journal?session=${reminder.sessionType}`}
                    className="inline-flex items-center justify-center rounded-full bg-[var(--brand-primary)] px-4 py-2 text-sm font-medium text-[var(--brand-on-primary)] transition-colors hover:bg-[var(--brand-primary-strong)]"
                  >
                    {reminder.ctaLabel}
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}
