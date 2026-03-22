import { AnimatePresence, motion } from "framer-motion"
import { useMemo, useState, useTransition } from "react"

import { MicIcon } from "~/components/icons/mic-icon"
import { Button } from "~/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "~/components/ui/dialog"
import { Slider } from "~/components/ui/slider"
import { useSoulForest } from "~/context/soul-forest-context"
import { type SoulEmotion } from "~/lib/emotions"

type VoiceInputModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const starterPrompts = [
  "What felt heavier than expected today?",
  "What helped you come back to yourself?",
  "What do you wish someone had asked you today?",
]

export function VoiceInputModal({
  open,
  onOpenChange,
}: VoiceInputModalProps) {
  const { addVoiceReflection } = useSoulForest()
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState(
    "Today felt full. I kept carrying tension in my shoulders, but the evening finally felt softer."
  )
  const [intensity, setIntensity] = useState([46])
  const [selectedPrompt, setSelectedPrompt] = useState(starterPrompts[0])
  const [isPending, startTransition] = useTransition()

  const liveCaption = useMemo(() => {
    if (!isRecording) {
      return "Recording is paused. Press the circle to begin your voice ritual."
    }

    return "Listening gently... your words are settling here in real time."
  }, [isRecording])

  async function handleAnalyzeEmotion() {
    const mockDelay = () =>
      new Promise<void>((resolve) => {
        window.setTimeout(resolve, 650)
      })

    const lowered = transcript.toLowerCase()
    let mood: SoulEmotion = "neutral"

    if (lowered.includes("overwhelmed")) {
      mood = "anxiety"
    } else if (
      lowered.includes("angry") ||
      lowered.includes("furious") ||
      lowered.includes("resent")
    ) {
      mood = "anger"
    } else if (
      lowered.includes("anxious") ||
      lowered.includes("panic") ||
      lowered.includes("tension")
    ) {
      mood = "anxiety"
    } else if (
      lowered.includes("sad") ||
      lowered.includes("empty") ||
      lowered.includes("cry")
    ) {
      mood = "sadness"
    } else if (
      lowered.includes("disgusted") ||
      lowered.includes("gross") ||
      lowered.includes("repulsed")
    ) {
      mood = "disgust"
    } else if (
      lowered.includes("surprised") ||
      lowered.includes("unexpected") ||
      lowered.includes("shocked")
    ) {
      mood = "surprise"
    } else if (
      lowered.includes("joy") ||
      lowered.includes("lighter") ||
      lowered.includes("grateful") ||
      lowered.includes("thankful") ||
      lowered.includes("appreciate") ||
      lowered.includes("happy")
    ) {
      mood = "joy"
    } else if (
      lowered.includes("breathe") ||
      lowered.includes("calm") ||
      lowered.includes("soft") ||
      lowered.includes("steady")
    ) {
      mood = "neutral"
    }

    const quotes = {
      joy: "Joy can be quiet and still completely real. Let it spread through the canopy.",
      surprise:
        "Surprise can wake the tree up. Let that spark become curiosity instead of noise.",
      neutral:
        "Neutral is not empty. It can be a place where your body starts to reset.",
      sadness:
        "Sadness softens when it is given somewhere safe to land.",
      disgust:
        "Disgust often protects your boundaries. Listening to it can clarify what no longer fits.",
      anxiety:
        "Your system is trying to protect you. Slow breaths can help it unclench.",
      anger:
        "Anger is often a boundary speaking. Listening to it gently can reveal what matters.",
    }

    await mockDelay()

    addVoiceReflection({
      mood,
      intensity: intensity[0] ?? 46,
      transcript,
      quote: quotes[mood],
      recordedAt: new Date().toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
      }),
    })

    setIsRecording(false)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90svh] w-[min(96vw,64rem)] overflow-hidden border-white/45 bg-[linear-gradient(180deg,rgba(255,255,255,0.38),rgba(255,255,255,0.22))] p-0">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="flex max-h-[90svh] flex-col"
        >
          <DialogHeader className="p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-[#7E9F8B]">
                  Voice check-in
                </p>
                <DialogTitle className="mt-2 text-3xl">
                  Let the forest hear what today felt like
                </DialogTitle>
                <DialogDescription className="mt-3 max-w-2xl text-[#2F3E36]/72">
                  This is a frontend placeholder for live speech-to-text
                  capture. `handleAnalyzeEmotion()` currently mocks the LLM
                  analysis step and writes the result back into the dashboard
                  timeline.
                </DialogDescription>
              </div>

              <DialogClose asChild>
                <Button
                  variant="ghost"
                  className="rounded-full bg-white/30 px-3 text-[#2F3E36] hover:bg-white/55"
                >
                  Close
                </Button>
              </DialogClose>
            </div>
          </DialogHeader>

          <div className="min-h-0 flex-1 overflow-y-auto px-6 pb-6 pt-2">
            <div className="grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
              <motion.div
                initial={{ opacity: 0, x: -18 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.08, duration: 0.45 }}
                className="rounded-[1.75rem] border border-white/40 bg-white/[0.28] p-5"
              >
                <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                  Recording
                </p>

                <div className="mt-6 flex justify-center">
                  <motion.button
                    type="button"
                    onClick={() => setIsRecording((value) => !value)}
                    animate={
                      isRecording
                        ? {
                            scale: [1, 1.06, 1],
                            boxShadow: [
                              "0 0 0 0 rgba(224,122,95,0.26)",
                              "0 0 0 18px rgba(224,122,95,0)",
                              "0 0 0 0 rgba(224,122,95,0)",
                            ],
                          }
                        : { scale: 1, boxShadow: "0 8px 24px rgba(47,62,54,0.08)" }
                    }
                    transition={{
                      duration: 1.8,
                      repeat: isRecording ? Infinity : 0,
                      ease: "easeInOut",
                    }}
                    className="flex h-32 w-32 flex-col items-center justify-center gap-2 rounded-full border border-white/60 bg-[radial-gradient(circle_at_top,rgba(224,122,95,0.55),rgba(126,159,139,0.88))] text-center text-white shadow-sm sm:h-36 sm:w-36"
                  >
                    <MicIcon className="h-5 w-5" />
                    <span className="max-w-24 text-sm font-medium leading-5">
                      {isRecording ? "Stop ritual" : "Start speaking"}
                    </span>
                  </motion.button>
                </div>

                <AnimatePresence mode="wait">
                  <motion.p
                    key={liveCaption}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.22 }}
                    className="mt-5 text-sm leading-6 text-[#2F3E36]/72"
                  >
                    {liveCaption}
                  </motion.p>
                </AnimatePresence>

                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.16, duration: 0.35 }}
                  className="mt-6 rounded-[1.5rem] bg-white/30 p-4"
                >
                  <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                    Gentle prompt
                  </p>
                  <p className="mt-2 text-sm leading-6 text-[#2F3E36]/80">
                    {selectedPrompt}
                  </p>
                </motion.div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 18 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.12, duration: 0.45 }}
                className="space-y-4 rounded-[1.75rem] border border-white/40 bg-white/[0.28] p-5"
              >
                <div>
                  <label
                    htmlFor="transcript"
                    className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]"
                  >
                    Live transcript
                  </label>
                  <textarea
                    id="transcript"
                    value={transcript}
                    onChange={(event) => setTranscript(event.target.value)}
                    className="mt-3 min-h-40 w-full rounded-[1.5rem] border border-white/50 bg-[#FDFBF7]/70 p-4 text-sm leading-7 text-[#2F3E36] outline-none placeholder:text-[#2F3E36]/40"
                    placeholder="Your spoken reflection will appear here..."
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                      Emotional intensity
                    </p>
                    <motion.span
                      key={intensity[0]}
                      initial={{ scale: 0.92, opacity: 0.65 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="rounded-full bg-white/40 px-3 py-1 text-sm"
                    >
                      {intensity[0]}%
                    </motion.span>
                  </div>
                  <div className="mt-4 px-1">
                    <Slider
                      value={intensity}
                      min={0}
                      max={100}
                      step={1}
                      onValueChange={setIntensity}
                      aria-label="Emotional intensity"
                    />
                  </div>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
                    Reflection starters
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {starterPrompts.map((prompt, index) => (
                      <motion.button
                        key={prompt}
                        type="button"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.18 + index * 0.06, duration: 0.28 }}
                        onClick={() => setSelectedPrompt(prompt)}
                        className={`rounded-full px-4 py-2 text-sm transition-colors ${
                          selectedPrompt === prompt
                            ? "bg-[#7E9F8B] text-white"
                            : "bg-white/35 text-[#2F3E36] hover:bg-white/55"
                        }`}
                      >
                        {prompt}
                      </motion.button>
                    ))}
                  </div>
                </div>
              </motion.div>
            </div>
          </div>

          <DialogFooter className="border-t border-white/35 bg-white/[0.18] p-6">
            <DialogClose asChild>
              <Button
                variant="outline"
                className="h-11 rounded-full border-white/50 bg-white/30 px-5 text-[#2F3E36] hover:bg-white/55"
              >
                Cancel
              </Button>
            </DialogClose>
            <motion.div whileTap={{ scale: 0.98 }}>
              <Button
                onClick={() => startTransition(() => void handleAnalyzeEmotion())}
                disabled={isPending || transcript.trim().length === 0}
                className="h-11 rounded-full border-0 bg-[#7E9F8B] px-5 text-white hover:bg-[#5C7D69]"
              >
                {isPending ? "Analyzing your reflection..." : "Analyze emotion"}
              </Button>
            </motion.div>
          </DialogFooter>
        </motion.div>
      </DialogContent>
    </Dialog>
  )
}
