import { motion } from "framer-motion"
import {
  BookOpen02Icon,
  Home01Icon,
  Mic01Icon,
  PanelRightCloseIcon,
  PanelRightOpenIcon,
} from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { Suspense, lazy, useState } from "react"
import { Navigate, NavLink, Outlet } from "react-router"

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
          "group flex items-center rounded-full border border-white/40 bg-white/35 text-[#2F3E36]/75 shadow-sm backdrop-blur-md transition-all hover:bg-white/55 hover:text-[#2F3E36]",
          minimal
            ? "mx-auto h-10 w-10 justify-center px-0"
            : compact
              ? "justify-center px-0 py-4"
              : "gap-3 px-4 py-3",
          isActive &&
            "bg-[#7E9F8B] text-white shadow-[0_10px_35px_rgba(126,159,139,0.28)]"
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
  const [isDesktopPanelVisible, setIsDesktopPanelVisible] = useState(true)

  function prepareVoiceModal() {
    void loadInteractiveVoiceModal()
  }

  if (!isReady) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-[#FDFBF7] text-sm text-[#2F3E36]/72">
        Preparing your dashboard...
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
        <div className="absolute inset-x-0 top-0 h-80 bg-[radial-gradient(circle_at_top,rgba(168,195,216,0.42),rgba(253,251,247,0.08),transparent_72%)]" />
        <div className="absolute -left-20 top-10 h-64 w-64 rounded-full bg-[#A8C3D8]/28 blur-3xl" />
        <div className="absolute bottom-20 right-[-3rem] h-72 w-72 rounded-full bg-[#7E9F8B]/22 blur-3xl" />
      </div>

      <div className="pointer-events-none fixed inset-0 hidden md:block">
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(253,251,247,0.72)_0%,rgba(253,251,247,0.34)_35%,rgba(253,251,247,0.12)_100%)]" />
      </div>

      <div className="fixed inset-0 z-0 hidden md:block">
        <motion.div
          initial={{ opacity: 0.45, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          className="absolute left-1/2 top-1/2 h-[118vh] w-[118vw] -translate-x-1/2 -translate-y-1/2"
        >
          <DeferredSoulTree
            emotion={currentMood}
            score={treeScore}
            deferMs={260}
            className="h-full rounded-none border-0 bg-transparent shadow-none"
          />
        </motion.div>
      </div>

      <div className="relative z-10 min-h-svh md:pointer-events-none">
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="pointer-events-none fixed left-1/2 top-6 z-20 hidden -translate-x-1/2 md:block"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-white/45 bg-white/38 px-4 py-2 text-sm font-medium text-[#2F3E36] shadow-sm backdrop-blur-xl">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: getEmotionColor(currentMood) }}
            />
            {formatEmotionLabel(currentMood)}
          </div>
        </motion.div>

        <aside className="fixed top-1/2 left-6 z-30 hidden w-20 -translate-y-1/2 rounded-[2rem] border border-white/40 bg-white/40 p-3 shadow-[0_18px_70px_rgba(47,62,54,0.12)] backdrop-blur-xl md:pointer-events-auto md:flex md:flex-col md:items-center md:justify-between md:gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#7E9F8B] text-sm font-semibold text-white shadow-[0_12px_25px_rgba(126,159,139,0.32)]">
            SF
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

          <motion.button
            type="button"
            whileHover={{ y: -2, scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            animate={{
              boxShadow: [
                "0 12px 30px rgba(126,159,139,0.24)",
                "0 18px 40px rgba(126,159,139,0.34)",
                "0 12px 30px rgba(126,159,139,0.24)",
              ],
            }}
            transition={{
              boxShadow: {
                duration: 2.6,
                repeat: Infinity,
                ease: "easeInOut",
              },
            }}
            onFocus={prepareVoiceModal}
            onMouseEnter={prepareVoiceModal}
            onClick={() => setIsVoiceModalOpen(true)}
            className="flex h-14 w-14 items-center justify-center rounded-full border border-white/60 bg-[#7E9F8B] text-white"
            aria-label="Open voice conversation"
          >
            <HugeiconsIcon icon={Mic01Icon} size={20} strokeWidth={1.8} />
          </motion.button>
        </aside>

        <main className="relative min-h-svh pb-24 md:pointer-events-none md:pb-0">
          <div className="mx-auto min-h-svh w-full max-w-md px-4 pt-4 md:max-w-none md:px-0 md:pt-0">
            <motion.button
              type="button"
              onClick={() => setIsDesktopPanelVisible((value) => !value)}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="fixed top-8 right-8 z-30 hidden h-12 w-12 items-center justify-center rounded-full border border-white/45 bg-white/42 text-[#2F3E36] shadow-[0_12px_40px_rgba(47,62,54,0.1)] backdrop-blur-xl md:pointer-events-auto md:flex"
              aria-label={
                isDesktopPanelVisible
                  ? "Hide right information panel"
                  : "Show right information panel"
              }
            >
              <HugeiconsIcon
                icon={isDesktopPanelVisible ? PanelRightCloseIcon : PanelRightOpenIcon}
                size={20}
                strokeWidth={1.8}
              />
            </motion.button>

            <motion.div
              animate={{
                opacity: isDesktopPanelVisible ? 1 : 0,
                x: isDesktopPanelVisible ? 0 : 420,
              }}
              transition={{ duration: 0.32, ease: "easeInOut" }}
              className={cn(
                "md:pointer-events-auto md:fixed md:right-8 md:top-8 md:bottom-8 md:w-[min(24rem,calc(100vw-9rem))]",
                !isDesktopPanelVisible && "md:pointer-events-none"
              )}
            >
              <div className="h-full md:overflow-hidden md:rounded-[2rem] md:border md:border-white/40 md:bg-white/40 md:shadow-[0_18px_70px_rgba(47,62,54,0.1)] md:backdrop-blur-xl">
                <div className="h-full md:overflow-y-auto md:overscroll-contain">
                  <Outlet />
                </div>
              </div>
            </motion.div>
          </div>
        </main>

        <nav className="fixed inset-x-0 bottom-3 z-30 px-4 md:hidden">
          <div className="mx-auto max-w-md">
            <div className="relative rounded-[1.6rem] border border-white/40 bg-white/46 px-3 pb-[calc(0.65rem+env(safe-area-inset-bottom))] pt-3 shadow-[0_14px_42px_rgba(47,62,54,0.1)] backdrop-blur-xl">
              <motion.button
                type="button"
                whileHover={{ y: -2, scale: 1.03 }}
                whileTap={{ scale: 0.96 }}
                animate={{
                  y: [0, -2, 0],
                  boxShadow: [
                    "0 16px 35px rgba(126,159,139,0.3)",
                    "0 22px 48px rgba(126,159,139,0.42)",
                    "0 16px 35px rgba(126,159,139,0.3)",
                  ],
                }}
                transition={{
                  y: {
                    duration: 2.8,
                    repeat: Infinity,
                    ease: "easeInOut",
                  },
                  boxShadow: {
                    duration: 2.8,
                    repeat: Infinity,
                    ease: "easeInOut",
                  },
                }}
                onFocus={prepareVoiceModal}
                onMouseEnter={prepareVoiceModal}
                onClick={() => setIsVoiceModalOpen(true)}
                className="absolute top-0 left-1/2 flex h-[3.9rem] w-[3.9rem] -translate-x-1/2 -translate-y-[46%] items-center justify-center rounded-full border border-white/60 bg-[#7E9F8B] text-white"
                aria-label="Open voice conversation"
              >
                <HugeiconsIcon icon={Mic01Icon} size={20} strokeWidth={1.8} />
              </motion.button>

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
