import { useEffect, useRef, useState } from "react"
import { Mic01Icon, StopCircleIcon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"

import { api } from "~/lib/api"

type MicTranscriptButtonProps = {
  disabled?: boolean
  token: string | null
  onTranscriptReady: (transcript: string) => void
}

type RecorderState =
  | "idle"
  | "requesting_permission"
  | "recording"
  | "stopping"
  | "transcribing"
  | "ready"
  | "error"

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
      return "Microphone access is off. Allow it in your browser to speak your message."
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

function formatElapsed(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`
}

export function MicTranscriptButton({
  disabled = false,
  token,
  onTranscriptReady,
}: MicTranscriptButtonProps) {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<BlobPart[]>([])
  const extensionRef = useRef("webm")
  const stopReasonRef = useRef<"cancelled" | "interrupted" | null>(null)
  const uploadAbortControllerRef = useRef<AbortController | null>(null)
  const isMountedRef = useRef(true)

  const [recorderState, setRecorderState] = useState<RecorderState>("idle")
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  useEffect(() => {
    if (recorderState !== "recording") {
      return
    }

    const intervalId = window.setInterval(() => {
      setElapsedSeconds((current) => current + 1)
    }, 1000)

    return () => window.clearInterval(intervalId)
  }, [recorderState])

  useEffect(() => {
    return () => {
      isMountedRef.current = false
      uploadAbortControllerRef.current?.abort()
      cleanupRecorder()
    }
  }, [])

  function updateUiState(nextState: RecorderState, nextMessage: string | null) {
    if (!isMountedRef.current) {
      return
    }

    setRecorderState(nextState)
    setStatusMessage(nextMessage)
  }

  function cleanupRecorder() {
    mediaRecorderRef.current = null
    chunksRef.current = []
    stopReasonRef.current = null

    const stream = streamRef.current
    if (stream) {
      stream.getTracks().forEach((track) => track.stop())
    }
    streamRef.current = null
  }

  async function uploadTranscript(audioBlob: Blob, extension: string) {
    if (!token) {
      throw new Error("Please sign in before using the microphone.")
    }

    const fileType = audioBlob.type || "audio/webm"
    const file = new File([audioBlob], `journal-checkin.${extension}`, {
      type: fileType,
    })

    const controller = new AbortController()
    uploadAbortControllerRef.current = controller

    try {
      const response = await api.transcribeCheckinAudio(token, file, controller.signal)
      if (!response.transcript.trim()) {
        throw new Error("No words came through clearly enough to transcribe. Please try again.")
      }

      if (isMountedRef.current) {
        onTranscriptReady(response.transcript.trim())
      }
    } finally {
      if (uploadAbortControllerRef.current === controller) {
        uploadAbortControllerRef.current = null
      }
    }
  }

  async function startRecording() {
    if (
      disabled ||
      recorderState === "requesting_permission" ||
      recorderState === "stopping" ||
      recorderState === "transcribing"
    ) {
      return
    }

    if (
      typeof window === "undefined" ||
      typeof navigator === "undefined" ||
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === "undefined"
    ) {
      updateUiState("error", "Voice recording is not supported in this browser.")
      return
    }

    uploadAbortControllerRef.current?.abort()
    uploadAbortControllerRef.current = null
    cleanupRecorder()
    setElapsedSeconds(0)
    updateUiState(
      "requesting_permission",
      "Allow microphone access to start recording."
    )

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

      stream.getAudioTracks().forEach((track) => {
        track.addEventListener("ended", () => {
          if (mediaRecorderRef.current !== recorder || recorder.state !== "recording") {
            return
          }

          stopReasonRef.current = "interrupted"
          try {
            recorder.stop()
          } catch {
            cleanupRecorder()
          }

          updateUiState("error", "Recording stopped unexpectedly. Please try again.")
        })
      })

      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      })

      recorder.addEventListener("error", () => {
        cleanupRecorder()
        updateUiState("error", "Recording stopped unexpectedly. Please try again.")
      })

      recorder.addEventListener("stop", () => {
        const stopReason = stopReasonRef.current
        const audioBlob = new Blob(chunksRef.current, {
          type: recorder.mimeType || selection.mimeType || "audio/webm",
        })

        cleanupRecorder()

        if (stopReason === "cancelled") {
          updateUiState("idle", "Recording discarded.")
          return
        }

        if (stopReason === "interrupted") {
          return
        }

        if (audioBlob.size === 0) {
          updateUiState("error", "We couldn't hear anything to transcribe. Please try again.")
          return
        }

        updateUiState("transcribing", "Turning your voice into text...")

        void uploadTranscript(audioBlob, extensionRef.current)
          .then(() => {
            updateUiState("ready", "Transcript added. You can edit it before sending.")
          })
          .catch((error) => {
            if (
              error instanceof DOMException &&
              error.name === "AbortError"
            ) {
              return
            }

            updateUiState(
              "error",
              error instanceof Error
                ? error.message
                : "We couldn't turn that recording into text. Please try again."
            )
          })
      })

      recorder.start()
      updateUiState("recording", "Listening now. Tap again when you're ready to stop.")
    } catch (error) {
      uploadAbortControllerRef.current = null
      cleanupRecorder()
      updateUiState("error", buildMicrophoneError(error))
    }
  }

  function stopRecording() {
    const recorder = mediaRecorderRef.current
    if (!recorder || recorder.state !== "recording") {
      return
    }

    updateUiState("stopping", "Finishing your recording...")
    recorder.stop()
  }

  function cancelRecording() {
    const recorder = mediaRecorderRef.current
    if (!recorder || recorder.state !== "recording") {
      cleanupRecorder()
      updateUiState("idle", null)
      setElapsedSeconds(0)
      return
    }

    stopReasonRef.current = "cancelled"
    chunksRef.current = []
    setElapsedSeconds(0)
    recorder.stop()
  }

  function handleMicClick() {
    if (recorderState === "recording") {
      stopRecording()
      return
    }

    void startRecording()
  }

  const isRecording = recorderState === "recording"
  const isBusy =
    recorderState === "requesting_permission" ||
    recorderState === "stopping" ||
    recorderState === "transcribing"
  const stateLabel =
    recorderState === "requesting_permission"
      ? "Microphone"
      : recorderState === "recording"
        ? "Recording"
        : recorderState === "stopping"
          ? "Finishing"
          : recorderState === "transcribing"
            ? "Transcribing"
            : recorderState === "ready"
              ? "Transcript ready"
              : recorderState === "error"
                ? "Try again"
                : "Speak"

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        onClick={handleMicClick}
        disabled={disabled || isBusy}
        className={`inline-flex items-center gap-2 rounded-full px-4 py-2.5 text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${
          isRecording
            ? "bg-[#D96C5F] text-white hover:bg-[#c85e52]"
            : "border border-white/50 bg-white/62 text-[#2F3E36] hover:bg-white/82"
        }`}
      >
        <HugeiconsIcon
          icon={isRecording ? StopCircleIcon : Mic01Icon}
          size={18}
          strokeWidth={1.8}
        />
        <span>
          {isRecording
            ? `Stop recording ${formatElapsed(elapsedSeconds)}`
            : recorderState === "requesting_permission"
              ? "Waiting for mic..."
              : recorderState === "stopping"
                ? "Finishing..."
                : recorderState === "transcribing"
              ? "Transcribing..."
              : recorderState === "ready"
                ? "Record again"
                : recorderState === "error"
                  ? "Try again"
                  : "Speak instead"}
        </span>
      </button>

      {isRecording ? (
        <button
          type="button"
          onClick={cancelRecording}
          className="rounded-full bg-white/62 px-4 py-2.5 text-sm text-[#2F3E36]/72 transition-colors hover:bg-white/82"
        >
          Cancel
        </button>
      ) : null}

      {statusMessage ? (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span
            className={`rounded-full px-2.5 py-1 text-[0.68rem] uppercase tracking-[0.14em] ${
              recorderState === "error"
                ? "bg-[#F7E9E2] text-[#8b4e3d]"
                : "bg-white/70 text-[#6A8375]"
            }`}
          >
            {stateLabel}
          </span>
          <span
            className={`${
            recorderState === "error" ? "text-[#8b4e3d]" : "text-[#2F3E36]/58"
            }`}
          >
            {statusMessage}
          </span>
        </div>
      ) : null}
    </div>
  )
}
