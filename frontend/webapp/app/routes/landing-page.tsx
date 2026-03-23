import {
  Leaf02Icon,
  QuoteUpIcon,
  SparklesIcon,
} from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { motion } from "framer-motion"
import { Link } from "react-router"

import { EFlowWordmark } from "~/components/branding/eflow-logo"
import { DeferredSoulTree } from "~/components/home/deferred-soul-tree"
import { Button } from "~/components/ui/button"

const fadeUp = {
  initial: { opacity: 0, y: 28 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.25 },
  transition: {
    duration: 0.85,
    ease: [0.22, 1, 0.36, 1] as const,
  },
}

const flowSteps = [
  {
    eyebrow: "Step 01",
    title: "Write It Down",
    description:
      "Begin with a simple daily check-in. A few honest lines are enough to start.",
    icon: Leaf02Icon,
  },
  {
    eyebrow: "Step 02",
    title: "Receive Reflection",
    description:
      "Receive a calm, supportive response grounded in what you actually shared.",
    icon: SparklesIcon,
  },
  {
    eyebrow: "Step 03",
    title: "Notice Your Patterns",
    description:
      "See your recent history and wrapups take shape over time, with the forest quietly supporting the journey.",
    icon: Leaf02Icon,
  },
]

const ambientNotes = [
  "Private daily journaling",
  "Supportive reflection",
  "A forest that grows with you",
]

const groundingQuotes = [
  "You don't always have to bloom. Be the pine in the storm.",
  "A softer pace is still a way forward.",
  "Let the feeling move through. It does not need to stay forever.",
  "You are allowed to witness yourself with kindness.",
]

