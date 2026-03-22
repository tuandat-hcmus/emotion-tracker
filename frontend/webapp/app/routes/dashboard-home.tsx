import {
  Activity01Icon,
  FavouriteIcon,
  Leaf02Icon,
  Moon02Icon,
  QuoteUpIcon,
} from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { motion } from "framer-motion"
import { Link } from "react-router"

import { DeferredSoulTree } from "~/components/home/deferred-soul-tree"
import { Card, CardContent } from "~/components/ui/card"
import { useSoulForest } from "~/context/soul-forest-context"
import {
  EMOTION_META,
  formatEmotionLabel,
  SOUL_EMOTIONS,
  type SoulEmotion,
} from "~/lib/emotions"

const quickActions = [
  {
    label: "Breathe",
    detail: "Two slow rounds",
    icon: Leaf02Icon,
  },
  {
    label: "Quote",
    detail: "Grounding line",
    icon: QuoteUpIcon,
  },
  {
    label: "Evening",
    detail: "Soft reset",
    icon: Moon02Icon,
  },
] as const

function MoodBadge({
  color,
  label,
}: {
  color: string
  label: string
}) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-white/45 px-3 py-1.5 text-xs font-medium text-[#2F3E36]">
      <span
        className="h-2.5 w-2.5 rounded-full"
        style={{ backgroundColor: color }}
      />
      {label}
    </span>
  )
}

function QuickActionChip({
  detail,
  icon,
  label,
}: {
  detail: string
  icon: typeof Leaf02Icon
  label: string
}) {
  return (
    <button
      type="button"
      className="flex min-w-[8.5rem] flex-1 items-center gap-3 rounded-full border border-white/50 bg-white/35 px-4 py-3 text-left shadow-sm backdrop-blur-md transition-colors hover:bg-white/55"
    >
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#7E9F8B]/14 text-[#7E9F8B]">
        <HugeiconsIcon icon={icon} size={18} strokeWidth={1.8} />
      </span>
      <span className="min-w-0">
        <span className="block text-sm font-medium text-[#2F3E36]">{label}</span>
        <span className="block text-xs text-[#2F3E36]/58">{detail}</span>
      </span>
    </button>
  )
}

function EmotionTestButton({
  active,
  emotion,
  onClick,
}: {
  active: boolean
  emotion: SoulEmotion
  onClick: () => void
}) {
  const metadata = EMOTION_META[emotion]

  return (
    <motion.button
      type="button"
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      className={`rounded-full border px-4 py-2 text-sm transition-all ${
        active
          ? "border-transparent bg-[#2F3E36] text-white shadow-[0_12px_24px_rgba(47,62,54,0.12)]"
          : "border-white/50 bg-white/36 text-[#2F3E36] hover:bg-white/56"
      }`}
    >
      <span className="inline-flex items-center gap-2">
        <span
          className="h-2.5 w-2.5 rounded-full"
          style={{ backgroundColor: metadata.color }}
        />
        {metadata.label}
      </span>
    </motion.button>
  )
}

function TimelineDotRow({
  activeMood,
  entries,
}: {
  activeMood: string
  entries: Array<{
    id: string
    mood: string
    moodColor: string
    time: string
  }>
}) {
  return (
    <div className="flex items-center gap-3 overflow-x-auto pb-1">
      {entries.map((entry) => {
        const isActive = entry.mood === activeMood

        return (
          <div key={entry.id} className="flex shrink-0 flex-col items-center gap-2">
            <motion.div
              animate={
                isActive
                  ? {
                      boxShadow: [
                        `0 0 0 0 ${entry.moodColor}40`,
                        `0 0 0 10px ${entry.moodColor}00`,
                        `0 0 0 0 ${entry.moodColor}00`,
                      ],
                      scale: [1, 1.06, 1],
                    }
                  : { scale: 1 }
              }
              transition={{
                duration: 2.4,
                repeat: isActive ? Infinity : 0,
                ease: "easeInOut",
              }}
              className="flex h-11 w-11 items-center justify-center rounded-full border border-white/60 bg-white/40"
            >
              <span
                className="h-4 w-4 rounded-full"
                style={{ backgroundColor: entry.moodColor }}
              />
            </motion.div>
            <span className="text-[0.7rem] text-[#2F3E36]/58">{entry.time}</span>
          </div>
        )
      })}
    </div>
  )
}

