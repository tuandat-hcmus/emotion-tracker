import { HugeiconsIcon } from "@hugeicons/react"
import {
  BookOpen02Icon,
  Leaf02Icon,
  QuoteUpIcon,
  SparklesIcon,
} from "@hugeicons/core-free-icons"
import { motion } from "framer-motion"
import { Link } from "react-router"

import { DeferredSoulTree } from "~/components/home/deferred-soul-tree"
import { useSoulForest } from "~/context/soul-forest-context"
import { formatEmotionLabel, getEmotionColor } from "~/lib/emotions"

function StatCard({
  label,
  tone = "mint",
  value,
}: {
  label: string
  tone?: "mint" | "sky" | "sun"
  value: string
}) {
  const toneClass =
    tone === "sky"
      ? "bg-[#EDF8FF] text-[#1C6282]"
      : tone === "sun"
        ? "bg-[#FFF7D7] text-[#8B6500]"
        : "bg-[var(--brand-primary-soft)] text-[var(--brand-primary-muted)]"

  return (
    <div className="rounded-[1.8rem] bg-white/82 p-5 shadow-[0_18px_50px_rgba(17,70,62,0.08)]">
      <p className="text-sm text-[#69857E]">{label}</p>
      <p className={`mt-4 inline-flex rounded-full px-3 py-1 text-xs ${toneClass}`}>{value}</p>
    </div>
  )
}

export default function DashboardHome() {
  const { currentMood, home, lastQuote, timeline, treeScore } = useSoulForest()
  const latestEntry = timeline[0]
  const currentMoodColor = getEmotionColor(currentMood)

  return (
    <section className="space-y-4 p-4 md:p-6">
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className="rounded-[2.4rem] bg-[linear-gradient(135deg,#E6FFF4,#F7FFFB_52%,#E9F7FF)] p-6 shadow-[0_24px_70px_rgba(17,70,62,0.08)]"
      >
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_340px] xl:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-1.5 text-xs uppercase tracking-[0.2em] text-[var(--brand-primary-muted)]">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: currentMoodColor }}
              />
              {formatEmotionLabel(currentMood)}
            </div>

            <h1 className="mt-4 text-4xl font-semibold text-[#123530]">
              Your emotional map, simplified.
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-7 text-[#48685F]">
              Chat to reflect. Open journal to review the month.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                to="/app/chat"
                className="inline-flex items-center rounded-full bg-[var(--brand-primary)] px-5 py-3 text-sm text-[var(--brand-on-primary)] transition-colors hover:bg-[var(--brand-primary-strong)]"
              >
                <HugeiconsIcon
                  icon={SparklesIcon}
                  size={16}
                  strokeWidth={1.8}
                  className="mr-2"
                />
                Open chat
              </Link>
              <Link
                to="/app/journal"
                className="inline-flex items-center rounded-full bg-white/90 px-5 py-3 text-sm text-[#123530] transition-colors hover:bg-white"
              >
                <HugeiconsIcon
                  icon={BookOpen02Icon}
                  size={16}
                  strokeWidth={1.8}
                  className="mr-2"
                />
                View journal
              </Link>
            </div>
          </div>

          <div className="rounded-[2rem] bg-white/70 p-4">
            <DeferredSoulTree
              emotion={currentMood}
              score={treeScore}
              deferMs={120}
              className="h-64 rounded-[1.8rem] border-0 bg-transparent shadow-none"
            />
          </div>
        </div>
      </motion.div>

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Current mood" value={formatEmotionLabel(currentMood)} />
        <StatCard
          label="Entries this week"
          tone="sky"
          value={`${home?.recent_trend.entries_last_7_days ?? timeline.length}`}
        />
        <StatCard
          label="Tree score"
          tone="sun"
          value={`${Math.round(treeScore)}/100`}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.04, duration: 0.35, ease: "easeOut" }}
          className="rounded-[2rem] bg-white/82 p-5 shadow-[0_18px_50px_rgba(17,70,62,0.08)]"
        >
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-xl font-semibold text-[#123530]">Recent entries</h2>
            <Link to="/app/journal" className="text-sm text-[var(--brand-primary-muted)] hover:text-[var(--brand-primary-strong)]">
              Calendar
            </Link>
          </div>

          <div className="mt-4 space-y-3">
            {timeline.length === 0 ? (
              <div className="rounded-[1.5rem] bg-[#F7FFFC] p-5 text-sm text-[#5D7972]">
                No entries yet.
              </div>
            ) : (
              timeline.slice(0, 4).map((entry) => (
                <div key={entry.id} className="rounded-[1.5rem] bg-[#F7FFFC] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <span
                        className="flex h-10 w-10 items-center justify-center rounded-2xl"
                        style={{
                          backgroundColor: `${entry.moodColor}22`,
                          color: entry.moodColor,
                        }}
                      >
                        <HugeiconsIcon icon={Leaf02Icon} size={18} strokeWidth={1.8} />
                      </span>
                      <div>
                        <p className="text-sm font-medium text-[#123530]">
                          {entry.day} - {entry.time}
                        </p>
                        <p className="text-xs text-[#69857E]">
                          {formatEmotionLabel(entry.mood)}
                        </p>
                      </div>
                    </div>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-[#22453F]">{entry.summary}</p>
                </div>
              ))
            )}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08, duration: 0.35, ease: "easeOut" }}
          className="rounded-[2rem] bg-white/82 p-5 shadow-[0_18px_50px_rgba(17,70,62,0.08)]"
        >
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#FFF7D7] text-[#8B6500]">
              <HugeiconsIcon icon={QuoteUpIcon} size={18} strokeWidth={1.8} />
            </span>
            <div>
              <p className="text-sm text-[#69857E]">Quote</p>
              <p className="text-lg font-semibold text-[#123530]">Today</p>
            </div>
          </div>

          <p className="mt-4 text-sm leading-7 text-[#22453F]">{lastQuote}</p>

          {latestEntry ? (
            <div className="mt-5 rounded-[1.5rem] bg-[#EDFFF8] p-4">
              <p className="text-sm text-[var(--brand-primary-muted)]">Latest note</p>
              <p className="mt-2 text-sm leading-6 text-[#22453F]">{latestEntry.quote}</p>
            </div>
          ) : null}
        </motion.div>
      </div>
    </section>
  )
}