export default function LandingPage() {
  return (
    <main className="relative overflow-hidden bg-[#FDFBF7] text-[#2F3E36]">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute left-[-8rem] top-[-5rem] h-80 w-80 rounded-full bg-[#EAD2AC]/40 blur-3xl" />
        <div className="absolute right-[-7rem] top-20 h-[28rem] w-[28rem] rounded-full bg-[#A8C3D8]/26 blur-3xl" />
        <div className="absolute bottom-[-7rem] left-1/3 h-96 w-96 rounded-full bg-[#7E9F8B]/18 blur-3xl" />
      </div>

      <header className="fixed inset-x-0 top-0 z-50 px-4 pt-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl rounded-full border border-white/40 bg-white/50 px-4 py-3 shadow-sm backdrop-blur-lg sm:px-6">
          <div className="flex items-center justify-between gap-4">
            <Link to="/" className="inline-flex rounded-full bg-white/70 px-4 py-2">
              <EFlowWordmark className="h-7 w-24 text-[#2F3E36]" />
            </Link>

            <nav className="flex items-center gap-2 sm:gap-3">
              <Link
                to="/login"
                className="rounded-full px-4 py-2 text-sm text-[#2F3E36]/72 transition-colors hover:bg-white/55 hover:text-[#2F3E36]"
              >
                Sign In
              </Link>
              <Button
                asChild
                className="h-11 rounded-full border-0 bg-[#7E9F8B] px-5 text-sm text-white hover:bg-[#5C7D69]"
              >
                <Link to="/register">Start journaling</Link>
              </Button>
            </nav>
          </div>
        </div>
      </header>

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <section className="flex min-h-svh items-center pt-28 pb-16 sm:pb-20">
          <div className="grid w-full items-center gap-10 lg:grid-cols-2 lg:gap-14">
            <motion.div {...fadeUp} className="max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full bg-white/40 px-4 py-2 text-sm text-[#2F3E36] shadow-sm backdrop-blur-md">
                <span>{"\u2728"}</span>
                <span>A calmer way to check in</span>
              </div>

              <h1
                className="mt-6 text-5xl leading-[0.96] font-semibold tracking-tight text-[#2F3E36] sm:text-6xl lg:text-7xl"
                style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
              >
                Write what is true.
                <br />
                Let it settle.
              </h1>

              <p className="mt-6 max-w-xl text-base leading-8 text-[#2F3E36]/72 sm:text-lg">
                A daily journaling companion for emotional clarity, supportive
                reflection, and a gentler understanding of your patterns over
                time.
              </p>

              <div className="mt-8 flex flex-col gap-4 sm:flex-row">
                <Button
                  asChild
                  size="lg"
                  className="h-12 rounded-full border-0 bg-[#7E9F8B] px-6 text-sm text-white hover:bg-[#5C7D69]"
                >
                  <Link to="/register">
                    Start journaling
                  </Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="h-12 rounded-full border-white/40 bg-white/40 px-6 text-sm text-[#2F3E36] hover:bg-white/60"
                >
                  <a href="#how-it-works">See how it works</a>
                </Button>
              </div>

              <div className="mt-8 flex flex-wrap gap-3">
                {ambientNotes.map((note) => (
                  <span
                    key={note}
                    className="rounded-full border border-white/40 bg-white/40 px-4 py-2 text-sm text-[#2F3E36]/72 shadow-sm backdrop-blur-md"
                  >
                    {note}
                  </span>
                ))}
              </div>
            </motion.div>

            <motion.div
              {...fadeUp}
              transition={{ ...fadeUp.transition, delay: 0.08 }}
              className="relative h-[420px] w-full lg:h-[600px]"
            >
              <div className="absolute inset-0 rounded-[2rem] bg-[radial-gradient(circle_at_top,rgba(168,195,216,0.24),rgba(253,251,247,0.76),rgba(126,159,139,0.14))]" />
              <div className="absolute inset-0 rounded-[2rem] border border-white/40 bg-white/40 shadow-sm backdrop-blur-md" />

              <div className="absolute inset-x-4 inset-y-4 rounded-[1.75rem] bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.34),rgba(253,251,247,0.1),rgba(126,159,139,0.08))] sm:inset-6" />
              <div className="absolute inset-x-4 bottom-4 top-4 rounded-[1.75rem] border border-white/30 bg-[#FDFBF7]/45 p-2 sm:inset-6 sm:p-4">
                <DeferredSoulTree
                  emotion="neutral"
                  score={78}
                  animateTransition={false}
                  deferMs={80}
                  className="h-full rounded-[1.5rem] border-0 bg-transparent shadow-none"
                />
              </div>
            </motion.div>
          </div>
        </section>

        <section id="how-it-works" className="py-24">
          <motion.div {...fadeUp} className="mx-auto max-w-3xl text-center">
            <p className="text-xs uppercase tracking-[0.32em] text-[#7E9F8B]">
              How it works
            </p>
            <h2
              className="mt-4 text-4xl leading-tight text-[#2F3E36] sm:text-5xl"
              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
            >
              A steadier way to understand yourself.
            </h2>
            <p className="mt-5 text-base leading-8 text-[#2F3E36]/68">
              eFlow helps you check in through writing, receive reflective
              guidance, and build a steadier picture of your inner landscape
              over time.
            </p>
          </motion.div>

          <div className="mt-12 grid gap-5 lg:grid-cols-3">
            {flowSteps.map((step, index) => (
              <motion.article
                key={step.title}
                {...fadeUp}
                transition={{
                  ...fadeUp.transition,
                  delay: 0.08 + index * 0.08,
                }}
                className="rounded-3xl border border-white/40 bg-white/40 p-6 shadow-sm backdrop-blur-md"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#7E9F8B]/12 text-[#7E9F8B]">
                  <HugeiconsIcon icon={step.icon} size={20} strokeWidth={1.8} />
                </div>
                <p className="mt-6 text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                  {step.eyebrow}
                </p>
                <h3 className="mt-3 text-2xl font-semibold text-[#2F3E36]">
                  {step.title}
                </h3>
                <p className="mt-4 text-sm leading-7 text-[#2F3E36]/68">
                  {step.description}
                </p>
              </motion.article>
            ))}
          </div>
        </section>

        <section className="py-6">
          <motion.div
            {...fadeUp}
            className="rounded-[2rem] bg-[#A8C3D8]/10 px-6 py-10 sm:px-8"
          >
            <div className="mx-auto max-w-3xl text-center">
              <p className="text-xs uppercase tracking-[0.32em] text-[#7E9F8B]">
                Daily grounding quotes
              </p>
              <h2
                className="mt-4 text-3xl text-[#2F3E36] sm:text-4xl"
                style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
              >
                Small lines to help your nervous system exhale.
              </h2>
            </div>

            <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {groundingQuotes.map((quote, index) => (
                <motion.article
                  key={quote}
                  {...fadeUp}
                  transition={{
                    ...fadeUp.transition,
                    delay: 0.06 + index * 0.06,
                  }}
                  className="rounded-3xl border border-white/40 bg-white/50 p-5 shadow-sm backdrop-blur-md"
                >
                  <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#FDFBF7] text-[#7E9F8B]">
                    <HugeiconsIcon
                      icon={QuoteUpIcon}
                      size={18}
                      strokeWidth={1.8}
                    />
                  </span>
                  <p className="mt-5 text-sm leading-7 text-[#2F3E36]/74">
                    {quote}
                  </p>
                </motion.article>
              ))}
            </div>
          </motion.div>
        </section>

        <section className="py-24">
          <motion.div
            {...fadeUp}
            className="mx-auto max-w-4xl rounded-[2rem] border border-white/40 bg-white/40 px-6 py-12 text-center shadow-sm backdrop-blur-md sm:px-10"
          >
            <EFlowWordmark className="mx-auto h-9 w-28 text-[#2F3E36]" />
            <h2
              className="mt-6 text-4xl leading-tight text-[#2F3E36] sm:text-5xl"
              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
            >
              Ready to begin your first check-in?
            </h2>
            <p className="mt-5 text-base leading-8 text-[#2F3E36]/68">
              Begin with one honest check-in and let the rest unfold at a human pace.
            </p>
            <Button
              asChild
              size="lg"
              className="mt-8 h-14 rounded-full border-0 bg-[#7E9F8B] px-8 text-sm text-white shadow-[0_18px_42px_rgba(126,159,139,0.24)] hover:bg-[#5C7D69]"
            >
              <Link to="/register">Start Your Journal</Link>
            </Button>
          </motion.div>
        </section>

        <footer className="pb-10">
          <div className="flex flex-col gap-5 rounded-[2rem] border border-white/40 bg-white/40 px-5 py-6 shadow-sm backdrop-blur-md sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <div className="flex items-center gap-3">
              <EFlowWordmark className="h-8 w-24 text-[#2F3E36]" />
              <p className="text-sm text-[#2F3E36]/58">
                Copyright 2026 eFlow. All rights reserved.
              </p>
            </div>

            <div className="flex flex-wrap gap-4 text-sm text-[#2F3E36]/68">
              <a href="#" className="transition-colors hover:text-[#2F3E36]">
                Privacy Policy
              </a>
              <a href="#" className="transition-colors hover:text-[#2F3E36]">
                Terms of Service
              </a>
            </div>
          </div>
        </footer>
      </div>
    </main>
  )
}
