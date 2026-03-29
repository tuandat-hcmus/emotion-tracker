import { useState } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { BookOpen02Icon, HeadphonesIcon } from "@hugeicons/core-free-icons"

type ContentCategory = "all" | "books" | "podcasts"
type EmotionTag = "anxiety" | "sadness" | "stress" | "self-growth" | "mindfulness" | "grief" | "general"

interface ContentItem {
  id: string
  type: "book" | "podcast"
  title: string
  author: string
  description: string
  emotionTags: EmotionTag[]
  coverColor: string
}

const LIBRARY_CONTENT: ContentItem[] = [
  {
    id: "b1",
    type: "book",
    title: "The Body Keeps the Score",
    author: "Bessel van der Kolk",
    description: "How trauma reshapes the body and brain, and innovative treatments for recovery.",
    emotionTags: ["anxiety", "stress", "general"],
    coverColor: "#7C9A92",
  },
  {
    id: "b2",
    type: "book",
    title: "Feeling Good: The New Mood Therapy",
    author: "David D. Burns",
    description: "Clinically proven techniques to overcome depression and develop a positive outlook.",
    emotionTags: ["sadness", "anxiety", "self-growth"],
    coverColor: "#E8A87C",
  },
  {
    id: "b3",
    type: "book",
    title: "Wherever You Go, There You Are",
    author: "Jon Kabat-Zinn",
    description: "A guide to mindfulness meditation for everyday life.",
    emotionTags: ["mindfulness", "stress", "general"],
    coverColor: "#A8C3D8",
  },
  {
    id: "b4",
    type: "book",
    title: "It's OK That You're Not OK",
    author: "Megan Devine",
    description: "Meeting grief and loss in a culture that doesn't understand.",
    emotionTags: ["grief", "sadness"],
    coverColor: "#C2A4C5",
  },
  {
    id: "b5",
    type: "book",
    title: "Atomic Habits",
    author: "James Clear",
    description: "Tiny changes, remarkable results — building good habits and breaking bad ones.",
    emotionTags: ["self-growth", "general"],
    coverColor: "#F4C95D",
  },
  {
    id: "b6",
    type: "book",
    title: "Self-Compassion",
    author: "Kristin Neff",
    description: "The proven power of being kind to yourself in moments of struggle.",
    emotionTags: ["sadness", "anxiety", "self-growth"],
    coverColor: "#D4A5A5",
  },
  {
    id: "p1",
    type: "podcast",
    title: "The Happiness Lab",
    author: "Dr. Laurie Santos",
    description: "Yale professor explores the science of happiness and what really makes us feel better.",
    emotionTags: ["self-growth", "general"],
    coverColor: "#F6C667",
  },
  {
    id: "p2",
    type: "podcast",
    title: "On Being",
    author: "Krista Tippett",
    description: "Deep conversations about the big questions of meaning, faith, and what it means to be human.",
    emotionTags: ["mindfulness", "grief", "general"],
    coverColor: "#8FB8CA",
  },
  {
    id: "p3",
    type: "podcast",
    title: "Unlocking Us",
    author: "Brené Brown",
    description: "Explores the emotions and experiences that define what it means to be human.",
    emotionTags: ["anxiety", "self-growth", "general"],
    coverColor: "#B67D6D",
  },
  {
    id: "p4",
    type: "podcast",
    title: "Ten Percent Happier",
    author: "Dan Harris",
    description: "Practical meditation and mindfulness advice from a skeptic turned believer.",
    emotionTags: ["mindfulness", "stress", "anxiety"],
    coverColor: "#6B9E78",
  },
  {
    id: "p5",
    type: "podcast",
    title: "Therapy for Black Girls",
    author: "Dr. Joy Harden Bradford",
    description: "An accessible space for mental health conversations and practical coping tools.",
    emotionTags: ["sadness", "anxiety", "self-growth"],
    coverColor: "#D8A7B1",
  },
  {
    id: "p6",
    type: "podcast",
    title: "Tara Brach",
    author: "Tara Brach",
    description: "Guided meditations and talks on emotional healing and radical acceptance.",
    emotionTags: ["mindfulness", "grief", "stress"],
    coverColor: "#9DB5B2",
  },
]

