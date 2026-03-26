import type {
  MonthlyWrapupDetailResponse,
  MonthlyWrapupHeadlineCard,
  MonthlyWrapupPatternItem,
  MonthlyWrapupWeeklyMetric,
} from "~/lib/contracts"

type TokenVisual = {
  bg: string
  border: string
  text: string
  accent: string
}

const COLOR_TOKENS: Record<string, TokenVisual> = {
  calm_blue: {
    bg: "linear-gradient(180deg, rgba(226,236,244,0.95), rgba(212,227,239,0.78))",
    border: "rgba(149,177,203,0.34)",
    text: "#315467",
    accent: "#6E99B3",
  },
  soft_yellow: {
    bg: "linear-gradient(180deg, rgba(251,244,205,0.96), rgba(247,233,183,0.8))",
    border: "rgba(213,186,102,0.34)",
    text: "#6E5721",
    accent: "#D7B04D",
  },
  warm_pink: {
    bg: "linear-gradient(180deg, rgba(248,226,227,0.96), rgba(244,212,216,0.82))",
    border: "rgba(206,150,160,0.34)",
    text: "#734753",
    accent: "#D1869A",
  },
  forest_green: {
    bg: "linear-gradient(180deg, rgba(224,239,226,0.96), rgba(204,226,208,0.8))",
    border: "rgba(117,157,126,0.34)",
    text: "#355743",
    accent: "#6F9C7D",
  },
  lavender: {
    bg: "linear-gradient(180deg, rgba(236,229,247,0.96), rgba(223,214,240,0.82))",
    border: "rgba(160,144,196,0.34)",
    text: "#56497A",
    accent: "#9A86BF",
  },
  sunset_orange: {
    bg: "linear-gradient(180deg, rgba(250,229,210,0.96), rgba(244,209,177,0.82))",
    border: "rgba(208,145,100,0.34)",
    text: "#7A4B2C",
    accent: "#D88C58",
  },
}

const DEFAULT_TOKEN = COLOR_TOKENS.calm_blue

function getTokenVisual(token: string | null | undefined) {
  return (token && COLOR_TOKENS[token]) || DEFAULT_TOKEN
}

function formatValue(value: string | number | null | undefined) {
  if (value == null) {
    return "Not enough yet"
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? `${value}` : value.toFixed(1)
  }
  return value
}

function formatPercent(value: number | null | undefined) {
  if (typeof value !== "number") {
    return "n/a"
  }
  return `${Math.round(value * 100)}%`
}

function formatStatValue(value: string | number | null | undefined) {
  if (value == null || value === "") {
    return "Not enough yet"
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? `${value}` : value.toFixed(1)
  }
  return value
}

function formatWeekRange(item: MonthlyWrapupWeeklyMetric) {
  const start = new Date(item.date_from)
  const end = new Date(item.date_to)

  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return item.week_label
  }

  return `${start.toLocaleDateString([], { month: "short", day: "numeric" })} - ${end.toLocaleDateString([], { day: "numeric" })}`
}

