import { motion } from "framer-motion"
import { useEffect, useState } from "react"
import SoulTree from "~/components/home/soul-tree"

function StaticSoulTreeFallback() {
  return (
    <div className="relative flex h-full min-h-[15rem] w-full items-end justify-center overflow-hidden">
      <div className="absolute bottom-6 h-16 w-40 rounded-full bg-[#7E9F8B]/18 blur-xl" />
      <div className="absolute bottom-16 h-28 w-8 rounded-full bg-[#7D5A50]/78" />
      <div className="absolute bottom-[7.5rem] left-1/2 h-20 w-20 -translate-x-[4.5rem] rounded-full bg-[#81B29A]/82 shadow-sm" />
      <div className="absolute bottom-36 left-1/2 h-24 w-24 -translate-x-1/2 rounded-full bg-[#7E9F8B]/86 shadow-sm" />
      <div className="absolute bottom-28 left-1/2 h-[4.5rem] w-[4.5rem] translate-x-[3.5rem] rounded-full bg-[#A8C3D8]/78 shadow-sm" />
    </div>
  )
}

export function SoulTreeStage() {
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="relative overflow-hidden rounded-[2rem] border border-white/40 bg-[radial-gradient(circle_at_top,rgba(168,195,216,0.28),rgba(255,255,255,0.12),rgba(126,159,139,0.22))] p-5 sm:p-6"
    >
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute top-8 left-8 h-24 w-24 rounded-full bg-[#A8C3D8]/20 blur-2xl" />
        <div className="absolute right-8 bottom-8 h-32 w-32 rounded-full bg-[#81B29A]/18 blur-3xl" />
      </div>

      <div className="relative flex min-h-[21rem] flex-col">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs tracking-[0.3em] text-[#7E9F8B] uppercase">
              Soul Tree stage
            </p>
            <h3 className="mt-2 text-xl font-semibold sm:text-2xl">
              A lighter, calmer tree preview
            </h3>
          </div>
          <div className="rounded-full bg-white/35 px-4 py-2 text-sm text-[#2F3E36]/72">
            Optimized canvas
          </div>
        </div>

        <div className="relative mt-6 flex min-h-[15rem] flex-1 items-center justify-center overflow-hidden rounded-[1.75rem] border border-white/35 bg-white/[0.18]">
          <div className="pointer-events-none absolute inset-x-6 top-4 h-14 rounded-full bg-white/25 blur-2xl" />

          {isMounted ? (
            <SoulTree
              className="h-[18rem] border-0 bg-transparent shadow-none"
              emotion="calm"
            />
          ) : (
            <StaticSoulTreeFallback />
          )}

          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-[#FDFBF7] via-[#FDFBF7]/35 to-transparent" />
        </div>
      </div>
    </motion.div>
  )
}
