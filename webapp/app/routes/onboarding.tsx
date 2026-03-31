import { AnimatePresence, motion } from "framer-motion"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

import { DeferredSoulTree } from "~/components/home/deferred-soul-tree"

// ─── Question types ───────────────────────────────────────────────────────────

type EmojiScaleQuestion = {
  id: string; type: "emoji-scale"; question: string
  options: { emoji: string; label: string; value: number }[]
}
type MultipleChoiceQuestion = {
  id: string; type: "multiple-choice"; multi?: boolean; question: string
  options: { label: string; value: string }[]
}
type SliderQuestion = {
  id: string; type: "slider"; question: string
  min: number; max: number; minLabel: string; maxLabel: string
}
type ShortTextQuestion = {
  id: string; type: "short-text"; question: string; placeholder: string
}
type Question = EmojiScaleQuestion | MultipleChoiceQuestion | SliderQuestion | ShortTextQuestion

// ─── Survey questions ─────────────────────────────────────────────────────────

const QUESTIONS: Question[] = [
  {
    id: "current_mood", type: "emoji-scale",
    question: "How are you feeling right now?",
    options: [
      { emoji: "😢", label: "Really low",  value: 1 },
      { emoji: "😟", label: "Not great",   value: 2 },
      { emoji: "😐", label: "Okay",        value: 3 },
      { emoji: "🙂", label: "Pretty good", value: 4 },
      { emoji: "😄", label: "Great!",      value: 5 },
    ],
  },
  {
    id: "mood_triggers", type: "multiple-choice", multi: true,
    question: "What tends to affect your mood most?",
    options: [
      { label: "Work or study",     value: "work" },
      { label: "Relationships",     value: "relationships" },
      { label: "Sleep & rest",      value: "sleep" },
      { label: "Physical health",   value: "health" },
      { label: "Money & finances",  value: "finances" },
      { label: "Sense of purpose",  value: "purpose" },
    ],
  },
  {
    id: "stress_level", type: "slider",
    question: "What's your stress level this week?",
    min: 0, max: 10, minLabel: "Very calm", maxLabel: "Very stressed",
  },
  {
    id: "journal_goals", type: "multiple-choice", multi: true,
    question: "What do you hope to get from this journal?",
    options: [
      { label: "Track emotions over time", value: "track" },
      { label: "Process my thoughts",      value: "process" },
      { label: "Reduce anxiety",           value: "anxiety" },
      { label: "Understand my patterns",   value: "patterns" },
      { label: "Build self-awareness",     value: "awareness" },
      { label: "Just curious!",            value: "curious" },
    ],
  },
  {
    id: "reflection_frequency", type: "multiple-choice", multi: false,
    question: "How often do you reflect on your emotions?",
    options: [
      { label: "Rarely — this is new for me",    value: "rarely" },
      { label: "Sometimes, when things get hard", value: "sometimes" },
      { label: "Fairly often",                   value: "often" },
      { label: "Daily — it's a habit already",   value: "daily" },
    ],
  },
  {
    id: "one_word", type: "short-text",
    question: "In a few words, describe how you feel today.",
    placeholder: "e.g. tired but hopeful, anxious about tomorrow…",
  },
]

type Answers = Record<string, string | string[] | number>

// ─── Floating particles background ───────────────────────────────────────────

const PARTICLES = [
  { x: "8%",  y: "12%", d: 6,  delay: 0,   dur: 7  },
  { x: "88%", y: "18%", d: 4,  delay: 1.2, dur: 9  },
  { x: "22%", y: "35%", d: 8,  delay: 0.5, dur: 11 },
  { x: "72%", y: "8%",  d: 5,  delay: 2,   dur: 8  },
  { x: "50%", y: "28%", d: 3,  delay: 1.8, dur: 10 },
  { x: "15%", y: "58%", d: 7,  delay: 0.8, dur: 13 },
  { x: "82%", y: "55%", d: 4,  delay: 3,   dur: 9  },
  { x: "38%", y: "70%", d: 5,  delay: 1.5, dur: 12 },
  { x: "65%", y: "80%", d: 6,  delay: 0.3, dur: 8  },
  { x: "92%", y: "75%", d: 3,  delay: 2.5, dur: 11 },
]

function NatureBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute inset-0 bg-[#FDFBF7]" />
      <div className="absolute inset-x-0 top-0 h-80 bg-[radial-gradient(ellipse_at_top,rgba(18,199,127,0.12),transparent_70%)]" />
      <div className="absolute inset-x-0 bottom-0 h-60 bg-[radial-gradient(ellipse_at_bottom,rgba(168,195,216,0.14),transparent_70%)]" />
      <div className="absolute -left-16 top-24 h-64 w-64 rounded-full bg-[#12c77f]/10 blur-3xl" />
      <div className="absolute -right-16 bottom-32 h-72 w-72 rounded-full bg-[#A8C3D8]/16 blur-3xl" />
      {PARTICLES.map((p, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full bg-[#12c77f]"
          style={{ left: p.x, top: p.y, width: p.d, height: p.d, opacity: 0.18 }}
          animate={{ y: [0, -18, 0], opacity: [0.18, 0.32, 0.18] }}
          transition={{ duration: p.dur, delay: p.delay, repeat: Infinity, ease: "easeInOut" }}
        />
      ))}
    </div>
  )
}

// ─── Growing tree on success screen ──────────────────────────────────────────

function GrowingTreeScene() {
  const [score, setScore] = useState(10)

  // Animate score upward so the tree visibly grows from seedling → full
  useEffect(() => {
    const steps = [20, 35, 52, 68, 80, 88]
    let i = 0
    const id = setInterval(() => {
      setScore(steps[i] ?? 88)
      i++
      if (i >= steps.length) clearInterval(id)
    }, 380)
    return () => clearInterval(id)
  }, [])

  return (
    <DeferredSoulTree
      emotion="joy"
      score={score}
      animateTransition
      deferMs={100}
      className="h-64 w-full rounded-[1.8rem] border-0 bg-transparent shadow-none"
    />
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<"intro" | "survey" | "done">("intro")
  const [questionIndex, setQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Answers>({})

  const question = QUESTIONS[questionIndex]
  const progress = ((questionIndex + 1) / QUESTIONS.length) * 100

  function setAnswer(id: string, value: string | string[] | number) {
    setAnswers((prev) => ({ ...prev, [id]: value }))
  }
  function toggleMulti(id: string, value: string) {
    setAnswers((prev) => {
      const cur = (prev[id] as string[] | undefined) ?? []
      return { ...prev, [id]: cur.includes(value) ? cur.filter((v) => v !== value) : [...cur, value] }
    })
  }
  function canAdvance() {
    if (!question) return false
    const ans = answers[question.id]
    if (question.type === "slider") return ans !== undefined
    if (question.type === "short-text") return typeof ans === "string" && ans.trim().length > 0
    if (question.type === "multiple-choice" && question.multi) return Array.isArray(ans) && ans.length > 0
    return ans !== undefined && ans !== ""
  }
  function advance() {
    if (questionIndex < QUESTIONS.length - 1) setQuestionIndex((i) => i + 1)
    else setStep("done")
  }
  function finish() {
    localStorage.setItem("eflow_onboarding_done", "1")
    navigate("/app/home")
  }

  return (
    <div className="relative flex min-h-svh flex-col items-center justify-center overflow-hidden px-5 py-10">
      <NatureBackground />

      <div className="relative z-10 w-full max-w-sm">
        <AnimatePresence mode="wait">

          {/* ── INTRO ── */}
          {step === "intro" && (
            <motion.div key="intro"
              initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="flex flex-col items-center text-center"
            >
              {/* 3D Soul Tree — same component as /app/home */}
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.15, duration: 0.55 }}
                className="w-full"
              >
                <DeferredSoulTree
                  emotion="neutral"
                  score={62}
                  animateTransition={false}
                  deferMs={120}
                  className="h-64 w-full rounded-[1.8rem] border border-[#DDF5EA] bg-white/40 shadow-[0_8px_32px_rgba(47,62,54,0.07)]"
                />
              </motion.div>

              {/* Text */}
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.35, duration: 0.4 }} className="mt-6">
                <h1 className="text-2xl font-semibold leading-snug text-[#163D33]"
                  style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}>
                  Create your own journey
                </h1>
                <p className="mt-2.5 text-sm leading-6 text-[#648078]">
                  A few gentle questions to personalize your experience. Takes about 2 minutes.
                </p>
              </motion.div>

              {/* Perks */}
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }} className="mt-5 w-full space-y-2">
                {["No wrong answers", "Completely private", "Helps your tree grow"].map((line) => (
                  <div key={line} className="flex items-center gap-3 rounded-[1rem] border border-[#DDF5EA] bg-white/70 px-4 py-2.5 text-sm text-[#2F3E36]">
                    <span className="text-[#12c77f]">✓</span>
                    {line}
                  </div>
                ))}
              </motion.div>

              <motion.button type="button" onClick={() => setStep("survey")}
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                transition={{ delay: 0.62 }}
                className="mt-7 w-full rounded-full bg-[#12c77f] py-4 text-sm font-semibold text-white shadow-[0_8px_28px_rgba(18,199,127,0.35)] transition-all hover:bg-[#0fae6f]">
                Start survey →
              </motion.button>
              <motion.button type="button" onClick={finish}
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                transition={{ delay: 0.7 }}
                className="mt-3 w-full py-2 text-xs text-[#648078] transition-colors hover:text-[#2F3E36]">
                Skip for now
              </motion.button>
            </motion.div>
          )}

          {/* ── SURVEY ── */}
          {step === "survey" && question && (
            <motion.div key={`q-${questionIndex}`}
              initial={{ opacity: 0, x: 36 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -36 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              {/* Progress */}
              <div className="mb-5 space-y-1.5">
                <div className="flex justify-between text-xs text-[#648078]">
                  <span>Question {questionIndex + 1} of {QUESTIONS.length}</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#DDF5EA]">
                  <motion.div className="h-full rounded-full bg-[#12c77f]"
                    initial={{ width: `${(questionIndex / QUESTIONS.length) * 100}%` }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.35 }} />
                </div>
              </div>

              {/* Card */}
              <div className="rounded-[1.75rem] border border-[#DDF5EA] bg-white/78 p-5 shadow-[0_12px_40px_rgba(47,62,54,0.07)] backdrop-blur-xl">
                <h2 className="text-[1.05rem] font-semibold leading-7 text-[#163D33]">
                  {question.question}
                </h2>

                <div className="mt-4">
                  {/* Emoji scale */}
                  {question.type === "emoji-scale" && (
                    <div className="flex justify-between gap-1.5">
                      {question.options.map((opt) => (
                        <button key={opt.value} type="button"
                          onClick={() => setAnswer(question.id, opt.value)}
                          className={`flex flex-1 flex-col items-center gap-1.5 rounded-[1rem] border py-3 transition-all ${
                            answers[question.id] === opt.value
                              ? "border-[#12c77f] bg-[#DDF5EA] shadow-[0_4px_14px_rgba(18,199,127,0.2)]"
                              : "border-[#E8F0EC] bg-[#F7FAF8] hover:bg-[#EDF7F1]"
                          }`}>
                          <span className="text-xl">{opt.emoji}</span>
                          <span className="text-[0.58rem] text-[#648078]">{opt.label}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Multiple choice */}
                  {question.type === "multiple-choice" && (
                    <div className="grid grid-cols-2 gap-2.5">
                      {question.options.map((opt) => {
                        const sel = question.multi
                          ? ((answers[question.id] as string[] | undefined) ?? []).includes(opt.value)
                          : answers[question.id] === opt.value
                        return (
                          <button key={opt.value} type="button"
                            onClick={() => question.multi
                              ? toggleMulti(question.id, opt.value)
                              : setAnswer(question.id, opt.value)}
                            className={`rounded-[1rem] border px-3 py-2.5 text-left text-xs transition-all ${
                              sel
                                ? "border-[#12c77f] bg-[#DDF5EA] font-medium text-[#163D33] shadow-[0_4px_12px_rgba(18,199,127,0.15)]"
                                : "border-[#E8F0EC] bg-[#F7FAF8] text-[#648078] hover:bg-[#EDF7F1]"
                            }`}>
                            {sel && <span className="mr-1 text-[#12c77f]">✓ </span>}
                            {opt.label}
                          </button>
                        )
                      })}
                    </div>
                  )}

                  {/* Slider */}
                  {question.type === "slider" && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-center gap-3">
                        <span className="text-2xl">
                          {((answers[question.id] as number) ?? 5) <= 2 ? "😌"
                            : ((answers[question.id] as number) ?? 5) <= 5 ? "😐"
                            : ((answers[question.id] as number) ?? 5) <= 8 ? "😟" : "😰"}
                        </span>
                        <span className="text-3xl font-light tabular-nums text-[#163D33]">
                          {answers[question.id] ?? 5}
                        </span>
                        <span className="text-sm text-[#648078]">/ {question.max}</span>
                      </div>
                      <input type="range" min={question.min} max={question.max}
                        value={(answers[question.id] as number | undefined) ?? 5}
                        onChange={(e) => setAnswer(question.id, Number(e.target.value))}
                        className="w-full cursor-pointer accent-[#12c77f]" />
                      <div className="flex justify-between text-xs text-[#648078]">
                        <span>{question.minLabel}</span>
                        <span>{question.maxLabel}</span>
                      </div>
                    </div>
                  )}

                  {/* Short text */}
                  {question.type === "short-text" && (
                    <textarea
                      value={(answers[question.id] as string | undefined) ?? ""}
                      onChange={(e) => setAnswer(question.id, e.target.value)}
                      placeholder={question.placeholder} rows={3}
                      className="w-full resize-none rounded-[1rem] border border-[#E8F0EC] bg-[#F7FAF8] px-4 py-3 text-sm leading-6 text-[#2F3E36] outline-none transition-all placeholder:text-[#2F3E36]/35 focus:border-[#12c77f] focus:shadow-[0_0_0_3px_rgba(18,199,127,0.12)]"
                    />
                  )}
                </div>
              </div>

              {/* Nav */}
              <div className="mt-4 flex items-center gap-3">
                <button type="button"
                  onClick={() => setQuestionIndex((i) => Math.max(0, i - 1))}
                  disabled={questionIndex === 0}
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-[#DDF5EA] bg-white/70 text-[#648078] transition-colors hover:bg-[#F0FFF7] disabled:opacity-30">
                  ←
                </button>
                <button type="button" onClick={advance} disabled={!canAdvance()}
                  className="flex-1 rounded-full bg-[#12c77f] py-3.5 text-sm font-semibold text-white shadow-[0_6px_20px_rgba(18,199,127,0.30)] transition-all hover:bg-[#0fae6f] disabled:cursor-not-allowed disabled:opacity-40">
                  {questionIndex === QUESTIONS.length - 1 ? "Finish →" : "Next →"}
                </button>
              </div>
            </motion.div>
          )}

          {/* ── DONE ── */}
          {step === "done" && (
            <motion.div key="done"
              initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, ease: "easeOut" }}
              className="flex flex-col items-center text-center"
            >
              {/* 3D growing tree — score animates from seedling up to 88 */}
              <motion.div className="w-full" initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}>
                <GrowingTreeScene />
              </motion.div>

              {/* Text */}
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5, duration: 0.45 }}>
                <h1 className="mt-5 text-2xl font-semibold text-[#163D33]"
                  style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}>
                  Your journey begins
                </h1>
                <p className="mt-2.5 text-sm leading-6 text-[#648078]">
                  Thank you for sharing. Your emotional garden is ready — watch it grow with you.
                </p>
              </motion.div>

              <motion.button type="button" onClick={finish}
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.72 }}
                className="mt-8 w-full rounded-full bg-[#12c77f] py-4 text-sm font-semibold text-white shadow-[0_8px_28px_rgba(18,199,127,0.35)] transition-all hover:bg-[#0fae6f]">
                Start now →
              </motion.button>
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </div>
  )
}