function SemanticIcon({
  iconKey,
  color,
  className = "h-5 w-5",
}: {
  iconKey: string
  color: string
  className?: string
}) {
  const commonProps = {
    className,
    fill: "none",
    stroke: color,
    strokeWidth: 1.75,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    viewBox: "0 0 24 24",
  }

  switch (iconKey) {
    case "sun":
      return (
        <svg {...commonProps}>
          <circle cx="12" cy="12" r="4.25" />
          <path d="M12 2.75v2.1M12 19.15v2.1M4.86 4.86l1.48 1.48M17.66 17.66l1.48 1.48M2.75 12h2.1M19.15 12h2.1M4.86 19.14l1.48-1.48M17.66 6.34l1.48-1.48" />
        </svg>
      )
    case "moon":
      return (
        <svg {...commonProps}>
          <path d="M15.6 3.15a8.55 8.55 0 1 0 5.25 15.43A9.6 9.6 0 0 1 15.6 3.15Z" />
        </svg>
      )
    case "leaf":
      return (
        <svg {...commonProps}>
          <path d="M19.75 4.25c-6.7-.7-11.66 2.4-13.1 8.04-.63 2.48-.2 4.92.73 7.46 2.56-.98 4.86-2.06 6.57-4.03 2.84-3.3 3.4-6.95 5.8-11.47Z" />
          <path d="M7.6 19.15c2.92-3.65 5.77-5.95 9.55-8.2" />
        </svg>
      )
    case "seed":
      return (
        <svg {...commonProps}>
          <path d="M12.1 20.2c-.1-4.4.12-7.55 3.06-10.52 1.46-1.46 3.45-2.49 5.84-2.82-.32 2.35-1.31 4.32-2.78 5.8-2.96 2.97-6.12 3.24-10.51 3.08" />
          <path d="M12 20.25c.06-3.2-.53-5.6-2.63-7.7-1.12-1.12-2.6-1.94-4.37-2.27.27 1.74 1.07 3.22 2.18 4.33C9.3 16.74 11.12 17.2 12 20.25Z" />
        </svg>
      )
    case "wave":
      return (
        <svg {...commonProps}>
          <path d="M2.5 14.5c2.05 0 2.05-2 4.1-2s2.05 2 4.1 2 2.05-2 4.1-2 2.05 2 4.1 2 2.05-2 4.1-2" />
          <path d="M2.5 9.5c2.05 0 2.05-2 4.1-2s2.05 2 4.1 2 2.05-2 4.1-2 2.05 2 4.1 2 2.05-2 4.1-2" />
        </svg>
      )
    case "cloud":
      return (
        <svg {...commonProps}>
          <path d="M6.3 18.2h10.4a3.8 3.8 0 0 0 .56-7.55 5.45 5.45 0 0 0-10.48-1.3A4.4 4.4 0 0 0 6.3 18.2Z" />
        </svg>
      )
    case "spark":
      return (
        <svg {...commonProps}>
          <path d="m12 2.75 1.54 4.79L18.3 9.1l-4.76 1.55L12 15.45l-1.54-4.8L5.7 9.1l4.76-1.56L12 2.75Z" />
          <path d="m18.2 15.6.76 2.35 2.34.76-2.34.77-.76 2.34-.77-2.34-2.34-.77 2.34-.76.77-2.35Z" />
        </svg>
      )
    default:
      return (
        <svg {...commonProps}>
          <path d="M12 20.4s-6.9-4.13-6.9-9.45A4.13 4.13 0 0 1 12 7.95a4.13 4.13 0 0 1 6.9 3c0 5.32-6.9 9.45-6.9 9.45Z" />
        </svg>
      )
  }
}

