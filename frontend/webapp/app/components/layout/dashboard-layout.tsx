import { motion } from "framer-motion"
import {
  BookOpen02Icon,
  Home01Icon,
  Mic01Icon,
} from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { Suspense, lazy, useState } from "react"
import { Navigate, NavLink, Outlet, useLocation } from "react-router"

import { DeferredSoulTree } from "~/components/home/deferred-soul-tree"
import { useAuth } from "~/context/auth-context"
import { useSoulForest } from "~/context/soul-forest-context"
import { formatEmotionLabel, getEmotionColor } from "~/lib/emotions"
import { cn } from "~/lib/utils"

const loadInteractiveVoiceModal = () =>
  import("~/components/home/interactive-voice-modal").then((module) => ({
    default: module.InteractiveVoiceModal,
  }))

const LazyInteractiveVoiceModal = lazy(loadInteractiveVoiceModal)

const navigation = [
  {
    label: "Home",
    to: "/app/home",
    icon: Home01Icon,
  },
  {
    label: "Journal",
    to: "/app/journal",
    icon: BookOpen02Icon,
  },
] as const

function NavigationLink({
  compact = false,
  icon: Icon,
  label,
  minimal = false,
  to,
}: {
  compact?: boolean
  icon: typeof Home01Icon
  label: string
  minimal?: boolean
  to: string
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          "group flex items-center rounded-full border border-white/45 bg-white/45 text-[#2F3E36]/78 shadow-sm backdrop-blur-md transition-all hover:bg-white/60 hover:text-[#2F3E36]",
          minimal
            ? "mx-auto h-10 w-10 justify-center px-0"
            : compact
              ? "justify-center px-0 py-4"
              : "gap-3 px-4 py-3",
          isActive &&
            "border-transparent bg-[#7E9F8B] text-white shadow-[0_10px_35px_rgba(126,159,139,0.24)]"
        )
      }
    >
      <HugeiconsIcon
        icon={Icon}
        size={minimal ? 18 : compact ? 20 : 16}
        strokeWidth={1.8}
        className="shrink-0"
      />
      {!compact && !minimal ? (
        <span className="text-sm font-medium">{label}</span>
      ) : null}
      <span className="sr-only">{label}</span>
    </NavLink>
  )
}