function DesktopStat({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="rounded-[1.75rem] border border-white/45 bg-white/28 p-4">
      <p className="text-[0.68rem] uppercase tracking-[0.24em] text-[#7E9F8B]">
        {label}
      </p>
      <p className="mt-3 text-2xl font-semibold text-[#2F3E36]">{value}</p>
    </div>
  )
}

export default function DashboardHome() {
  const {
    currentMood,
    home,
    homeError,
    homeStatus,
    lastQuote,
    setEmotion,
    timeline,
    treeScore,
  } = useSoulForest()
  const todayTimeline = timeline.slice(0, 5)
  const latestEntry = timeline[0]
  const isHomeLoading = homeStatus === "loading" && !home
  const isTimelineEmpty = timeline.length === 0

  return (
    <div className="min-h-[calc(100svh-7rem)] md:min-h-full">
      <section className="relative flex min-h-[calc(100svh-7rem)] flex-col overflow-hidden md:hidden">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-[-4rem] top-12 h-40 w-40 rounded-full bg-[#A8C3D8]/25 blur-3xl" />
          <div className="absolute right-[-3rem] top-28 h-44 w-44 rounded-full bg-[#7E9F8B]/18 blur-3xl" />
        </div>

        <div className="relative h-[68svh] min-h-[29rem]">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: "easeOut" }}
            className="absolute inset-x-0 top-4 z-10 px-4"
          >
            <div className="flex items-center justify-between gap-3">
              <div className="rounded-full border border-white/50 bg-white/36 px-4 py-2 text-[0.68rem] uppercase tracking-[0.28em] text-[#7E9F8B] shadow-sm backdrop-blur-md">
                Soul Forest
              </div>
              <MoodBadge
                color={latestEntry?.moodColor ?? EMOTION_META[currentMood].color}
                label={formatEmotionLabel(currentMood)}
              />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.08, duration: 0.6, ease: "easeOut" }}
            className="absolute inset-0 pt-10"
          >
            <DeferredSoulTree
              emotion={currentMood}
              score={treeScore}
              deferMs={120}
              className="h-full scale-[1.12] rounded-none border-0 bg-transparent shadow-none"
            />
          </motion.div>

          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-[#FDFBF7] via-[#FDFBF7]/35 to-transparent" />
        </div>

        <Card className="-mt-12 flex min-h-0 flex-1 flex-col rounded-t-[2rem] border-b-0 bg-white/40 pb-24 shadow-[0_-16px_40px_rgba(47,62,54,0.08)]">
          <div className="flex justify-center pt-3">
            <span className="h-1.5 w-14 rounded-full bg-[#2F3E36]/12" />
          </div>

          <CardContent className="min-h-0 flex-1 space-y-6 overflow-y-auto px-5 pb-6 pt-4">
            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08, duration: 0.45 }}
              className="rounded-[1.75rem] border border-white/45 bg-gradient-to-r from-[#A8C3D8]/24 to-[#7E9F8B]/16 p-4"
            >
              <p className="text-[0.68rem] uppercase tracking-[0.24em] text-[#7E9F8B]">
                Today&apos;s canopy
              </p>
              <p className="mt-2 text-base font-semibold text-[#2F3E36]">
                A {formatEmotionLabel(currentMood).toLowerCase()} rhythm is
                moving through the tree.
              </p>
              <p className="mt-2 text-sm leading-6 text-[#2F3E36]/72">
                {isHomeLoading
                  ? "Loading your latest check-ins and tree state..."
                  : homeStatus === "error"
                  ? homeError
                  : "Let the tree breathe in full view, then tap the center mic when you want to add a new voice memory."}
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.45 }}
              className="space-y-3"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[0.68rem] uppercase tracking-[0.24em] text-[#7E9F8B]">
                    Test tree states
                  </p>
                  <h2 className="mt-1 text-lg font-semibold text-[#2F3E36]">
                    Drop a gem to preview emotions
                  </h2>
                </div>
                <span className="rounded-full bg-white/45 px-3 py-1.5 text-xs text-[#2F3E36]/68">
                  7 states
                </span>
              </div>

              <div className="flex flex-wrap gap-2">
                {SOUL_EMOTIONS.map((emotion) => (
                  <EmotionTestButton
                    key={emotion}
                    active={emotion === currentMood}
                    emotion={emotion}
                    onClick={() => setEmotion(emotion)}
                  />
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.12, duration: 0.45 }}
              className="space-y-3"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[0.68rem] uppercase tracking-[0.24em] text-[#7E9F8B]">
                    Daily mood timeline
                  </p>
                  <h2 className="mt-1 text-lg font-semibold text-[#2F3E36]">
                    Gentle shifts across today
                  </h2>
                </div>
                <span className="rounded-full bg-white/45 px-3 py-1.5 text-xs text-[#2F3E36]/68">
                  {todayTimeline.length} moments
                </span>
              </div>

              {isTimelineEmpty ? (
                <p className="text-sm leading-6 text-[#2F3E36]/64">
                  No journal moments have been synced yet. Add a text check-in or
                  start a conversation to populate this timeline.
                </p>
              ) : (
                <TimelineDotRow activeMood={currentMood} entries={todayTimeline} />
              )}
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.18, duration: 0.45 }}
              className="space-y-3"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[0.68rem] uppercase tracking-[0.24em] text-[#7E9F8B]">
                    Quick actions
                  </p>
                  <h2 className="mt-1 text-lg font-semibold text-[#2F3E36]">
                    Small rituals for right now
                  </h2>
                </div>
              </div>

              <div className="flex gap-3 overflow-x-auto pb-1">
                {quickActions.map((action) => (
                  <QuickActionChip
                    key={action.label}
                    detail={action.detail}
                    icon={action.icon}
                    label={action.label}
                  />
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.24, duration: 0.45 }}
              className="rounded-[1.75rem] border border-white/45 bg-gradient-to-r from-[#A8C3D8]/28 to-[#7E9F8B]/22 p-4"
            >
              <div className="flex items-start gap-3">
                <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/45 text-[#7E9F8B]">
                  <HugeiconsIcon icon={Activity01Icon} size={18} strokeWidth={1.8} />
                </span>
                <div>
                  <p className="text-[0.68rem] uppercase tracking-[0.24em] text-[#7E9F8B]">
                    Forest pulse
                  </p>
                  <p className="mt-2 text-base font-semibold text-[#2F3E36]">
                    Growth is holding at {Math.round(treeScore)}/100.
                  </p>
                  <p className="mt-2 text-sm leading-6 text-[#2F3E36]/72">
                    {lastQuote}
                  </p>
                </div>
              </div>
            </motion.div>
          </CardContent>
        </Card>
      </section>

      <section className="hidden h-full md:flex md:flex-col md:gap-5 md:p-6">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="rounded-[2rem] border border-white/45 bg-gradient-to-br from-[#A8C3D8]/30 via-white/28 to-[#7E9F8B]/18 p-5"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[0.68rem] uppercase tracking-[0.28em] text-[#7E9F8B]">
                Daily companion
              </p>
              <h1 className="mt-2 text-3xl leading-tight font-semibold text-[#2F3E36]">
                Your forest is ready to listen.
              </h1>
            </div>
            <MoodBadge
              color={latestEntry?.moodColor ?? EMOTION_META[currentMood].color}
              label={formatEmotionLabel(currentMood)}
            />
          </div>

          <p className="mt-4 text-sm leading-7 text-[#2F3E36]/72">
            {isHomeLoading
              ? "Syncing your latest dashboard state from the backend."
              : homeStatus === "error"
                ? homeError
                : "The canopy behind this panel stays live with your emotional state. Use the mic in the sidebar to begin a new voice ritual, or visit your journal to revisit what has already taken root."}
          </p>

          <div className="mt-5 flex gap-3">
            <Link
              to="/app/journal"
              className="inline-flex flex-1 items-center justify-center rounded-full bg-[#7E9F8B] px-4 py-3 text-sm font-medium text-white shadow-[0_16px_35px_rgba(126,159,139,0.22)] transition-colors hover:bg-[#6D8D7A]"
            >
              Open journal
            </Link>
            <div className="inline-flex flex-1 items-center justify-center rounded-full border border-white/50 bg-white/35 px-4 py-3 text-sm text-[#2F3E36]/72">
              Tap the mic to speak
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.04, duration: 0.45, ease: "easeOut" }}
          className="rounded-[2rem] border border-white/45 bg-white/28 p-4"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[0.68rem] uppercase tracking-[0.24em] text-[#7E9F8B]">
                Test tree states
              </p>
              <h2 className="mt-1 text-lg font-semibold text-[#2F3E36]">
                Tap a gem and watch it fall into the tree
              </h2>
            </div>
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#7E9F8B]/14 text-[#7E9F8B]">
              <HugeiconsIcon icon={FavouriteIcon} size={18} strokeWidth={1.8} />
            </span>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {SOUL_EMOTIONS.map((emotion) => (
              <EmotionTestButton
                key={emotion}
                active={emotion === currentMood}
                emotion={emotion}
                onClick={() => setEmotion(emotion)}
              />
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.06, duration: 0.45, ease: "easeOut" }}
          className="grid gap-3 sm:grid-cols-2"
        >
          <DesktopStat label="Tree growth" value={`${Math.round(treeScore)}/100`} />
          <DesktopStat
            label="Entries this week"
            value={`${home?.recent_trend.entries_last_7_days ?? timeline.length}`}
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12, duration: 0.45, ease: "easeOut" }}
          className="space-y-3"
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[0.68rem] uppercase tracking-[0.24em] text-[#7E9F8B]">
                Main actions
              </p>
              <h2 className="mt-1 text-lg font-semibold text-[#2F3E36]">
                Care rituals for this moment
              </h2>
            </div>
          </div>

          <div className="grid gap-3">
            {quickActions.map((action) => (
              <QuickActionChip
                key={action.label}
                detail={action.detail}
                icon={action.icon}
                label={action.label}
              />
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.18, duration: 0.45, ease: "easeOut" }}
          className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[2rem] border border-white/45 bg-white/28"
        >
          <div className="border-b border-white/45 px-5 py-4">
            <p className="text-[0.68rem] uppercase tracking-[0.24em] text-[#7E9F8B]">
              Daily timeline
            </p>
            <h2 className="mt-1 text-lg font-semibold text-[#2F3E36]">
              Recent canopy shifts
            </h2>
          </div>

          <div className="min-h-0 space-y-3 overflow-y-auto px-5 py-4">
            {isTimelineEmpty ? (
              <div className="rounded-[1.5rem] border border-dashed border-white/45 bg-white/22 p-5">
                <p className="text-sm leading-6 text-[#2F3E36]/68">
                  Your recent timeline is empty. Save a journal check-in to see
                  transcript excerpts, emotion labels, and response summaries here.
                </p>
              </div>
            ) : (
              timeline.map((entry, index) => (
                <motion.div
                  key={entry.id}
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.22 + index * 0.04, duration: 0.3 }}
                  className="rounded-[1.5rem] border border-white/45 bg-white/32 p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex min-w-0 gap-3">
                      <span
                        className="mt-1 h-3.5 w-3.5 shrink-0 rounded-full"
                        style={{ backgroundColor: entry.moodColor }}
                      />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-[#2F3E36]">
                          {entry.day} at {entry.time}
                        </p>
                        <p className="mt-1 text-sm leading-6 text-[#2F3E36]/70">
                          {entry.summary}
                        </p>
                      </div>
                    </div>
                    <MoodBadge
                      color={entry.moodColor}
                      label={formatEmotionLabel(entry.mood)}
                    />
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.24, duration: 0.45, ease: "easeOut" }}
          className="rounded-[2rem] border border-white/45 bg-gradient-to-r from-[#A8C3D8]/24 to-[#7E9F8B]/20 p-5"
        >
          <p className="text-[0.68rem] uppercase tracking-[0.24em] text-[#7E9F8B]">
            Latest grounding
          </p>
          <p className="mt-3 text-base leading-7 text-[#2F3E36]/76">
            {lastQuote}
          </p>
        </motion.div>
      </section>
    </div>
  )
}
