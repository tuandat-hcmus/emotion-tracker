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
import { useCallback, useEffect, useRef, useState } from "react"

import { Button } from "~/components/ui/button"
import { useAuth } from "~/context/auth-context"
import { api, getWebSocketBaseUrl } from "~/lib/api"
import type { CheckinDetail } from "~/lib/contracts"
import { formatEmotionLabel, isSoulEmotion } from "~/lib/emotions"

type InteractiveVoiceModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCheckinCreated?: (detail: CheckinDetail) => void
}

type ModalMode = "idle" | "recording" | "processing" | "result"

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
    if (!candidate.mimeType) return candidate
    if (
      typeof MediaRecorder.isTypeSupported === "function" &&
      MediaRecorder.isTypeSupported(candidate.mimeType)
    ) {
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
  return error instanceof Error ? error.message : "Microphone recording could not start."
}

function ListeningWaveform() {
  return (
    <div className="flex h-10 items-end justify-center gap-1.5">
      {Array.from({ length: 7 }).map((_, index) => (
        <motion.span
          key={index}
          className="w-1.5 rounded-full bg-[var(--brand-primary)]"
          animate={{
            height: ["0.75rem", `${1.6 + (index % 3) * 0.5}rem`, "0.75rem"],
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
  onCheckinCreated,
}: InteractiveVoiceModalProps) {
  const { token } = useAuth()
  const isMountedRef = useRef(true)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const micStreamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<BlobPart[]>([])
  const extensionRef = useRef("webm")

  // Camera refs
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const cameraStreamRef = useRef<MediaStream | null>(null)
  const frameIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const multimodalWsRef = useRef<WebSocket | null>(null)
  const multimodalSessionIdRef = useRef<string | null>(null)

  const [mode, setMode] = useState<ModalMode>("idle")
  const [recordingSeconds, setRecordingSeconds] = useState(0)
  const [cameraEnabled, setCameraEnabled] = useState(false)
  const [cameraActive, setCameraActive] = useState(false)
  const [transcript, setTranscript] = useState("")
  const [result, setResult] = useState<CheckinDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showCloseConfirm, setShowCloseConfirm] = useState(false)
  const [faceLabel, setFaceLabel] = useState<string | null>(null)

  // Cleanup helpers
  const cleanupMic = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      try { mediaRecorderRef.current.stop() } catch { /* ignore */ }
    }
    mediaRecorderRef.current = null
    chunksRef.current = []
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((t) => t.stop())
      micStreamRef.current = null
    }
  }, [])

  const cleanupCamera = useCallback(() => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current)
      frameIntervalRef.current = null
    }
    if (cameraStreamRef.current) {
      cameraStreamRef.current.getTracks().forEach((t) => t.stop())
      cameraStreamRef.current = null
    }
    if (multimodalWsRef.current) {
      multimodalWsRef.current.close()
      multimodalWsRef.current = null
    }
    setCameraActive(false)
  }, [])

  const cleanupAll = useCallback(() => {
    cleanupMic()
    cleanupCamera()
  }, [cleanupMic, cleanupCamera])

  // Reset on open
  useEffect(() => {
    if (!open) return
    setMode("idle")
    setRecordingSeconds(0)
    setCameraEnabled(false)
    setCameraActive(false)
    setTranscript("")
    setResult(null)
    setError(null)
    setShowCloseConfirm(false)
    setFaceLabel(null)
    multimodalSessionIdRef.current = null
  }, [open])

  // Mount tracking
  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
      cleanupAll()
    }
  }, [cleanupAll])

  // Cleanup on close
  useEffect(() => {
    if (!open) return () => cleanupAll()
  }, [open, cleanupAll])

  // Recording timer
  useEffect(() => {
    if (!open || mode !== "recording") return
    const interval = window.setInterval(() => {
      setRecordingSeconds((p) => p + 1)
    }, 1000)
    return () => window.clearInterval(interval)
  }, [mode, open])

  // Escape key
  useEffect(() => {
    if (!open) return
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") requestClose()
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [open, mode, transcript])

  // --- Camera logic ---
  async function startCamera() {
    if (!token) return

    try {
      // Create multimodal session
      const session = await api.createMultimodalSession(token)
      if (!isMountedRef.current) return
      multimodalSessionIdRef.current = session.session_id

      // Open multimodal WebSocket
      const wsBase = getWebSocketBaseUrl()
      const ws = new WebSocket(
        `${wsBase}/v1/multimodal/ws/${session.session_id}?token=${encodeURIComponent(token)}`
      )
      multimodalWsRef.current = ws

      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data as string)
          if (msg.type === "face_emotion" && msg.face_detected) {
            setFaceLabel(String(msg.label))
          }
        } catch { /* ignore */ }
      }

      // Start video
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 320, height: 240, facingMode: "user" },
        audio: false,
      })
      if (!isMountedRef.current) {
        stream.getTracks().forEach((t) => t.stop())
        ws.close()
        return
      }

      cameraStreamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream
      setCameraActive(true)

      // Send frames at 2fps once WS is open
      ws.onopen = () => {
        frameIntervalRef.current = setInterval(() => {
          const canvas = canvasRef.current
          const video = videoRef.current
          if (!canvas || !video || ws.readyState !== WebSocket.OPEN) return
          canvas.width = 320
          canvas.height = 240
          canvas.getContext("2d")?.drawImage(video, 0, 0, 320, 240)
          const b64 = canvas.toDataURL("image/jpeg", 0.6).split(",")[1]
          if (b64) ws.send(JSON.stringify({ type: "frame", data: b64 }))
        }, 500)
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err.message : "Could not start camera.")
      }
    }
  }

  // --- Recording logic ---
  async function startRecording() {
    if (typeof MediaRecorder === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setError("Voice recording is not supported in this browser.")
      return
    }

    cleanupMic()
    setTranscript("")
    setResult(null)
    setRecordingSeconds(0)
    setError(null)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
      })

      const selection = selectRecorderMimeType()
      const recorder = selection.mimeType
        ? new MediaRecorder(stream, { mimeType: selection.mimeType })
        : new MediaRecorder(stream)

      micStreamRef.current = stream
      mediaRecorderRef.current = recorder
      chunksRef.current = []
      extensionRef.current = selection.extension

      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      })

      recorder.addEventListener("error", () => {
        cleanupMic()
        setError("Recording stopped unexpectedly. Please try again.")
        setMode("idle")
      })

      recorder.addEventListener("stop", () => {
        const audioBlob = new Blob(chunksRef.current, {
          type: recorder.mimeType || selection.mimeType || "audio/webm",
        })
        cleanupMic()

        if (audioBlob.size === 0) {
          setError("We couldn't hear anything. Please try again.")
          setMode("idle")
          return
        }

        void processRecording(audioBlob, selection.extension)
      })

      recorder.start()
      setMode("recording")
    } catch (err) {
      cleanupMic()
      setError(buildMicrophoneError(err))
    }
  }

  async function stopRecording() {
    const recorder = mediaRecorderRef.current
    if (recorder && recorder.state === "recording") {
      recorder.stop()
    }
  }

  // --- Processing pipeline ---
  async function processRecording(audioBlob: Blob, extension: string) {
    if (!token) {
      setError("Please sign in before recording.")
      setMode("idle")
      return
    }

    setMode("processing")

    try {
      // 1. Transcribe audio
      const file = new File([audioBlob], `recording.${extension}`, {
        type: audioBlob.type || "audio/webm",
      })
      const transcription = await api.transcribeCheckinAudio(token, file)
      const text = transcription.transcript.trim()

      if (!text) {
        setError("No words came through clearly enough. Please try again.")
        setMode("idle")
        return
      }

      if (!isMountedRef.current) return
      setTranscript(text)

      // 2. Create text check-in (runs full emotion pipeline + saves to DB)
      const checkinResult = await api.createTextCheckin(token, { text, session_type: "free" })
      if (!isMountedRef.current) return

      // 3. If camera was enabled, end multimodal session and link to journal entry
      if (multimodalSessionIdRef.current) {
        try {
          await api.endMultimodalSession(token, multimodalSessionIdRef.current, {
            journal_entry_id: checkinResult.entry_id,
          })
        } catch {
          // Non-critical — text check-in already saved
        }
        cleanupCamera()
      }

      setResult(checkinResult)
      setMode("result")
      onCheckinCreated?.(checkinResult)
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err.message : "Processing failed. Please try again.")
        setMode("idle")
      }
    }
  }

  // --- Camera toggle ---
  async function handleToggleCamera() {
    if (cameraActive) {
      cleanupCamera()
      setCameraEnabled(false)
      return
    }
    setCameraEnabled(true)
    await startCamera()

    // Auto-start voice recording when camera is enabled
    if (mode === "idle") {
      await startRecording()
    }
  }

  // --- Mic button ---
  async function handleMicButton() {
    if (mode === "recording") {
      await stopRecording()
    } else if (mode === "idle") {
      await startRecording()
    }
  }

  // --- Close logic ---
  const hasProgress = recordingSeconds > 0 || result !== null || transcript.trim().length > 0

  function requestClose() {
    if (hasProgress && mode !== "result") {
      setShowCloseConfirm(true)
      return
    }
    cleanupAll()
    onOpenChange(false)
  }

  function handleConfirmClose() {
    setShowCloseConfirm(false)
    cleanupAll()
    onOpenChange(false)
  }

  function handleRecordAgain() {
    setResult(null)
    setTranscript("")
    setFaceLabel(null)
    setError(null)
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
            {/* Close button */}
            <div className="pointer-events-none absolute inset-x-0 top-0 z-30 flex justify-end px-6 pt-5 sm:px-10">
              <button
                type="button"
                onClick={requestClose}
                className="pointer-events-auto flex h-12 w-12 items-center justify-center rounded-full border border-white/55 bg-white/45 text-[#2F3E36] shadow-sm backdrop-blur-md transition-colors hover:bg-white/65"
                aria-label="Close"
              >
                <HugeiconsIcon icon={Cancel01Icon} size={20} strokeWidth={1.8} />
              </button>
            </div>

            <div className="mx-auto flex w-full max-w-lg flex-1 flex-col items-center justify-center gap-6">
              {/* Hidden camera elements */}
              <video ref={videoRef} autoPlay muted playsInline className="hidden" />
              <canvas ref={canvasRef} className="hidden" />

              {/* Single card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="w-full rounded-[2rem] border border-white/45 bg-white/32 px-6 py-8 shadow-sm backdrop-blur-xl"
              >
                {/* Header: status + timer */}
                <div className="flex items-center justify-between">
                  <div className="inline-flex items-center gap-2 rounded-full bg-[#2F3E36]/8 px-3 py-1.5 text-xs font-medium text-[#2F3E36]">
                    {mode === "recording" ? (
                      <>
                        <HugeiconsIcon icon={RecordIcon} size={14} strokeWidth={1.8} className="text-[#D26D57]" />
                        REC
                      </>
                    ) : mode === "processing" ? (
                      <>
                        <HugeiconsIcon icon={SparklesIcon} size={14} strokeWidth={1.8} className="text-[var(--brand-primary)]" />
                        Processing
                      </>
                    ) : mode === "result" ? (
                      <>
                        <HugeiconsIcon icon={SparklesIcon} size={14} strokeWidth={1.8} className="text-[var(--brand-primary)]" />
                        Done
                      </>
                    ) : (
                      <span className="text-[#2F3E36]/60">Ready</span>
                    )}
                  </div>
                  <div className="inline-flex items-center gap-2 rounded-full bg-white/52 px-3 py-1.5 text-xs font-medium text-[#2F3E36]/78">
                    <HugeiconsIcon icon={Clock02Icon} size={14} strokeWidth={1.8} />
                    {formatElapsed(recordingSeconds)}
                  </div>
                </div>

                {/* Content area */}
                <div className="mt-6 min-h-[6rem]">
                  <AnimatePresence mode="wait">
                    {mode === "recording" ? (
                      <motion.div
                        key="recording"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="space-y-4"
                      >
                        <ListeningWaveform />
                        <p className="text-center text-sm leading-7 text-[#2F3E36]/70">
                          Speak naturally. Your words will appear here once the recording stops.
                        </p>
                        {faceLabel && (
                          <div className="flex items-center justify-center gap-2">
                            <span className="rounded-full bg-[var(--brand-primary-soft)] px-2.5 py-0.5 text-xs text-[var(--brand-primary-muted)] capitalize">
                              Detected: {faceLabel}
                            </span>
                          </div>
                        )}
                      </motion.div>
                    ) : mode === "processing" ? (
                      <motion.div
                        key="processing"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex flex-col items-center gap-4"
                      >
                        <motion.div
                          className="h-10 w-10 rounded-full border-2 border-[var(--brand-primary)] border-t-transparent"
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        />
                        <p className="text-center text-sm text-[#2F3E36]/70">
                          {transcript ? "Analyzing your reflection..." : "Transcribing your voice..."}
                        </p>
                      </motion.div>
                    ) : mode === "result" && result ? (
                      <motion.div
                        key="result"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="space-y-4"
                      >
                        <p className="text-center text-sm leading-7 text-[#2F3E36]/55">
                          {transcript}
                        </p>
                        <div className="rounded-[1.25rem] bg-[#FDFBF7]/65 p-4 text-center">
                          <p className="text-xs uppercase tracking-[0.3em] text-[var(--brand-primary-muted)]">
                            Feeling {formatPrimaryFeeling(result.primary_label)}
                          </p>
                          {result.ai_response && (
                            <p
                              className="mt-3 text-lg leading-8 text-[#2F3E36]"
                              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
                            >
                              {result.ai_response}
                            </p>
                          )}
                          {result.gentle_suggestion && (
                            <p className="mt-2 text-sm text-[#2F3E36]/60">
                              {result.gentle_suggestion}
                            </p>
                          )}
                        </div>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="idle"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex flex-col items-center gap-3"
                      >
                        <p
                          className="text-center text-xl leading-tight text-[#2F3E36]"
                          style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
                        >
                          Ready for a quiet moment?
                        </p>
                        <p className="text-center text-sm leading-7 text-[#2F3E36]/55">
                          Press the mic to speak, or enable the camera for face detection too.
                        </p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Error */}
                {error && (
                  <div className="mt-4 rounded-[1rem] bg-[#f4ddd4] px-4 py-2.5 text-center text-sm text-[#8b4e3d]">
                    {error}
                  </div>
                )}

                {/* Action buttons */}
                <div className="mt-6 flex items-center justify-center gap-3">
                  {mode === "idle" ? (
                    <>
                      {/* Mic button */}
                      <Button
                        onClick={() => void handleMicButton()}
                        className="h-14 rounded-full border-0 bg-[var(--brand-primary)] px-8 text-sm text-[var(--brand-on-primary)] shadow-[0_12px_32px_rgba(18,199,127,0.22)] hover:bg-[var(--brand-primary-strong)]"
                      >
                        <HugeiconsIcon icon={Mic01Icon} size={18} strokeWidth={1.8} className="mr-2" />
                        Record
                      </Button>

                      {/* Camera button */}
                      <Button
                        onClick={() => void handleToggleCamera()}
                        variant="outline"
                        className={`h-14 rounded-full border-white/50 px-6 text-sm transition-colors ${
                          cameraActive
                            ? "border-[var(--brand-primary)] bg-[var(--brand-primary-soft)] text-[var(--brand-primary-muted)]"
                            : "bg-white/35 text-[#2F3E36] hover:bg-white/55"
                        }`}
                      >
                        <svg className="mr-2" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M23 7 16 12 23 17V7z" />
                          <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
                        </svg>
                        {cameraActive ? "Camera on" : "Camera"}
                      </Button>
                    </>
                  ) : mode === "recording" ? (
                    <Button
                      onClick={() => void handleMicButton()}
                      className="h-14 rounded-full border-0 bg-[#2F3E36] px-8 text-sm text-white hover:bg-[#24302a]"
                    >
                      <HugeiconsIcon icon={StopCircleIcon} size={18} strokeWidth={1.8} className="mr-2" />
                      Stop listening
                    </Button>
                  ) : mode === "result" ? (
                    <div className="flex flex-col items-center gap-3 sm:flex-row">
                      <Button
                        onClick={handleRecordAgain}
                        className="h-12 rounded-full border-0 bg-[var(--brand-primary)] px-6 text-sm text-[var(--brand-on-primary)] hover:bg-[var(--brand-primary-strong)]"
                      >
                        <HugeiconsIcon icon={Mic01Icon} size={16} strokeWidth={1.8} className="mr-2" />
                        Record again
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={requestClose}
                        className="h-12 rounded-full bg-white/25 px-6 text-[#2F3E36] hover:bg-white/45"
                      >
                        Done
                      </Button>
                    </div>
                  ) : null}
                </div>
              </motion.div>
            </div>
          </div>

          {/* Close confirmation overlay */}
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
                  <h3
                    className="text-2xl text-[#2F3E36]"
                    style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
                  >
                    Leave this recording?
                  </h3>
                  <p className="mt-3 text-sm leading-7 text-[#2F3E36]/68">
                    Your current recording will be lost.
                  </p>
                  <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:justify-center">
                    <Button
                      variant="outline"
                      onClick={() => setShowCloseConfirm(false)}
                      className="h-12 rounded-full border-white/50 bg-white/60 px-6 text-[#2F3E36] hover:bg-white"
                    >
                      Stay
                    </Button>
                    <Button
                      onClick={handleConfirmClose}
                      className="h-12 rounded-full border-0 bg-[#2F3E36] px-6 text-white hover:bg-[#24302a]"
                    >
                      Leave
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