const EMOTION_TAG_LABELS: Record<EmotionTag, string> = {
  anxiety: "Anxiety",
  sadness: "Sadness",
  stress: "Stress",
  "self-growth": "Self-Growth",
  mindfulness: "Mindfulness",
  grief: "Grief",
  general: "General",
}

export default function LibraryPage() {
  const [category, setCategory] = useState<ContentCategory>("all")
  const [selectedTag, setSelectedTag] = useState<EmotionTag | null>(null)

  const filtered = LIBRARY_CONTENT.filter((item) => {
    if (category === "books" && item.type !== "book") return false
    if (category === "podcasts" && item.type !== "podcast") return false
    if (selectedTag && !item.emotionTags.includes(selectedTag)) return false
    return true
  })

  const allTags: EmotionTag[] = ["anxiety", "sadness", "stress", "self-growth", "mindfulness", "grief", "general"]

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4 sm:p-6">
      {/* Header */}
      <div>
        <h1
          className="text-2xl text-[#163D33] sm:text-3xl"
          style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
        >
          Healing Library
        </h1>
        <p className="mt-2 text-sm leading-7 text-[#648078]">
          Books and podcasts to support your emotional wellness journey.
        </p>
      </div>

      {/* Category tabs */}
      <div className="flex gap-2">
        {(["all", "books", "podcasts"] as ContentCategory[]).map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setCategory(cat)}
            className={`rounded-full px-4 py-2 text-sm font-medium capitalize transition-colors ${
              category === cat
                ? "bg-[var(--brand-primary)] text-[var(--brand-on-primary)]"
                : "bg-white/60 text-[#2F3E36] hover:bg-white/80"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Emotion tag filters */}
      <div className="flex flex-wrap gap-2">
        {allTags.map((tag) => (
          <button
            key={tag}
            type="button"
            onClick={() => setSelectedTag(selectedTag === tag ? null : tag)}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
              selectedTag === tag
                ? "border-[var(--brand-primary)] bg-[var(--brand-primary-soft)] text-[var(--brand-primary-muted)]"
                : "border-[#DDF5EA] bg-white/60 text-[#648078] hover:bg-[#F8FFFC]"
            }`}
          >
            {EMOTION_TAG_LABELS[tag]}
          </button>
        ))}
      </div>

      {/* Content grid */}
      <div className="grid gap-4 sm:grid-cols-2">
        {filtered.map((item) => (
          <div
            key={item.id}
            className="rounded-[1.5rem] border border-[#DDF5EA] bg-white/88 p-5 shadow-[0_8px_24px_rgba(17,70,62,0.06)] transition-transform hover:-translate-y-0.5"
          >
            <div className="flex items-start gap-4">
              {/* Cover placeholder */}
              <div
                className="flex h-16 w-12 shrink-0 items-center justify-center rounded-lg"
                style={{ backgroundColor: `${item.coverColor}30` }}
              >
                <HugeiconsIcon
                  icon={item.type === "book" ? BookOpen02Icon : HeadphonesIcon}
                  size={20}
                  strokeWidth={1.8}
                  style={{ color: item.coverColor }}
                />
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-[#F0FFF7] px-2 py-0.5 text-[0.6rem] uppercase tracking-[0.15em] text-[#648078]">
                    {item.type}
                  </span>
                </div>
                <h3 className="mt-1.5 text-sm font-semibold leading-5 text-[#163D33]">
                  {item.title}
                </h3>
                <p className="mt-0.5 text-xs text-[#648078]">{item.author}</p>
                <p className="mt-2 text-xs leading-5 text-[#648078]">{item.description}</p>

                {/* Tags */}
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {item.emotionTags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-[#F0FFF7] px-2 py-0.5 text-[0.6rem] text-[#648078]"
                    >
                      {EMOTION_TAG_LABELS[tag]}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="rounded-[1.5rem] bg-white/60 p-8 text-center">
          <p className="text-sm text-[#648078]">No items match your filters.</p>
        </div>
      )}
    </div>
  )
}
