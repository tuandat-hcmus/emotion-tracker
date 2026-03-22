import { AnimatePresence, motion } from "framer-motion"
import {
  Cancel01Icon,
  Clock02Icon,
  Mic01Icon,
  RecordIcon,
  SparklesIcon,
  StopCircleIcon,
} from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { useEffect, useState } from "react"

import { Button } from "~/components/ui/button"

type InteractiveVoiceModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
}

type ConversationMode =
  | "listening"
  | "review"
  | "processing"
  | "ai_replying"

const aiPrompts = [
  "I hear you. What specific moment made you feel that way today?",
  "Where did you notice that feeling living in your body?",
  "What would help your nervous system feel 5% softer tonight?",
]

const transcriptPlaceholders = [
  "\"I kept trying to stay composed, but the afternoon felt heavier than I expected...\"",
  "\"I noticed my chest tighten after that conversation, and I carried it longer than I wanted...\"",
  "\"By evening I finally had a quiet moment, and that gave me enough room to breathe again...\"",
]

const processingStages = [
  "Capturing your reflection",
  "Organizing the emotional threads",
  "Preparing a gentle reply",
]

function ListeningWaveform() {
  return (
    <div className="flex h-16 items-end justify-center gap-2">
      {Array.from({ length: 7 }).map((_, index) => (
        <motion.span
          key={index}
          className="w-2 rounded-full bg-[#7E9F8B]"
          animate={{
            height: ["1.25rem", `${2.6 + (index % 3) * 0.8}rem`, "1.25rem"],
            opacity: [0.45, 1, 0.45],
          }}
          transition={{
            duration: 1.4,
            repeat: Infinity,
            delay: index * 0.09,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  )
}

function ProcessingOrb() {
  return (
    <div className="relative flex h-20 w-20 items-center justify-center">
      <motion.div
        className="absolute inset-0 rounded-full border border-white/50"
        animate={{ opacity: [0.7, 0.12, 0.7], scale: [1, 1.22, 1] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute inset-3 rounded-full bg-white/40"
        animate={{ scale: [0.95, 1.12, 0.95] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
      />
      <HugeiconsIcon
        icon={SparklesIcon}
        size={24}
        strokeWidth={1.8}
        className="relative text-[#7E9F8B]"
      />
    </div>
  )
}

function formatElapsed(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60

  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`
}

export function InteractiveVoiceModal({
  open,
  onOpenChange,
}: InteractiveVoiceModalProps) {
  const [mode, setMode] = useState<ConversationMode>("listening")
  const [promptIndex, setPromptIndex] = useState(0)
  const [processingStageIndex, setProcessingStageIndex] = useState(0)
  const [recordingSeconds, setRecordingSeconds] = useState(0)
  const [showCloseConfirm, setShowCloseConfirm] = useState(false)

  useEffect(() => {
    if (!open) {
      return
    }

    setMode("listening")
    setPromptIndex(0)
    setProcessingStageIndex(0)
    setRecordingSeconds(0)
    setShowCloseConfirm(false)
  }, [open])

  useEffect(() => {
    if (!open) {
      return
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        requestClose()
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [open, recordingSeconds, mode])

  useEffect(() => {
    if (!open || mode !== "listening") {
      return
    }

    const interval = window.setInterval(() => {
      setRecordingSeconds((previous) => previous + 1)
    }, 1000)

    return () => window.clearInterval(interval)
  }, [mode, open])

  useEffect(() => {
    if (!open || mode !== "processing") {
      return
    }

    const interval = window.setInterval(() => {
      setProcessingStageIndex((previous) => (previous + 1) % processingStages.length)
    }, 450)

    const timeout = window.setTimeout(() => {
      window.clearInterval(interval)
      setMode("ai_replying")
    }, 1800)

    return () => {
      window.clearInterval(interval)
      window.clearTimeout(timeout)
    }
  }, [mode, open])

  const transcript =
    transcriptPlaceholders[promptIndex] ?? transcriptPlaceholders[0]
  const prompt = aiPrompts[promptIndex] ?? aiPrompts[0]
  const processingStage =
    processingStages[processingStageIndex] ?? processingStages[0]
  const hasProgress = recordingSeconds > 0 || mode !== "listening"

  function handleReply() {
    setPromptIndex((previous) => (previous + 1) % aiPrompts.length)
    setRecordingSeconds(0)
    setMode("listening")
  }

  function requestClose() {
    if (hasProgress) {
      setShowCloseConfirm(true)
      return
    }

    onOpenChange(false)
  }

  function handleConfirmClose() {
    setShowCloseConfirm(false)
    onOpenChange(false)
  }

  function handleRecordAgain() {
    setRecordingSeconds(0)
    setMode("listening")
  }

  function handleSendToAi() {
    setProcessingStageIndex(0)
    setMode("processing")
  }

  function handleStopListening() {
    setMode("review")
  }

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 overflow-hidden bg-[#FDFBF7]/46 backdrop-blur-[18px]"
        >
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(168,195,216,0.44),rgba(253,251,247,0.4),rgba(126,159,139,0.24))]" />
          <div className="absolute inset-0 bg-[#2F3E36]/18" />
          <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(253,251,247,0.75),rgba(253,251,247,0.34),rgba(47,62,54,0.18))]" />
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute left-[-5rem] top-16 h-56 w-56 rounded-full bg-[#A8C3D8]/26 blur-3xl" />
            <div className="absolute right-[-4rem] top-24 h-64 w-64 rounded-full bg-[#7E9F8B]/24 blur-3xl" />
            <div className="absolute bottom-[-3rem] left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-[#EAD2AC]/28 blur-3xl" />
          </div>

          <div className="relative z-10 flex min-h-svh flex-col px-6 pb-8 pt-20 sm:px-10">
            <div className="pointer-events-none absolute inset-x-0 top-0 z-30 flex justify-end px-6 pt-5 sm:px-10">
              <button
                type="button"
                onClick={requestClose}
                className="pointer-events-auto flex h-12 w-12 items-center justify-center rounded-full border border-white/55 bg-white/45 text-[#2F3E36] shadow-sm backdrop-blur-md transition-colors hover:bg-white/65"
                aria-label="Close conversation overlay"
              >
                <HugeiconsIcon
                  icon={Cancel01Icon}
                  size={20}
                  strokeWidth={1.8}
                />
              </button>
            </div>

            <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col items-center justify-between">
              <div className="flex min-h-[12rem] flex-1 items-center justify-center text-center">
                <AnimatePresence mode="wait">
                  {mode === "ai_replying" ? (
                    <motion.div
                      key="ai-reply"
                      initial={{ opacity: 0, y: 22 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -16 }}
                      transition={{ duration: 0.55, ease: "easeOut" }}
                      className="max-w-3xl space-y-6 rounded-[2rem] border border-white/40 bg-white/28 px-6 py-6 shadow-sm backdrop-blur-xl"
                    >
                      <p className="text-xs uppercase tracking-[0.35em] text-[#7E9F8B]">
                        Ethereal conversation
                      </p>
                      <h2
                        className="text-3xl leading-tight text-[#2F3E36] sm:text-4xl md:text-5xl"
                        style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
                      >
                        {prompt}
                      </h2>
                      <p className="mx-auto max-w-2xl text-sm leading-7 text-[#2F3E36]/72 sm:text-base">
                        The forest is reflecting your words with care. If you
                        want to keep going, answer with one more honest breath.
                      </p>
                    </motion.div>
                  ) : (
                    <motion.div
                      key={mode}
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -12 }}
                      transition={{ duration: 0.45, ease: "easeOut" }}
                      className="space-y-5 rounded-[2rem] border border-white/40 bg-white/24 px-6 py-6 text-center shadow-sm backdrop-blur-xl"
                    >
                      <p className="text-xs uppercase tracking-[0.35em] text-[#7E9F8B]">
                        Soul Forest
                      </p>
                      <h2
                        className="text-3xl leading-tight text-[#2F3E36] sm:text-4xl"
                        style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
                      >
                        {mode === "listening"
                          ? "Listening to your thoughts..."
                          : mode === "review"
                            ? "Ready to send this reflection?"
                            : "Letting the canopy gather what it heard..."}
                      </h2>
                      {mode === "listening" ? (
                        <p className="text-sm leading-7 text-[#2F3E36]/72">
                          Speak freely, then tap stop when you want the forest
                          to respond.
                        </p>
                      ) : mode === "review" ? (
                        <p className="text-sm leading-7 text-[#2F3E36]/72">
                          Listen back to your intention for a second. You can
                          record again or approve this entry before AI
                          reflection begins.
                        </p>
                      ) : null}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <div className="flex w-full max-w-3xl flex-col items-center gap-6 text-center">
                <AnimatePresence mode="wait">
                  {mode === "listening" ? (
                    <motion.div
                      key="listening"
                      initial={{ opacity: 0, y: 18 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -12 }}
                      transition={{ duration: 0.4 }}
                      className="w-full rounded-[2rem] border border-white/45 bg-white/32 px-5 py-6 shadow-sm backdrop-blur-xl"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="inline-flex items-center gap-2 rounded-full bg-[#2F3E36]/8 px-3 py-1.5 text-xs font-medium text-[#2F3E36]">
                          <HugeiconsIcon
                            icon={RecordIcon}
                            size={14}
                            strokeWidth={1.8}
                            className="text-[#D26D57]"
                          />
                          REC
                        </div>
                        <div className="inline-flex items-center gap-2 rounded-full bg-white/52 px-3 py-1.5 text-xs font-medium text-[#2F3E36]/78">
                          <HugeiconsIcon
                            icon={Clock02Icon}
                            size={14}
                            strokeWidth={1.8}
                          />
                          {formatElapsed(recordingSeconds)}
                        </div>
                      </div>
                      <ListeningWaveform />
                      <p className="mt-5 text-sm leading-7 text-[#2F3E36]/70">
                        {transcript}
                      </p>
                      <div className="mt-5 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
                        <Button
                          onClick={handleStopListening}
                          className="h-12 rounded-full border-0 bg-[#2F3E36] px-6 text-sm text-white hover:bg-[#24302a]"
                        >
                          <HugeiconsIcon
                            icon={StopCircleIcon}
                            size={16}
                            strokeWidth={1.8}
                            className="mr-2"
                          />
                          Stop listening
                        </Button>
                        <p className="text-xs text-[#2F3E36]/58">
                          The timer stops when you press this button.
                        </p>
                      </div>
                    </motion.div>
                  ) : null}

                  {mode === "review" ? (
                    <motion.div
                      key="review"
                      initial={{ opacity: 0, y: 18 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -12 }}
                      transition={{ duration: 0.4 }}
                      className="w-full rounded-[2rem] border border-white/45 bg-white/32 px-5 py-6 shadow-sm backdrop-blur-xl"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="inline-flex items-center gap-2 rounded-full bg-[#2F3E36]/8 px-3 py-1.5 text-xs font-medium text-[#2F3E36]">
                          <HugeiconsIcon
                            icon={RecordIcon}
                            size={14}
                            strokeWidth={1.8}
                            className="text-[#D26D57]"
                          />
                          Review your voice note
                        </div>
                        <div className="inline-flex items-center gap-2 rounded-full bg-white/52 px-3 py-1.5 text-xs font-medium text-[#2F3E36]/78">
                          <HugeiconsIcon
                            icon={Clock02Icon}
                            size={14}
                            strokeWidth={1.8}
                          />
                          {formatElapsed(recordingSeconds)}
                        </div>
                      </div>

                      <p className="mt-5 rounded-[1.5rem] bg-[#FDFBF7]/65 p-4 text-left text-sm leading-7 text-[#2F3E36]/74">
                        {transcript}
                      </p>

                      <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:justify-center">
                        <Button
                          variant="outline"
                          onClick={handleRecordAgain}
                          className="h-12 rounded-full border-white/50 bg-white/35 px-6 text-sm text-[#2F3E36] hover:bg-white/55"
                        >
                          <HugeiconsIcon
                            icon={Mic01Icon}
                            size={16}
                            strokeWidth={1.8}
                            className="mr-2"
                          />
                          Record again
                        </Button>
                        <Button
                          onClick={handleSendToAi}
                          className="h-12 rounded-full border-0 bg-[#7E9F8B] px-6 text-sm text-white hover:bg-[#6E8F7C]"
                        >
                          <HugeiconsIcon
                            icon={SparklesIcon}
                            size={16}
                            strokeWidth={1.8}
                            className="mr-2"
                          />
                          Send to AI
                        </Button>
                      </div>
                    </motion.div>
                  ) : null}

                  {mode === "processing" ? (
                    <motion.div
                      key="processing"
                      initial={{ opacity: 0, y: 18 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -12 }}
                      transition={{ duration: 0.4 }}
                      className="flex w-full flex-col items-center gap-5 rounded-[2rem] border border-white/45 bg-white/32 px-5 py-8 shadow-sm backdrop-blur-xl"
                    >
                      <ProcessingOrb />
                      <div className="flex flex-wrap justify-center gap-2">
                        {processingStages.map((stage, index) => {
                          const active = index === processingStageIndex

                          return (
                            <span
                              key={stage}
                              className={`rounded-full px-3 py-1.5 text-xs transition-colors ${
                                active
                                  ? "bg-[#7E9F8B] text-white"
                                  : "bg-white/45 text-[#2F3E36]/62"
                              }`}
                            >
                              {stage}
                            </span>
                          )
                        })}
                      </div>
                      <p className="max-w-xl text-sm leading-7 text-[#2F3E36]/70">
                        {processingStage}
                      </p>
                    </motion.div>
                  ) : null}

                  {mode === "ai_replying" ? (
                    <motion.div
                      key="actions"
                      initial={{ opacity: 0, y: 18 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -12 }}
                      transition={{ duration: 0.4 }}
                      className="flex flex-col items-center gap-3"
                    >
                      <motion.div
                        animate={{ scale: [1, 1.04, 1] }}
                        transition={{
                          duration: 2.4,
                          repeat: Infinity,
                          ease: "easeInOut",
                        }}
                      >
                        <Button
                          onClick={handleReply}
                          className="h-14 rounded-full border-0 bg-[#7E9F8B] px-8 text-sm text-white shadow-[0_16px_40px_rgba(126,159,139,0.28)] hover:bg-[#6E8F7C]"
                        >
                          <HugeiconsIcon
                            icon={Mic01Icon}
                            size={16}
                            strokeWidth={1.8}
                            className="mr-2"
                          />
                          Reply
                        </Button>
                      </motion.div>
                      <Button
                        variant="ghost"
                        onClick={requestClose}
                        className="h-12 rounded-full bg-white/25 px-6 text-[#2F3E36] hover:bg-white/45"
                      >
                        Finish &amp; Grow Tree
                      </Button>
                    </motion.div>
                  ) : null}
                </AnimatePresence>
              </div>
            </div>
          </div>

          <AnimatePresence>
            {showCloseConfirm ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 z-20 flex items-center justify-center bg-[#2F3E36]/26 px-6"
              >
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 8 }}
                  transition={{ duration: 0.28, ease: "easeOut" }}
                  className="w-full max-w-md rounded-[2rem] border border-white/45 bg-white/82 p-6 text-center shadow-sm backdrop-blur-xl"
                >
                  <p className="text-xs uppercase tracking-[0.32em] text-[#7E9F8B]">
                    Exit recording
                  </p>
                  <h3
                    className="mt-3 text-2xl text-[#2F3E36]"
                    style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
                  >
                    Are you sure you want to close this recording?
                  </h3>
                  <p className="mt-4 text-sm leading-7 text-[#2F3E36]/68">
                    Your current voice reflection will be dismissed if you exit
                    now.
                  </p>

                  <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
                    <Button
                      variant="outline"
                      onClick={() => setShowCloseConfirm(false)}
                      className="h-12 rounded-full border-white/50 bg-white/60 px-6 text-[#2F3E36] hover:bg-white"
                    >
                      Keep recording
                    </Button>
                    <Button
                      onClick={handleConfirmClose}
                      className="h-12 rounded-full border-0 bg-[#2F3E36] px-6 text-white hover:bg-[#24302a]"
                    >
                      Yes, close it
                    </Button>
                  </div>
                </motion.div>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}
