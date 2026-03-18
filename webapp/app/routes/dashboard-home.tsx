import { motion } from "framer-motion"
import { useState } from "react"

import { MicIcon } from "~/components/icons/mic-icon"
import SoulTree, { type EmotionState } from "~/components/home/soul-tree"
import { VoiceInputModal } from "~/components/home/voice-input-modal"
import { Button } from "~/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { useSoulForest } from "~/context/soul-forest-context"

const weeklySignals = [
  { label: "Calm", count: 9, color: "bg-[#81B29A]" },
  { label: "Reflective", count: 6, color: "bg-[#A8C3D8]" },
  { label: "Stressed", count: 3, color: "bg-[#E07A5F]" },
  { label: "Hopeful", count: 5, color: "bg-[#7E9F8B]" },
]

export default function DashboardHome() {
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false)
  const { currentMood, intensity, timeline, lastQuote } = useSoulForest()
  const [treePreviewEmotion, setTreePreviewEmotion] =
    useState<EmotionState | null>(null)

  const liveTreeEmotion: EmotionState =
    currentMood === "Calm"
      ? "calm"
      : currentMood === "Reflective"
        ? "reflective"
        : currentMood === "Hopeful"
          ? "hopeful"
          : "stressed"

  const activeTreeEmotion = treePreviewEmotion ?? liveTreeEmotion

  const treePresets: Array<{ label: string; emotion: EmotionState }> = [
    { label: "Calm", emotion: "calm" },
    { label: "Reflective", emotion: "reflective" },
    { label: "Stressed", emotion: "stressed" },
    { label: "Hopeful", emotion: "hopeful" },
  ]

  return (
    <>
      <motion.section
        initial={{ opacity: 0, y: 22 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: "easeOut" }}
        className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.75fr)]"
      >
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05, duration: 0.5 }}
          >
            <Card className="overflow-hidden border-white/50 bg-gradient-to-br from-[#A8C3D8]/28 via-white/22 to-[#7E9F8B]/20">
              <CardHeader className="pb-3">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-[#7E9F8B]">
                      Today&apos;s grove
                    </p>
                    <CardTitle className="mt-2 text-2xl sm:text-3xl">
                      Your inner weather has a place to land.
                    </CardTitle>
                    <CardDescription className="mt-2 max-w-xl text-sm leading-6">
                      Record a reflection and watch the tree respond without
                      needing to scroll before you even see it.
                    </CardDescription>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <motion.div whileHover={{ y: -1 }} whileTap={{ scale: 0.98 }}>
                      <Button
                        onClick={() => setIsVoiceModalOpen(true)}
                        size="lg"
                        className="h-11 rounded-full border-0 bg-[#7E9F8B] px-5 text-white hover:bg-[#5C7D69]"
                      >
                        <MicIcon className="mr-2 h-4 w-4" />
                        Voice input now
                      </Button>
                    </motion.div>
                    <motion.div
                      animate={{ y: [0, -2, 0] }}
                      transition={{
                        duration: 5,
                        repeat: Infinity,
                        ease: "easeInOut",
                      }}
                      className="rounded-full bg-white/35 px-4 py-3 text-sm text-[#2F3E36]/76"
                    >
                      Current mood: {currentMood}
                    </motion.div>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="pb-5">
                <div className="rounded-[2rem] border border-white/40 bg-[radial-gradient(circle_at_top,rgba(168,195,216,0.28),rgba(255,255,255,0.12),rgba(126,159,139,0.22))] p-4 sm:p-5">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.3em] text-[#7E9F8B]">
                        Soul Tree stage
                      </p>
                      <h3 className="mt-2 text-lg font-semibold sm:text-xl">
                        Your forest is reflecting today&apos;s emotional tone
                      </h3>
                      <p className="mt-2 text-sm leading-6 text-[#2F3E36]/72">
                        Switch states below or sync to the live detected mood.
                      </p>
                    </div>
                    <div className="rounded-full bg-white/35 px-4 py-2 text-sm text-[#2F3E36]/72">
                      {treePreviewEmotion ? "Manual preview" : "Synced to mood"}
                    </div>
                  </div>

                  <div className="mt-5 flex flex-wrap gap-2">
                    {treePresets.map((preset) => (
                      <button
                        key={preset.emotion}
                        type="button"
                        onClick={() => setTreePreviewEmotion(preset.emotion)}
                        className={`rounded-full px-4 py-2 text-sm transition-colors ${
                          activeTreeEmotion === preset.emotion
                            ? "bg-[#7E9F8B] text-white"
                            : "bg-white/35 text-[#2F3E36] hover:bg-white/55"
                        }`}
                      >
                        {preset.label}
                      </button>
                    ))}
                    <button
                      type="button"
                      onClick={() => setTreePreviewEmotion(null)}
                      className={`rounded-full px-4 py-2 text-sm transition-colors ${
                        treePreviewEmotion === null
                          ? "bg-[#2F3E36] text-white"
                          : "bg-white/35 text-[#2F3E36] hover:bg-white/55"
                      }`}
                    >
                      Sync with mood
                    </button>
                  </div>

                  <div className="mt-4 overflow-hidden rounded-[1.75rem] border border-white/35 bg-white/[0.18]">
                    <SoulTree
                      emotion={activeTreeEmotion}
                      className="h-[17.5rem] border-0 bg-transparent shadow-none sm:h-[18.5rem]"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <div className="grid gap-4 lg:grid-cols-3">
            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.12, duration: 0.45 }}
            >
              <Card className="bg-white/[0.28]">
                <CardHeader className="pb-2">
                  <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                    Emotional balance
                  </p>
                  <CardTitle className="text-2xl">{intensity}%</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-6 text-[#2F3E36]/72">
                    Your latest reflection carries a{" "}
                    {currentMood.toLowerCase()} tone with moderate intensity.
                  </p>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.18, duration: 0.45 }}
            >
              <Card className="bg-white/[0.28]">
                <CardHeader className="pb-2">
                  <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                    Weekly seeds
                  </p>
                  <CardTitle className="text-2xl">{timeline.length + 8}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-6 text-[#2F3E36]/72">
                    Voice moments already planted across your recent emotional
                    timeline.
                  </p>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.24, duration: 0.45 }}
            >
              <Card className="bg-white/[0.28]">
                <CardHeader className="pb-2">
                  <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                    Grounding note
                  </p>
                  <CardTitle className="text-2xl">Keep blooming</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-6 text-[#2F3E36]/72">
                    {lastQuote}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>

        <div className="space-y-6 xl:sticky xl:top-0 xl:self-start">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.14, duration: 0.5 }}
          >
            <Card className="bg-white/[0.28]">
              <CardHeader>
                <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                  Daily mood timeline
                </p>
                <CardTitle className="text-2xl">Recent canopy shifts</CardTitle>
                <CardDescription>
                  A soft read on the emotional rhythm across your latest
                  entries.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {timeline.map((entry, index) => (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.18 + index * 0.04, duration: 0.34 }}
                    className="rounded-[1.5rem] border border-white/35 bg-white/[0.24] p-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <span
                          className="mt-1 h-3.5 w-3.5 rounded-full"
                          style={{ backgroundColor: entry.moodColor }}
                        />
                        <div>
                          <p className="text-sm font-medium text-[#2F3E36]">
                            {entry.day} - {entry.time}
                          </p>
                          <p className="mt-1 text-sm leading-6 text-[#2F3E36]/72">
                            {entry.summary}
                          </p>
                        </div>
                      </div>
                      <span className="rounded-full bg-white/40 px-3 py-1 text-xs">
                        {entry.mood}
                      </span>
                    </div>
                    <p className="mt-4 text-sm italic text-[#2F3E36]/62">
                      {entry.quote}
                    </p>
                  </motion.div>
                ))}
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.22, duration: 0.5 }}
          >
            <Card className="bg-gradient-to-br from-[#A8C3D8]/22 to-[#7E9F8B]/18">
              <CardHeader>
                <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                  Mood weather
                </p>
                <CardTitle className="text-2xl">This week in colors</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {weeklySignals.map((signal, index) => (
                  <div key={signal.label} className="space-y-2">
                    <div className="flex items-center justify-between gap-3 text-sm">
                      <span>{signal.label}</span>
                      <span>{signal.count} entries</span>
                    </div>
                    <div className="h-3 rounded-full bg-white/35">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${signal.count * 9}%` }}
                        transition={{
                          delay: 0.28 + index * 0.06,
                          duration: 0.8,
                          ease: "easeOut",
                        }}
                        className={`h-3 rounded-full ${signal.color}`}
                      />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </motion.section>

      <VoiceInputModal
        open={isVoiceModalOpen}
        onOpenChange={setIsVoiceModalOpen}
      />
    </>
  )
}
