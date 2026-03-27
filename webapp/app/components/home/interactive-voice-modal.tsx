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
import { useEffect, useRef, useState } from "react"

import { Button } from "~/components/ui/button"
import { useAuth } from "~/context/auth-context"
import { api, getWebSocketBaseUrl, type ConversationSocketEvent } from "~/lib/api"
import type { ConversationTurnResult } from "~/lib/contracts"
import { formatEmotionLabel, isSoulEmotion } from "~/lib/emotions"

type InteractiveVoiceModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
}

type ConversationMode =
  | "connecting"
  | "listening"
  | "review"
  | "processing"
  | "ai_replying"

type RecorderState =
  | "idle"
  | "requesting_permission"
  | "recording"
  | "stopping"
  | "transcribing"
  | "error"

const aiPrompts = [
  "What specific moment from today still feels unfinished?",
  "What did your body do when that moment landed?",
  "What would feel supportive for the next hour, not the whole week?",
] as const

type SelectedMimeType = {
  extension: string
  mimeType: string | undefined
}

const MIME_TYPE_CANDIDATES: SelectedMimeType[] = [
  { mimeType: "audio/webm;codecs=opus", extension: "webm" },
  { mimeType: "audio/webm", extension: "webm" },
  { mimeType: "audio/ogg;codecs=opus", extension: "ogg" },
  { mimeType: "audio/ogg", extension: "ogg" },
  { mimeType: "audio/mp4", extension: "m4a" },
  { mimeType: undefined, extension: "webm" },
]

function selectRecorderMimeType(): SelectedMimeType {
  if (typeof MediaRecorder === "undefined") {
    return MIME_TYPE_CANDIDATES[MIME_TYPE_CANDIDATES.length - 1]!
  }

  for (const candidate of MIME_TYPE_CANDIDATES) {
    if (!candidate.mimeType) {
      return candidate
    }

    if (typeof MediaRecorder.isTypeSupported !== "function") {
      return candidate
    }

    if (MediaRecorder.isTypeSupported(candidate.mimeType)) {
      return candidate
    }
  }

  return MIME_TYPE_CANDIDATES[MIME_TYPE_CANDIDATES.length - 1]!
}

function buildMicrophoneError(error: unknown) {
  if (error instanceof DOMException) {
    if (error.name === "NotAllowedError" || error.name === "SecurityError") {
      return "Microphone access is off. Allow it in your browser to speak your reflection."
    }

    if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
      return "No microphone was found on this device."
    }

    if (error.name === "NotReadableError" || error.name === "TrackStartError") {
      return "Your microphone is busy or unavailable right now."
    }

    if (error.name === "AbortError") {
      return "Recording was interrupted before it could start."
    }
  }

  return error instanceof Error
    ? error.message
    : "Microphone recording could not start."
}

