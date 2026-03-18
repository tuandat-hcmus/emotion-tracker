import { Link } from "react-router"

import { Button } from "~/components/ui/button"

const ritualSteps = [
  {
    eyebrow: "Step 01",
    title: "Speak into your forest",
    description:
      "Record a voice journal the moment a feeling arrives, without needing to translate it into perfect words first.",
  },
  {
    eyebrow: "Step 02",
    title: "Let the forest listen",
    description:
      "Soul Forest turns your voice into a transcript, detects emotional patterns, and reflects them back with care.",
  },
  {
    eyebrow: "Step 03",
    title: "Watch your inner landscape grow",
    description:
      "Each entry nourishes your Soul Tree, building a living picture of your moods, stressors, and calm seasons over time.",
  },
]

const highlights = [
  {
    value: "42 sec",
    label: "Average check-in to capture a moment before it slips away.",
  },
  {
    value: "Daily",
    label: "Mood snapshots that help you notice patterns with more gentleness.",
  },
  {
    value: "Private",
    label: "A reflective space designed to feel safe, grounded, and personal.",
  },
]

const emotionalSignals = [
  { label: "Calm", color: "bg-[#81B29A]" },
  { label: "Tender", color: "bg-[#EAD2AC]" },
  { label: "Stressed", color: "bg-[#E07A5F]" },
  { label: "Grounded", color: "bg-[#7E9F8B]" },
]