function FeaturedCard({ card }: { card: MonthlyWrapupHeadlineCard }) {
  const token = getTokenVisual(card.color_token)

  return (
    <div
      className="rounded-[1.4rem] border p-4 shadow-[0_18px_34px_rgba(73,87,81,0.08)]"
      style={{
        background: token.bg,
        borderColor: token.border,
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[0.65rem] uppercase tracking-[0.18em]" style={{ color: token.text }}>
            Monthly highlight
          </p>
          <h4 className="mt-2 text-base font-semibold text-[#2F3E36]">{card.title}</h4>
          {card.subtitle ? (
            <p className="mt-1 text-sm leading-6 text-[#2F3E36]/68">{card.subtitle}</p>
          ) : null}
        </div>
        <div
          className="flex h-11 w-11 items-center justify-center rounded-full border bg-white/55"
          style={{ borderColor: token.border }}
        >
          <SemanticIcon iconKey={card.icon_key} color={token.text} />
        </div>
      </div>
      <p className="mt-5 text-2xl font-semibold tracking-tight text-[#2F3E36]">
        {formatValue(card.value)}
      </p>
      {card.supporting_text ? (
        <p className="mt-2 text-sm leading-6 text-[#2F3E36]/66">{card.supporting_text}</p>
      ) : null}
    </div>
  )
}

function SecondaryCard({ card }: { card: MonthlyWrapupHeadlineCard }) {
  const token = getTokenVisual(card.color_token)

  return (
    <div
      className="rounded-[1.15rem] border p-3.5"
      style={{
        background: "rgba(255,255,255,0.58)",
        borderColor: token.border,
      }}
    >
      <div className="flex items-start gap-3">
        <div
          className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full"
          style={{ backgroundColor: `${token.accent}20` }}
        >
          <SemanticIcon iconKey={card.icon_key} color={token.accent} className="h-[18px] w-[18px]" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-[#2F3E36]">{card.title}</p>
          <p className="mt-1 text-sm text-[#2F3E36]/70">{formatValue(card.value)}</p>
          {card.supporting_text ? (
            <p className="mt-2 text-[0.76rem] leading-5 text-[#2F3E36]/54">{card.supporting_text}</p>
          ) : null}
        </div>
      </div>
    </div>
  )
}

function SummaryMetric({
  label,
  value,
  emphasis = false,
}: {
  label: string
  value: string
  emphasis?: boolean
}) {
  return (
    <div className={`rounded-[1rem] border border-white/42 bg-white/50 px-3 py-3 ${emphasis ? "shadow-[0_12px_24px_rgba(73,87,81,0.07)]" : ""}`}>
      <p className="text-[0.68rem] uppercase tracking-[0.14em] text-[#2F3E36]/44">{label}</p>
      <p className={`mt-2 ${emphasis ? "text-lg font-semibold" : "text-sm font-medium"} text-[#2F3E36]`}>
        {value}
      </p>
    </div>
  )
}

function EmotionDistributionChart({
  items,
}: {
  items: MonthlyWrapupDetailResponse["distributions"]["emotion_distribution"]
}) {
  if (items.length === 0) {
    return (
      <div className="rounded-[1rem] bg-white/48 px-4 py-5 text-sm leading-6 text-[#2F3E36]/58">
        Emotion distribution appears once a few processed check-ins are available this month.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {items.slice(0, 4).map((item) => {
        const token = getTokenVisual(
          item.label.toLowerCase().includes("stress") || item.label.toLowerCase().includes("anx")
            ? "sunset_orange"
            : item.label.toLowerCase().includes("sad")
              ? "lavender"
              : item.label.toLowerCase().includes("joy") || item.label.toLowerCase().includes("grat")
                ? "soft_yellow"
                : "warm_pink"
        )

        return (
          <div key={item.label} className="space-y-1.5">
            <div className="flex items-center justify-between gap-3 text-sm text-[#2F3E36]/68">
              <span>{item.label}</span>
              <span>{item.percent.toFixed(1)}%</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-white/62">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${item.percent}%`,
                  backgroundColor: token.accent,
                }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

function WeeklyRhythmChart({ items }: { items: MonthlyWrapupWeeklyMetric[] }) {
  if (items.length === 0) {
    return (
      <div className="rounded-[1rem] bg-white/48 px-4 py-5 text-sm leading-6 text-[#2F3E36]/58">
        Weekly rhythm will appear here once this month has stored entries.
      </div>
    )
  }

  const maxCount = Math.max(...items.map((item) => item.count), 1)

  return (
    <div className="flex items-end gap-2">
      {items.map((item) => (
        <div key={item.week_label} className="flex flex-1 flex-col items-center gap-2">
          <div className="flex h-[4.5rem] w-full items-end rounded-[0.9rem] bg-white/48 p-1.5">
            <div
              className="w-full rounded-[0.65rem] bg-[linear-gradient(180deg,#D3E6D7,#7E9F8B)]"
              style={{
                height: `${Math.max((item.count / maxCount) * 100, item.count > 0 ? 20 : 8)}%`,
                opacity: item.count > 0 ? 0.92 : 0.35,
              }}
            />
          </div>
          <div className="text-center">
            <p className="text-[0.68rem] text-[#2F3E36]/48">{item.week_label}</p>
            <p className="text-[0.68rem] text-[#2F3E36]/58">{item.count}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

function WeeklyStressChart({ items }: { items: MonthlyWrapupWeeklyMetric[] }) {
  const points = items
    .map((item) => item.avg_stress_score)
    .filter((value): value is number => typeof value === "number")

  if (points.length === 0) {
    return (
      <div className="rounded-[1rem] bg-white/48 px-4 py-5 text-sm leading-6 text-[#2F3E36]/58">
        Weekly stress trend appears after enough stress-scored check-ins are available.
      </div>
    )
  }

  const width = 220
  const height = 72
  const min = Math.min(...points)
  const max = Math.max(...points)
  const range = max - min || 1

  const path = points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * width
      const y = height - ((point - min) / range) * (height - 20) - 10
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(" ")

  return (
    <div className="space-y-3">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-[4.5rem] w-full overflow-visible">
        <path
          d={path}
          fill="none"
          stroke="#D88C58"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <div className="flex justify-between gap-2 text-[0.68rem] text-[#2F3E36]/48">
        {items.slice(0, points.length).map((item) => (
          <span key={item.week_label}>{item.week_label}</span>
        ))}
      </div>
    </div>
  )
}

function PatternSection({
  title,
  items,
  emptyText,
}: {
  title: string
  items: MonthlyWrapupPatternItem[]
  emptyText: string
}) {
  return (
    <div className="rounded-[1.1rem] bg-white/42 p-3.5">
      <p className="text-sm font-medium text-[#2F3E36]">{title}</p>
      {items.length === 0 ? (
        <p className="mt-2 text-sm leading-6 text-[#2F3E36]/56">{emptyText}</p>
      ) : (
        <div className="mt-3 flex flex-wrap gap-2">
          {items.slice(0, 4).map((item) => {
            const token = getTokenVisual(item.color_token)
            return (
              <span
                key={`${title}-${item.label}`}
                className="inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[0.74rem]"
                style={{
                  borderColor: token.border,
                  background: "rgba(255,255,255,0.68)",
                  color: token.text,
                }}
              >
                <SemanticIcon iconKey={item.icon_key} color={token.accent} className="h-3.5 w-3.5" />
                <span>{item.label}</span>
                <span className="text-[#2F3E36]/44">{item.count}</span>
              </span>
            )
          })}
        </div>
      )}
    </div>
  )
}

export function MonthlyWrapupPanel({
  detail,
}: {
  detail: MonthlyWrapupDetailResponse | null
}) {
  if (!detail) {
    return (
      <div className="rounded-[1.15rem] bg-[#FDFBF7]/44 p-4">
        <p className="text-sm font-medium text-[#2F3E36]">Monthly recap</p>
        <p className="mt-3 text-sm leading-6 text-[#2F3E36]/64">
          Monthly reflection is loading.
        </p>
      </div>
    )
  }

  const heroCard = detail.headline_cards[0] ?? null
  const supportingCards = detail.headline_cards.slice(1, 4)
  const themeToken = getTokenVisual(detail.visual_hints.month_mood_color)
  const hasNoData = detail.overview.overall_checkin_count === 0

  return (
    <div className="space-y-4">
      <div
        className="rounded-[1.2rem] border p-4"
        style={{
          background: `radial-gradient(circle at top right, ${themeToken.accent}20, rgba(255,255,255,0.68) 58%)`,
          borderColor: themeToken.border,
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[0.68rem] uppercase tracking-[0.2em] text-[#7E9F8B]">
              {detail.period.label}
            </p>
            <p className="mt-2 text-base font-semibold text-[#2F3E36]">Monthly recap</p>
          </div>
          <div
            className="flex h-11 w-11 items-center justify-center rounded-full border bg-white/66"
            style={{ borderColor: themeToken.border }}
          >
            <SemanticIcon
              iconKey={detail.visual_hints.month_theme_icon}
              color={themeToken.accent}
            />
          </div>
        </div>
        <p className="mt-3 text-sm leading-6 text-[#2F3E36]/68">
          {detail.overview.summary_text || "This month does not have enough processed check-ins for a fuller reflection yet."}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="rounded-full bg-white/70 px-3 py-1.5 text-[0.72rem] text-[#2F3E36]/70">
            {detail.overview.dominant_emotion || "No dominant emotion yet"}
          </span>
          <span className="rounded-full bg-white/70 px-3 py-1.5 text-[0.72rem] text-[#2F3E36]/70">
            {detail.overview.emotional_direction_trend}
          </span>
          <span className="rounded-full bg-white/70 px-3 py-1.5 text-[0.72rem] text-[#2F3E36]/70">
            {formatPercent(detail.overview.high_stress_frequency)} high stress
          </span>
        </div>
      </div>

      {heroCard ? <FeaturedCard card={heroCard} /> : null}

      {supportingCards.length > 0 ? (
        <div className="space-y-3">
          {supportingCards.map((card) => (
            <SecondaryCard key={card.id} card={card} />
          ))}
        </div>
      ) : null}

      <div className="rounded-[1.15rem] bg-[#FDFBF7]/44 p-4">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm font-medium text-[#2F3E36]">At a glance</p>
          <span className="rounded-full bg-white/68 px-3 py-1 text-[0.68rem] text-[#2F3E36]/56">
            {detail.stats.total_checkins} check-ins
          </span>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3">
          <SummaryMetric
            label="Active days"
            value={formatStatValue(detail.stats.active_days)}
            emphasis
          />
          <SummaryMetric
            label="Best streak"
            value={formatStatValue(detail.stats.best_streak_days)}
            emphasis
          />
          <SummaryMetric
            label="Top trigger"
            value={formatStatValue(detail.stats.top_trigger)}
          />
          <SummaryMetric
            label="Positive anchor"
            value={formatStatValue(detail.stats.top_positive_anchor)}
          />
          <SummaryMetric
            label="Average stress"
            value={formatStatValue(detail.stats.avg_stress_score)}
          />
          <SummaryMetric
            label="Longest gap"
            value={formatStatValue(detail.stats.longest_gap_days)}
          />
        </div>
      </div>

      <div className="rounded-[1.15rem] bg-[#FDFBF7]/44 p-4">
        <p className="text-sm font-medium text-[#2F3E36]">Emotion distribution</p>
        <div className="mt-4">
          <EmotionDistributionChart items={detail.distributions.emotion_distribution} />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
        <div className="rounded-[1.15rem] bg-[#FDFBF7]/44 p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-medium text-[#2F3E36]">Weekly rhythm</p>
            <span className="text-[0.68rem] text-[#2F3E36]/48">
              {detail.period.date_from.slice(5)} to {detail.period.date_to.slice(5)}
            </span>
          </div>
          <div className="mt-4">
            <WeeklyRhythmChart items={detail.distributions.weekly_checkin_counts} />
          </div>
        </div>

        <div className="rounded-[1.15rem] bg-[#FDFBF7]/44 p-4">
          <p className="text-sm font-medium text-[#2F3E36]">Stress trend</p>
          <div className="mt-4">
            <WeeklyStressChart items={detail.distributions.weekly_stress_trend} />
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <PatternSection
          title="Recurring triggers"
          items={detail.pattern_lists.recurring_triggers}
          emptyText="No repeated trigger has surfaced clearly this month."
        />
        <PatternSection
          title="Positive anchors"
          items={detail.pattern_lists.positive_anchors}
          emptyText="Positive anchors appear here when they repeat across check-ins."
        />
        <PatternSection
          title="Workload patterns"
          items={detail.pattern_lists.workload_deadline_patterns}
          emptyText="No repeated workload or deadline signal was saved this month."
        />
        <PatternSection
          title="Emotional patterns"
          items={detail.pattern_lists.dominant_emotional_patterns}
          emptyText="A clearer emotional pattern will appear once more check-ins are saved."
        />
      </div>

      {hasNoData ? (
        <p className="rounded-[1rem] border border-dashed border-white/42 bg-white/22 px-4 py-4 text-sm leading-6 text-[#2F3E36]/62">
          This month is still quiet. A few honest check-ins are enough to turn this into a more meaningful reflection.
        </p>
      ) : null}
    </div>
  )
}