function ListeningWaveform() {
  return (
    <div className="flex h-16 items-end justify-center gap-2">
      {Array.from({ length: 7 }).map((_, index) => (
        <motion.span
          key={index}
          className="w-2 rounded-full bg-[var(--brand-primary)]"
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
        className="relative text-[var(--brand-primary-muted)]"
      />
    </div>
  )
}

function formatElapsed(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60

  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`
}

function formatPrimaryFeeling(value: string | null | undefined) {
  return value && isSoulEmotion(value) ? formatEmotionLabel(value) : "Neutral"
}

export function InteractiveVoiceModal({
  open,
  onOpenChange,
}: InteractiveVoiceModalProps) {
  const { token } = useAuth()
  const socketRef = useRef<WebSocket | null>(null)
  const sessionIdRef = useRef<string | null>(null)
  const isClosingSessionRef = useRef(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<BlobPart[]>([])
  const extensionRef = useRef("webm")
  const isMountedRef = useRef(true)
  const [mode, setMode] = useState<ConversationMode>("connecting")
  const [recorderState, setRecorderState] = useState<RecorderState>("idle")
  const [promptIndex, setPromptIndex] = useState(0)
  const [recordingSeconds, setRecordingSeconds] = useState(0)
  const [showCloseConfirm, setShowCloseConfirm] = useState(false)
  const [transcript, setTranscript] = useState<string>("")
  const [result, setResult] = useState<ConversationTurnResult | null>(null)
  const [connectionError, setConnectionError] = useState<string | null>(null)

  function cleanupRecorder() {
    mediaRecorderRef.current = null
    chunksRef.current = []

    const stream = streamRef.current
    if (stream) {
      stream.getTracks().forEach((track) => track.stop())
    }

    streamRef.current = null
  }

  function updateRecorderState(nextState: RecorderState) {
    if (!isMountedRef.current) {
      return
    }

    setRecorderState(nextState)
  }

  async function transcribeRecording(audioBlob: Blob, extension: string) {
    if (!token) {
      throw new Error("Please sign in before using the microphone.")
    }

    const file = new File([audioBlob], `conversation-turn.${extension}`, {
      type: audioBlob.type || "audio/webm",
    })

    updateRecorderState("transcribing")
    setMode("processing")

    const response = await api.transcribeCheckinAudio(token, file)
    const nextTranscript = response.transcript.trim()

    if (!nextTranscript) {
      throw new Error("No words came through clearly enough to transcribe. Please try again.")
    }

    if (!isMountedRef.current) {
      return
    }

    setTranscript(nextTranscript)
    setConnectionError(null)
    setMode("review")
    updateRecorderState("idle")
  }

  async function startRecording() {
    if (
      typeof window === "undefined" ||
      typeof navigator === "undefined" ||
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === "undefined"
    ) {
      setConnectionError("Voice recording is not supported in this browser.")
      setMode("review")
      updateRecorderState("error")
      return
    }

    if (
      recorderState === "requesting_permission" ||
      recorderState === "recording" ||
      recorderState === "stopping" ||
      recorderState === "transcribing"
    ) {
      return
    }

    cleanupRecorder()
    setTranscript("")
    setResult(null)
    setRecordingSeconds(0)
    setConnectionError(null)
    updateRecorderState("requesting_permission")

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })

      const selection = selectRecorderMimeType()
      const recorder = selection.mimeType
        ? new MediaRecorder(stream, { mimeType: selection.mimeType })
        : new MediaRecorder(stream)

      streamRef.current = stream
      mediaRecorderRef.current = recorder
      chunksRef.current = []
      extensionRef.current = selection.extension

      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      })

      recorder.addEventListener("error", () => {
        cleanupRecorder()
        setConnectionError("Recording stopped unexpectedly. Please try again.")
        setMode("review")
        updateRecorderState("error")
      })

      recorder.addEventListener("stop", () => {
        const audioBlob = new Blob(chunksRef.current, {
          type: recorder.mimeType || selection.mimeType || "audio/webm",
        })

        cleanupRecorder()

        if (audioBlob.size === 0) {
          setConnectionError("We couldn't hear anything to transcribe. Please try again.")
          setMode("review")
          updateRecorderState("error")
          return
        }

        void transcribeRecording(audioBlob, selection.extension).catch((error) => {
          if (!isMountedRef.current) {
            return
          }

          setConnectionError(
            error instanceof Error
              ? error.message
              : "We couldn't transcribe that recording. Please try again."
          )
          setMode("review")
          updateRecorderState("error")
        })
      })

      recorder.start()
      setMode("listening")
      updateRecorderState("recording")
    } catch (error) {
      cleanupRecorder()
      setConnectionError(buildMicrophoneError(error))
      setMode("review")
      updateRecorderState("error")
    }
  }

  function stopRecording() {
    const recorder = mediaRecorderRef.current

    if (!recorder || recorder.state !== "recording") {
      return
    }

    updateRecorderState("stopping")
    recorder.stop()
  }

  useEffect(() => {
    return () => {
      isMountedRef.current = false
      cleanupRecorder()
    }
  }, [])

  useEffect(() => {
    if (!open) {
      return
    }

    setMode("connecting")
    setRecorderState("idle")
    setPromptIndex(0)
    setRecordingSeconds(0)
    setShowCloseConfirm(false)
    setTranscript("")
    setResult(null)
    setConnectionError(null)

    if (!token) {
      setConnectionError("Please sign in before opening a conversation.")
      setMode("review")
      return
    }

    const accessToken = token
    let cancelled = false

    async function startConversation() {
      try {
        const session = await api.createConversationSession(accessToken)

        if (cancelled) {
          void api.endConversationSession(accessToken, session.id).catch(() => undefined)
          return
        }

        sessionIdRef.current = session.id

        const socket = new WebSocket(
          `${getWebSocketBaseUrl()}/v1/conversations/ws/${session.id}?token=${encodeURIComponent(accessToken)}`
        )

        socketRef.current = socket

        socket.addEventListener("open", () => {
          if (!cancelled) {
            void startRecording()
          }
        })

        socket.addEventListener("message", (event) => {
          const payload = JSON.parse(event.data) as ConversationSocketEvent

          if (payload.type === "assistant_response") {
            setResult(payload.payload)
            setConnectionError(null)
            setMode("ai_replying")
            return
          }

          if (payload.type === "partial_transcript") {
            setTranscript(payload.text)
            return
          }

          if (payload.type === "final_transcript") {
            setTranscript(payload.text)
            setConnectionError(null)
            setMode("review")
            return
          }

          if (payload.type === "error") {
            setConnectionError(payload.message)
            setMode("review")
          }
        })

        socket.addEventListener("error", () => {
          setConnectionError("The conversation connection was interrupted.")
          setMode("review")
        })
      } catch (error) {
        if (!cancelled) {
          setConnectionError(
            error instanceof Error
              ? error.message
              : "Failed to start a conversation session."
          )
          setMode("review")
        }
      }
    }

    void startConversation()

    return () => {
      cancelled = true
    }
  }, [open, token])

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
  }, [open, transcript, mode])

  useEffect(() => {
    if (!open || mode !== "listening" || recorderState !== "recording") {
      return
    }

    const interval = window.setInterval(() => {
      setRecordingSeconds((previous) => previous + 1)
    }, 1000)

    return () => window.clearInterval(interval)
  }, [mode, open, recorderState])

  useEffect(() => {
    if (!open) {
      return
    }

    return () => {
      cleanupRecorder()

      const socket = socketRef.current
      if (
        socket &&
        (socket.readyState === WebSocket.OPEN ||
          socket.readyState === WebSocket.CONNECTING)
      ) {
        socket.close()
      }

      socketRef.current = null

      const sessionId = sessionIdRef.current
      sessionIdRef.current = null

      if (token && sessionId && !isClosingSessionRef.current) {
        isClosingSessionRef.current = true
        void api
          .endConversationSession(token, sessionId)
          .catch(() => undefined)
          .finally(() => {
            isClosingSessionRef.current = false
          })
      }
    }
  }, [open, token])

  const prompt = aiPrompts[promptIndex] ?? aiPrompts[0]
  const hasProgress =
    recordingSeconds > 0 ||
    result !== null ||
    transcript.trim().length > 0

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
    void startRecording()
  }

  function handleStopListening() {
    stopRecording()
  }

  function handleSendToAi() {
    const socket = socketRef.current

    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setConnectionError("The conversation connection is not ready.")
      return
    }

    if (!transcript.trim()) {
      setConnectionError("Add a transcript before sending this turn.")
      return
    }

    setConnectionError(null)
    setMode("processing")
    socket.send(
      JSON.stringify({
        type: "user_text",
        text: transcript.trim(),
      })
    )
  }

  function handleReply() {
    setPromptIndex((current) => (current + 1) % aiPrompts.length)
    void startRecording()
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
            <div className="absolute right-[-4rem] top-24 h-64 w-64 rounded-full bg-[var(--brand-primary)]/24 blur-3xl" />
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
                      <p className="text-xs uppercase tracking-[0.35em] text-[var(--brand-primary-muted)]">
                        Conversation
                      </p>
                      <h2
                        className="text-3xl leading-tight text-[#2F3E36] sm:text-4xl md:text-5xl"
                        style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
                      >
                        {result?.assistant_response || "The forest replied."}
                      </h2>
                      <p className="mx-auto max-w-2xl text-sm leading-7 text-[#2F3E36]/72 sm:text-base">
                        Holding a {formatPrimaryFeeling(result?.emotion_analysis.primary_label)} feeling.
                        Take a breath before you decide whether to continue.
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
                      <p className="text-xs uppercase tracking-[0.35em] text-[var(--brand-primary-muted)]">
                        Soul Forest
                      </p>
                      <h2
                        className="text-3xl leading-tight text-[#2F3E36] sm:text-4xl"
                        style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
                      >
                        {mode === "connecting"
                          ? "Opening a quiet space..."
                          : mode === "listening"
                            ? "Listening..."
                            : mode === "review"
                              ? "Ready to send this reflection?"
                              : "Shaping a thoughtful reply..."}
                      </h2>
                      <p className="text-sm leading-7 text-[#2F3E36]/72">
                        {prompt}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <div className="flex w-full max-w-3xl flex-col items-center gap-6 text-center">
                {connectionError ? (
                  <div className="w-full rounded-[1.5rem] bg-[#f4ddd4] px-4 py-3 text-sm text-[#8b4e3d]">
                    {connectionError}
                  </div>
                ) : null}

                <AnimatePresence mode="wait">
                  {mode === "connecting" ? (
                    <motion.div
                      key="connecting"
                      initial={{ opacity: 0, y: 18 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -12 }}
                      className="flex w-full flex-col items-center gap-5 rounded-[2rem] border border-white/45 bg-white/32 px-5 py-8 shadow-sm backdrop-blur-xl"
                    >
                      <ProcessingOrb />
                      <p className="max-w-xl text-sm leading-7 text-[#2F3E36]/70">
                        Preparing your conversation so you can move at a calm pace.
                      </p>
                    </motion.div>
                  ) : null}

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
                        {transcript || "Speak naturally. Your words will appear here once the recording stops."}
                      </p>
                      <div className="mt-5 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
                        <Button
                          onClick={handleStopListening}
                          disabled={recorderState !== "recording"}
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
                          You can review your words before sending them.
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
                          Review this reflection
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

                      <textarea
                        value={transcript}
                        onChange={(event) => setTranscript(event.target.value)}
                        placeholder="Your reflection will appear here after recording, and you can edit it before sending."
                        className="mt-5 min-h-32 w-full rounded-[1.5rem] bg-[#FDFBF7]/65 p-4 text-left text-sm leading-7 text-[#2F3E36]/74 outline-none"
                      />

                      <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:justify-center">
                        <Button
                          variant="outline"
                          onClick={handleRecordAgain}
                          disabled={recorderState === "requesting_permission" || recorderState === "transcribing"}
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
                          disabled={!transcript.trim() || recorderState === "transcribing"}
                          className="h-12 rounded-full border-0 bg-[var(--brand-primary)] px-6 text-sm text-[var(--brand-on-primary)] hover:bg-[var(--brand-primary-strong)]"
                        >
                          <HugeiconsIcon
                            icon={SparklesIcon}
                            size={16}
                            strokeWidth={1.8}
                            className="mr-2"
                          />
                          Send reflection
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
                      <p className="max-w-xl text-sm leading-7 text-[#2F3E36]/70">
                        Taking a moment to respond with care.
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
                          className="h-14 rounded-full border-0 bg-[var(--brand-primary)] px-8 text-sm text-[var(--brand-on-primary)] shadow-[0_16px_40px_rgba(18,199,127,0.28)] hover:bg-[var(--brand-primary-strong)]"
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
                        Finish conversation
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
                  <p className="text-xs uppercase tracking-[0.32em] text-[var(--brand-primary-muted)]">
                    Exit conversation
                  </p>
                  <h3
                    className="mt-3 text-2xl text-[#2F3E36]"
                    style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
                  >
                    Are you sure you want to close this conversation?
                  </h3>
                  <p className="mt-4 text-sm leading-7 text-[#2F3E36]/68">
                    This conversation will close for now. You can come back whenever you want another quiet moment.
                  </p>

                  <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
                    <Button
                      variant="outline"
                      onClick={() => setShowCloseConfirm(false)}
                      className="h-12 rounded-full border-white/50 bg-white/60 px-6 text-[#2F3E36] hover:bg-white"
                    >
                      Keep talking
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