export function DashboardLayout() {
  const { isAuthenticated, isReady } = useAuth()
  const { currentMood, treeScore } = useSoulForest()
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false)
  const location = useLocation()
  const isJournalRoute = location.pathname.startsWith("/app/journal")

  function prepareVoiceModal() {
    void loadInteractiveVoiceModal()
  }

  if (!isReady) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-[#FDFBF7] text-sm text-[#2F3E36]/72">
        Preparing your journal...
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="relative min-h-svh overflow-hidden bg-[#FDFBF7] text-[#2F3E36]">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute inset-0 bg-[#FDFBF7]" />
        <div className="absolute inset-x-0 top-0 h-72 bg-[radial-gradient(circle_at_top,rgba(168,195,216,0.32),rgba(253,251,247,0.08),transparent_72%)]" />
        <div className="absolute -left-20 top-8 h-64 w-64 rounded-full bg-[#A8C3D8]/22 blur-3xl" />
        <div className="absolute bottom-12 right-[-4rem] h-72 w-72 rounded-full bg-[#7E9F8B]/18 blur-3xl" />
      </div>

      {!isJournalRoute ? (
        <div className="pointer-events-none fixed inset-y-8 left-[7.5rem] z-0 hidden w-[min(22rem,28vw)] items-center lg:flex">
          <motion.div
            initial={{ opacity: 0.24, scale: 0.96 }}
            animate={{ opacity: 0.72, scale: 1 }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="h-[30rem] w-full rounded-[2.25rem] border border-white/28 bg-white/10 p-4 backdrop-blur-[2px]"
          >
            <DeferredSoulTree
              emotion={currentMood}
              score={treeScore}
              deferMs={220}
              className="h-full rounded-[1.8rem] border-0 bg-transparent shadow-none"
            />
          </motion.div>
        </div>
      ) : null}

      <div className="relative z-10 min-h-svh">
        {!isJournalRoute ? (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="pointer-events-none fixed right-6 top-6 z-20 hidden lg:block"
          >
            <div className="inline-flex items-center gap-2 rounded-full border border-white/45 bg-white/48 px-4 py-2 text-sm font-medium text-[#2F3E36] shadow-sm backdrop-blur-xl">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: getEmotionColor(currentMood) }}
              />
              {formatEmotionLabel(currentMood)}
            </div>
          </motion.div>
        ) : null}

        <aside className="fixed left-6 top-1/2 z-30 hidden w-20 -translate-y-1/2 rounded-[2rem] border border-white/40 bg-white/44 p-3 shadow-[0_18px_70px_rgba(47,62,54,0.1)] backdrop-blur-xl md:flex md:flex-col md:items-center md:justify-between md:gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#7E9F8B] text-sm font-semibold text-white shadow-[0_12px_25px_rgba(126,159,139,0.28)]">
            EF
          </div>

          <div className="flex w-full flex-col gap-3">
            {navigation.map((item) => (
              <NavigationLink
                key={item.to}
                compact
                icon={item.icon}
                label={item.label}
                to={item.to}
              />
            ))}
          </div>

          <button
            type="button"
            onFocus={prepareVoiceModal}
            onMouseEnter={prepareVoiceModal}
            onClick={() => setIsVoiceModalOpen(true)}
            className="flex h-12 w-12 items-center justify-center rounded-full border border-white/60 bg-white/58 text-[#2F3E36] transition-colors hover:bg-white"
            aria-label="Open voice conversation"
          >
            <HugeiconsIcon icon={Mic01Icon} size={18} strokeWidth={1.8} />
          </button>
        </aside>

        <main className="relative min-h-svh pb-24 md:pb-10">
          <div className="mx-auto w-full max-w-md px-4 pt-4 md:max-w-5xl md:px-8 md:pb-8 md:pt-8 lg:max-w-7xl lg:pl-[7.5rem]">
            <div
              className={
                isJournalRoute
                  ? "lg:max-w-[min(76rem,calc(100vw-9rem))]"
                  : "lg:ml-[min(20rem,25vw)] lg:max-w-[min(54rem,calc(100vw-13rem))]"
              }
            >
              <div className="min-h-[calc(100svh-2rem)] rounded-[2rem] border border-white/42 bg-white/42 shadow-[0_18px_70px_rgba(47,62,54,0.08)] backdrop-blur-xl md:min-h-[calc(100svh-4rem)]">
                <div className="min-h-[calc(100svh-2rem)] md:max-h-[calc(100svh-4rem)] md:overflow-y-auto md:overscroll-contain">
                  <Outlet />
                </div>
              </div>
            </div>
          </div>
        </main>

        <nav className="fixed inset-x-0 bottom-3 z-30 px-4 md:hidden">
          <div className="mx-auto max-w-md">
            <div className="relative rounded-[1.6rem] border border-white/40 bg-white/50 px-3 pb-[calc(0.65rem+env(safe-area-inset-bottom))] pt-3 shadow-[0_14px_42px_rgba(47,62,54,0.1)] backdrop-blur-xl">
              <button
                type="button"
                onFocus={prepareVoiceModal}
                onMouseEnter={prepareVoiceModal}
                onClick={() => setIsVoiceModalOpen(true)}
                className="absolute left-1/2 top-0 flex h-[3.7rem] w-[3.7rem] -translate-x-1/2 -translate-y-[46%] items-center justify-center rounded-full border border-white/60 bg-[#7E9F8B] text-white shadow-[0_16px_35px_rgba(126,159,139,0.25)]"
                aria-label="Open voice conversation"
              >
                <HugeiconsIcon icon={Mic01Icon} size={20} strokeWidth={1.8} />
              </button>

              <div className="flex items-center justify-between gap-4 pt-2">
                {navigation.map((item) => (
                  <div key={item.to} className="flex-1">
                    <NavigationLink
                      icon={item.icon}
                      label={item.label}
                      minimal
                      to={item.to}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </nav>
      </div>

      <Suspense fallback={null}>
        {isVoiceModalOpen ? (
          <LazyInteractiveVoiceModal
            open={isVoiceModalOpen}
            onOpenChange={setIsVoiceModalOpen}
          />
        ) : null}
      </Suspense>
    </div>
  )
}