export default function LandingPage() {
  return (
    <main className="relative min-h-svh overflow-hidden bg-[#FDFBF7] text-[#2F3E36]">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[-8rem] top-[-5rem] h-72 w-72 rounded-full bg-[#A8C3D8]/35 blur-3xl" />
        <div className="absolute right-[-6rem] top-24 h-80 w-80 rounded-full bg-[#7E9F8B]/20 blur-3xl" />
        <div className="absolute bottom-[-5rem] left-1/3 h-72 w-72 rounded-full bg-[#EAD2AC]/35 blur-3xl" />
      </div>

      <div className="relative mx-auto flex max-w-7xl flex-col gap-8 px-4 py-5 sm:px-6 lg:px-8">
        <header className="rounded-[2rem] border border-white/40 bg-white/30 px-5 py-4 shadow-sm backdrop-blur-md sm:px-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#7E9F8B] text-sm font-semibold text-white">
                SF
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.32em] text-[#7E9F8B]">
                  Soul Forest
                </p>
                <p className="text-sm text-[#2F3E36]/70">
                  Voice journaling for your inner weather
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <a
                href="#how-it-works"
                className="rounded-full px-4 py-2 text-sm text-[#2F3E36]/75 transition-colors hover:bg-white/40 hover:text-[#2F3E36]"
              >
                How it works
              </a>
              <Button
                asChild
                size="lg"
                className="rounded-full border-0 bg-[#7E9F8B] px-5 text-white hover:bg-[#5C7D69]"
              >
                <Link to="/app/home">Voice Up Now</Link>
              </Button>
            </div>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="rounded-[2.25rem] border border-white/40 bg-white/30 p-8 shadow-sm backdrop-blur-md sm:p-10">
            <div className="inline-flex rounded-full bg-[#7E9F8B]/12 px-4 py-2 text-xs uppercase tracking-[0.3em] text-[#7E9F8B]">
              Therapeutic voice reflection
            </div>

            <div className="mt-6 max-w-3xl space-y-6">
              <h1 className="text-5xl leading-[1.02] font-semibold tracking-tight sm:text-6xl lg:text-7xl">
                A gentle forest for the feelings you have not named yet.
              </h1>
              <p className="max-w-2xl text-base leading-8 text-[#2F3E36]/75 sm:text-lg">
                Soul Forest helps you exhale into your phone, hear yourself more
                clearly, and return to calm with voice journaling that feels
                soft, natural, and deeply personal.
              </p>
            </div>

            <div className="mt-8 flex flex-col gap-4 sm:flex-row">
              <Button
                asChild
                size="lg"
                className="h-12 rounded-full border-0 bg-[#7E9F8B] px-6 text-sm text-white hover:bg-[#5C7D69]"
              >
                <Link to="/app/home">Enter your Soul Forest</Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="h-12 rounded-full border-white/50 bg-white/35 px-6 text-sm text-[#2F3E36] hover:bg-white/55"
              >
                <Link to="/app/journal">Explore the journal</Link>
              </Button>
            </div>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {highlights.map((item) => (
                <div
                  key={item.value}
                  className="rounded-[1.75rem] border border-white/40 bg-white/25 p-4"
                >
                  <p className="text-2xl font-semibold text-[#2F3E36]">
                    {item.value}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-[#2F3E36]/70">
                    {item.label}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <div className="overflow-hidden rounded-[2.25rem] border border-white/40 bg-gradient-to-br from-[#A8C3D8]/35 via-white/20 to-[#7E9F8B]/30 p-6 shadow-sm backdrop-blur-md sm:p-7">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-[#7E9F8B]">
                    Today&apos;s canopy
                  </p>
                  <h2 className="mt-2 text-2xl font-semibold">
                    Your voice becomes a living mood map.
                  </h2>
                </div>
                <div className="rounded-full bg-white/45 px-4 py-2 text-sm text-[#2F3E36]/75">
                  Live preview
                </div>
              </div>

              <div className="mt-8 rounded-[2rem] border border-white/40 bg-white/30 p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm text-[#2F3E36]/60">Evening check-in</p>
                    <p className="mt-2 max-w-sm text-base leading-7 text-[#2F3E36]/80">
                      &quot;I felt overwhelmed this afternoon, but after my walk I
                      can finally breathe again.&quot;
                    </p>
                  </div>
                  <div className="h-16 w-16 rounded-full bg-[#7E9F8B]/20" />
                </div>

                <div className="mt-6 flex flex-wrap gap-3">
                  {emotionalSignals.map((signal) => (
                    <span
                      key={signal.label}
                      className="inline-flex items-center gap-2 rounded-full bg-white/40 px-3 py-2 text-sm"
                    >
                      <span
                        className={`h-2.5 w-2.5 rounded-full ${signal.color}`}
                      />
                      {signal.label}
                    </span>
                  ))}
                </div>

                <div className="mt-6 grid grid-cols-7 gap-2">
                  {Array.from({ length: 21 }).map((_, index) => {
                    const palette = [
                      "bg-[#81B29A]/90",
                      "bg-[#A8C3D8]/85",
                      "bg-[#EAD2AC]/90",
                      "bg-[#E07A5F]/70",
                    ]

                    return (
                      <div
                        key={index}
                        className={`aspect-square rounded-full ${palette[index % palette.length]}`}
                      />
                    )
                  })}
                </div>
              </div>
            </div>

            <div className="rounded-[2.25rem] border border-white/40 bg-white/30 p-6 shadow-sm backdrop-blur-md sm:p-7">
              <p className="text-xs uppercase tracking-[0.3em] text-[#7E9F8B]">
                A quieter way to begin
              </p>
              <blockquote className="mt-3 text-xl leading-9 text-[#2F3E36]/85">
                &quot;When your mind feels crowded, start with your breath and a
                sentence. The forest will hold the rest.&quot;
              </blockquote>
              <p className="mt-4 text-sm text-[#2F3E36]/60">
                AI-guided grounding after each reflection
              </p>
            </div>
          </div>
        </section>

        <section
          id="how-it-works"
          className="rounded-[2.5rem] border border-white/40 bg-white/25 p-8 shadow-sm backdrop-blur-md sm:p-10"
        >
          <div className="max-w-2xl">
            <p className="text-xs uppercase tracking-[0.3em] text-[#7E9F8B]">
              How it works
            </p>
            <h2 className="mt-3 text-3xl font-semibold sm:text-4xl">
              Small voice rituals that grow into self-understanding.
            </h2>
            <p className="mt-4 text-base leading-8 text-[#2F3E36]/75">
              Soul Forest is designed for moments when typing feels too rigid
              and silence feels too heavy. You speak, the platform listens, and
              your emotional landscape slowly comes into view.
            </p>
          </div>

          <div className="mt-10 grid gap-4 lg:grid-cols-3">
            {ritualSteps.map((step) => (
              <article
                key={step.title}
                className="rounded-[2rem] border border-white/40 bg-white/30 p-6 shadow-sm backdrop-blur-md"
              >
                <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                  {step.eyebrow}
                </p>
                <h3 className="mt-4 text-2xl font-semibold">{step.title}</h3>
                <p className="mt-4 text-sm leading-7 text-[#2F3E36]/70">
                  {step.description}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-[2.25rem] border border-white/40 bg-white/30 p-8 shadow-sm backdrop-blur-md">
            <p className="text-xs uppercase tracking-[0.3em] text-[#7E9F8B]">
              Built for emotional clarity
            </p>
            <h2 className="mt-3 text-3xl font-semibold">
              More than notes. More than mood tracking.
            </h2>
            <div className="mt-6 space-y-4 text-sm leading-7 text-[#2F3E36]/75">
              <p>
                Voice-first journaling removes the pressure to sound polished.
                Your entries stay human, messy, and real.
              </p>
              <p>
                Gentle emotional analysis gives shape to what you felt, while
                your evolving Soul Tree creates a visual story of resilience.
              </p>
              <p>
                Daily reflections, timelines, and wrap-ups help you notice where
                you soften, where you strain, and what helps you return.
              </p>
            </div>
          </div>

          <div className="rounded-[2.25rem] border border-white/40 bg-gradient-to-r from-[#A8C3D8]/40 to-[#7E9F8B]/35 p-8 shadow-sm backdrop-blur-md">
            <div className="max-w-2xl">
              <p className="text-xs uppercase tracking-[0.3em] text-[#2F3E36]/65">
                Ready to begin
              </p>
              <h2 className="mt-3 text-3xl font-semibold sm:text-4xl">
                Start with one honest breath and let the forest grow around it.
              </h2>
              <p className="mt-4 text-base leading-8 text-[#2F3E36]/75">
                Open your dashboard, press record, and give today a place to
                land.
              </p>
            </div>

            <div className="mt-8 flex flex-col gap-4 sm:flex-row">
              <Button
                asChild
                size="lg"
                className="h-12 rounded-full border-0 bg-[#7E9F8B] px-6 text-white hover:bg-[#5C7D69]"
              >
                <Link to="/app/home">Voice Up Now</Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="h-12 rounded-full border-white/50 bg-white/35 px-6 text-[#2F3E36] hover:bg-white/55"
              >
                <Link to="/app/journal">See the journal view</Link>
              </Button>
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
