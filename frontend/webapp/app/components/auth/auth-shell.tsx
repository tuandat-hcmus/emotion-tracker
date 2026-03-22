import { motion } from "framer-motion"
import { Link } from "react-router"

import { EFlowWordmark } from "~/components/branding/eflow-logo"

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.25 },
  transition: {
    duration: 0.8,
    ease: [0.22, 1, 0.36, 1] as const,
  },
}

type AuthShellProps = {
  children: React.ReactNode
  description: string
  eyebrow: string
  helperLink: {
    label: string
    to: string
  }
  highlights: string[]
  title: string
}

export function AuthShell({
  children,
  description,
  eyebrow,
  helperLink,
  highlights,
  title,
}: AuthShellProps) {
  return (
    <main className="relative min-h-svh overflow-hidden bg-[#FDFBF7] text-[#2F3E36]">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[-8rem] top-[-5rem] h-80 w-80 rounded-full bg-[#EAD2AC]/38 blur-3xl" />
        <div className="absolute right-[-8rem] top-14 h-[28rem] w-[28rem] rounded-full bg-[#A8C3D8]/22 blur-3xl" />
        <div className="absolute bottom-[-7rem] left-1/3 h-96 w-96 rounded-full bg-[#7E9F8B]/18 blur-3xl" />
      </div>

      <div className="relative mx-auto flex min-h-svh max-w-7xl items-center justify-center px-4 py-4 sm:px-6 lg:px-8">
        <motion.section
          {...fadeUp}
          className="w-full max-w-lg rounded-[2rem] border border-white/40 bg-white/45 p-6 shadow-sm backdrop-blur-md sm:p-8"
        >
          <div className="flex items-center justify-between gap-4">
            <Link
              to="/"
              className="inline-flex rounded-full border border-white/40 bg-white/55 px-4 py-2 shadow-sm backdrop-blur-md transition-colors hover:bg-white/75"
            >
              <EFlowWordmark className="h-6 w-20 text-[#2F3E36]" />
            </Link>

            <Link
              to={helperLink.to}
              className="rounded-full px-4 py-2 text-sm text-[#2F3E36]/68 transition-colors hover:bg-white/55 hover:text-[#2F3E36]"
            >
              {helperLink.label}
            </Link>
          </div>

          <div className="mt-6">
            <p className="text-xs uppercase tracking-[0.32em] text-[#7E9F8B]">
              {eyebrow}
            </p>
            <h1
              className="mt-3 text-3xl leading-tight text-[#2F3E36] sm:text-4xl"
              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
            >
              {title}
            </h1>
            <p className="mt-3 text-sm leading-6 text-[#2F3E36]/68">
              {description}
            </p>
          </div>

          <div className="mt-5 flex flex-wrap gap-2.5">
            {highlights.map((item) => (
              <span
                key={item}
                className="rounded-full border border-white/40 bg-white/55 px-3 py-1.5 text-xs text-[#2F3E36]/72 shadow-sm backdrop-blur-md"
              >
                {item}
              </span>
            ))}
          </div>

          <div className="mt-6">{children}</div>
        </motion.section>
      </div>
    </main>
  )
}
