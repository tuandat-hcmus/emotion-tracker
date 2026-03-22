import {
  Activity01Icon,
  BookOpen02Icon,
  Leaf02Icon,
  QuoteUpIcon,
  SparklesIcon,
} from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { motion } from "framer-motion"
import { Link } from "react-router"

import { DeferredSoulTree } from "~/components/home/deferred-soul-tree"
import { useSoulForest } from "~/context/soul-forest-context"
import { EMOTION_META, formatEmotionLabel } from "~/lib/emotions"

function MoodBadge({
  color,
  label,
}: {
  color: string
  label: string
}) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-white/60 px-3 py-1.5 text-xs font-medium text-[#2F3E36]">
      <span
        className="h-2.5 w-2.5 rounded-full"
        style={{ backgroundColor: color }}
      />
      {label}
    </span>
  )
}

function MetricCard({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="rounded-[1.5rem] border border-white/45 bg-white/42 p-4">
      <p className="text-[0.68rem] uppercase tracking-[0.24em] text-[#7E9F8B]">
        {label}
      </p>
      <p className="mt-3 text-xl font-semibold text-[#2F3E36]">{value}</p>
    </div>
  )
}

export default function DashboardHome() {
  const { currentMood, home, homeError, homeStatus, lastQuote, timeline, treeScore } =
    useSoulForest()
  const latestEntry = timeline[0]
  const recentEntries = timeline.slice(0, 4)
  const isHomeLoading = homeStatus === "loading" && !home
  const isTimelineEmpty = timeline.length === 0
  const moodLabel = formatEmotionLabel(currentMood)
  const primaryTitle = isTimelineEmpty
    ? "Begin today's check-in"
    : "Return to today's reflection"
  const primaryMessage = isHomeLoading
    ? "Gathering your latest check-ins and recent patterns."
    : homeStatus === "error"
      ? "Your journal is still available, but the latest dashboard details could not be refreshed just now."
      : isTimelineEmpty
        ? "Start with a few honest lines about how today feels. The rest of the dashboard will grow from there."
        : latestEntry?.summary || "Pick up where you left off and add the next thought that feels true."

  return (
    <section className="space-y-5 p-4 md:p-6">
      <div className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="rounded-[2rem] border border-white/45 bg-gradient-to-br from-[#A8C3D8]/18 via-white/44 to-[#7E9F8B]/14 p-6"
        >
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-2xl">
              <p className="text-[0.7rem] uppercase tracking-[0.28em] text-[#7E9F8B]">
                Today&apos;s journal
              </p>
              <h1 className="mt-3 text-3xl leading-tight font-semibold text-[#2F3E36]">
                {primaryTitle}
              </h1>
              <p className="mt-4 text-sm leading-7 text-[#2F3E36]/72">
                {primaryMessage}
              </p>
            </div>

            <MoodBadge
              color={latestEntry?.moodColor ?? EMOTION_META[currentMood].color}
              label={moodLabel}
            />
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to="/app/journal"
              className="inline-flex items-center justify-center rounded-full bg-[#7E9F8B] px-5 py-3 text-sm font-medium text-white shadow-[0_16px_35px_rgba(126,159,139,0.22)] transition-colors hover:bg-[#6D8D7A]"
            >
              <HugeiconsIcon
                icon={BookOpen02Icon}
                size={16}
                strokeWidth={1.8}
                className="mr-2"
              />
              {isTimelineEmpty ? "Start writing" : "Open journal"}
            </Link>
            <div className="inline-flex items-center rounded-full border border-white/50 bg-white/48 px-5 py-3 text-sm text-[#2F3E36]/68">
              Use the mic when speaking feels easier.
            </div>
          </div>

          {homeStatus === "error" ? (
            <div className="mt-5 rounded-[1.25rem] bg-[#F7E9E2] px-4 py-3 text-sm text-[#8b4e3d]">
              {homeError || "Some dashboard details are unavailable right now."}
            </div>
          ) : null}

          {latestEntry ? (
            <div className="mt-6 rounded-[1.5rem] border border-white/45 bg-white/55 p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm font-medium text-[#2F3E36]">
                  Latest reflection
                </p>
                <p className="text-xs text-[#2F3E36]/56">
                  {latestEntry.day} at {latestEntry.time}
                </p>
              </div>
              <p className="mt-3 text-base leading-7 text-[#2F3E36]/78">
                {latestEntry.summary}
              </p>
              <p className="mt-4 rounded-[1.25rem] bg-[#FDFBF7]/72 px-4 py-3 text-sm leading-6 text-[#2F3E36]/68">
                {latestEntry.quote}
              </p>
            </div>
          ) : (
            <div className="mt-6 rounded-[1.5rem] border border-dashed border-white/50 bg-white/28 p-5">
              <p className="text-sm leading-6 text-[#2F3E36]/68">
                Your first reflection will appear here after you save a check-in.
              </p>
            </div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05, duration: 0.4, ease: "easeOut" }}
          className="rounded-[2rem] border border-white/45 bg-white/40 p-5"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[0.7rem] uppercase tracking-[0.28em] text-[#7E9F8B]">
                Forest support
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-[#2F3E36]">
                A calm view of where you are today
              </h2>
            </div>
            <span className="rounded-full bg-[#7E9F8B]/12 px-3 py-1.5 text-xs text-[#7E9F8B]">
              {Math.round(treeScore)}/100
            </span>
          </div>

          <div className="mt-5 rounded-[1.75rem] bg-[radial-gradient(circle_at_top,rgba(168,195,216,0.18),rgba(253,251,247,0.88),rgba(126,159,139,0.12))] p-3">
            <DeferredSoulTree
              emotion={currentMood}
              score={treeScore}
              deferMs={120}
              className="h-56 rounded-[1.4rem] border border-white/35 bg-transparent shadow-none"
            />
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <MetricCard
              label="Entries this week"
              value={`${home?.recent_trend.entries_last_7_days ?? timeline.length}`}
            />
            <MetricCard
              label="Today"
              value={`${home?.today.total_entries_today ?? timeline.length}`}
            />
          </div>

          <div className="mt-5 rounded-[1.5rem] border border-white/45 bg-gradient-to-r from-[#A8C3D8]/24 to-[#7E9F8B]/16 p-4">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/60 text-[#7E9F8B]">
                <HugeiconsIcon icon={QuoteUpIcon} size={18} strokeWidth={1.8} />
              </span>
              <div>
                <p className="text-[0.68rem] uppercase tracking-[0.24em] text-[#7E9F8B]">
                  Grounding line
                </p>
                <p className="mt-3 text-sm leading-7 text-[#2F3E36]/72">
                  {lastQuote}
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Current mood" value={moodLabel} />
        <MetricCard
          label="Recent pace"
          value={
            home?.recent_trend.last_7_days_average_stress != null
              ? `${Math.round(home.recent_trend.last_7_days_average_stress * 100)}% stress`
              : "Settling in"
          }
        />
        <MetricCard
          label="Tree stage"
          value={home?.tree.current_stage ?? "Growing gently"}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08, duration: 0.4, ease: "easeOut" }}
        className="rounded-[2rem] border border-white/45 bg-white/40 p-5"
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[0.7rem] uppercase tracking-[0.28em] text-[#7E9F8B]">
              Recent reflections
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-[#2F3E36]">
              What has been taking shape lately
            </h2>
          </div>
          <Link
            to="/app/journal"
            className="inline-flex items-center rounded-full border border-white/50 bg-white/52 px-4 py-2 text-sm text-[#2F3E36]/72 transition-colors hover:bg-white/72 hover:text-[#2F3E36]"
          >
            View full journal
          </Link>
        </div>

        <div className="mt-5 space-y-3">
          {isHomeLoading ? (
            <div className="rounded-[1.5rem] border border-dashed border-white/45 bg-white/24 p-5 text-sm leading-6 text-[#2F3E36]/68">
              Loading your recent reflections...
            </div>
          ) : isTimelineEmpty ? (
            <div className="rounded-[1.5rem] border border-dashed border-white/45 bg-white/24 p-5 text-sm leading-6 text-[#2F3E36]/68">
              Your journal is still quiet. Start a check-in to build a readable history here.
            </div>
          ) : (
            recentEntries.map((entry, index) => (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.12 + index * 0.04, duration: 0.28 }}
                className="rounded-[1.5rem] border border-white/45 bg-[#FDFBF7]/72 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-2">
                    <MoodBadge color={entry.moodColor} label={formatEmotionLabel(entry.mood)} />
                    <p className="text-sm font-medium text-[#2F3E36]">
                      {entry.day} at {entry.time}
                    </p>
                  </div>
                  <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#7E9F8B]/12 text-[#7E9F8B]">
                    <HugeiconsIcon
                      icon={index === 0 ? Activity01Icon : Leaf02Icon}
                      size={18}
                      strokeWidth={1.8}
                    />
                  </span>
                </div>
                <p className="mt-3 text-sm leading-7 text-[#2F3E36]/74">
                  {entry.summary}
                </p>
                <p className="mt-3 rounded-[1.1rem] bg-white/72 px-4 py-3 text-sm leading-6 text-[#2F3E36]/64">
                  {entry.quote}
                </p>
              </motion.div>
            ))
          )}
        </div>
      </motion.div>

      <div className="rounded-[1.75rem] border border-white/45 bg-gradient-to-r from-[#A8C3D8]/20 to-[#7E9F8B]/16 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[0.7rem] uppercase tracking-[0.28em] text-[#7E9F8B]">
              Secondary support
            </p>
            <p className="mt-2 text-base leading-7 text-[#2F3E36]/74">
              When writing feels hard, the conversation mic is there for a gentler back-and-forth.
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-white/55 px-4 py-2 text-sm text-[#2F3E36]/68">
            <HugeiconsIcon
              icon={SparklesIcon}
              size={16}
              strokeWidth={1.8}
              className="mr-2 text-[#7E9F8B]"
            />
            Optional support
          </span>
        </div>
      </div>
    </section>
  )
}
