import { useEffect, useRef, useState } from "react"
import { api, getWebSocketBaseUrl } from "~/lib/api"
import type { MultimodalSessionResponse } from "~/lib/contracts"

interface MultimodalCaptureProps {
  token: string | null
  onSessionCreated?: (sessionId: string) => void
  onFaceEmotion?: (label: string, confidence: number) => void
  onVoiceEmotion?: (label: string) => void
}

export function MultimodalCapture({
  token,
  onSessionCreated,
  onFaceEmotion,
  onVoiceEmotion,
}: MultimodalCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const videoStreamRef = useRef<MediaStream | null>(null)
  const frameIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)

  const [faceLabel, setFaceLabel] = useState<string | null>(null)
  const [faceConfidence, setFaceConfidence] = useState(0)
  const [voiceLabel, setVoiceLabel] = useState<string | null>(null)
  const [isReady, setIsReady] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessingVoice, setIsProcessingVoice] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return

    let cancelled = false

    async function init() {
      try {
        // 1. Create multimodal session
        let session: MultimodalSessionResponse
        try {
          session = await api.createMultimodalSession(token!)
        } catch {
          if (!cancelled) setError("Could not start multimodal session.")
          return
        }
        if (cancelled) return

        onSessionCreated?.(session.session_id)

        // 2. Open WebSocket
        const wsBase = getWebSocketBaseUrl()
        const ws = new WebSocket(
          `${wsBase}/v1/multimodal/ws/${session.session_id}?token=${token}`
        )
        wsRef.current = ws

        ws.onmessage = (ev) => {
          try {
            const msg = JSON.parse(ev.data as string)
            if (msg.type === "face_emotion" && msg.face_detected) {
              setFaceLabel(String(msg.label))
              setFaceConfidence(Number(msg.confidence))
              onFaceEmotion?.(String(msg.label), Number(msg.confidence))
            }
            if (msg.type === "voice_emotion") {
              setVoiceLabel(String(msg.label))
              setIsProcessingVoice(false)
              onVoiceEmotion?.(String(msg.label))
            }
            if (msg.type === "error") {
              setIsProcessingVoice(false)
            }
          } catch {
            // ignore malformed messages
          }
        }

        // 3. Start webcam (video only)
        let videoStream: MediaStream
        try {
          videoStream = await navigator.mediaDevices.getUserMedia({
            video: { width: 320, height: 240, facingMode: "user" },
            audio: false,
          })
        } catch {
          if (!cancelled) setError("Camera permission denied.")
          ws.close()
          return
        }
        if (cancelled) {
          videoStream.getTracks().forEach((t) => t.stop())
          ws.close()
          return
        }

        videoStreamRef.current = videoStream
        if (videoRef.current) videoRef.current.srcObject = videoStream

        // 4. Send frames at 2 fps
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

        if (!cancelled) setIsReady(true)
      } catch (err) {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to start camera")
      }
    }

    void init()

    return () => {
      cancelled = true
      if (frameIntervalRef.current) { clearInterval(frameIntervalRef.current); frameIntervalRef.current = null }
      if (videoStreamRef.current) { videoStreamRef.current.getTracks().forEach((t) => t.stop()); videoStreamRef.current = null }
      if (wsRef.current) { wsRef.current.close(); wsRef.current = null }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop()
      }
    }
  }, [token]) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleStartRecording() {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return

    let audioStream: MediaStream
    try {
      audioStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      setError("Microphone permission denied.")
      return
    }

    const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/ogg"
    const recorder = new MediaRecorder(audioStream, { mimeType })
    mediaRecorderRef.current = recorder

    recorder.ondataavailable = (e) => {
      if (e.data.size === 0 || ws.readyState !== WebSocket.OPEN) return
      const reader = new FileReader()
      reader.onloadend = () => {
        const base64 = (reader.result as string).split(",")[1]
        if (base64) ws.send(JSON.stringify({ type: "audio_chunk", chunk: base64, extension: ".webm" }))
      }
      reader.readAsDataURL(e.data)
    }

    recorder.onstop = () => {
      audioStream.getTracks().forEach((t) => t.stop())
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "audio_final", extension: ".webm" }))
        setIsProcessingVoice(true)
      }
      setIsRecording(false)
    }

    recorder.start(250) // chunk every 250ms
    setIsRecording(true)
  }

  function handleStopRecording() {
    mediaRecorderRef.current?.stop()
  }

  return (
    <div className="mt-4 rounded-[1.35rem] border border-[#DDF5EA] bg-[#F8FFFC] p-4">
      <div className="flex items-start gap-4">
        {/* Webcam preview */}
        <div className="relative shrink-0">
          <video
            ref={videoRef}
            autoPlay
            muted
            playsInline
            className="h-28 w-36 rounded-[0.75rem] bg-[#E7FFF4] object-cover"
          />
          <canvas ref={canvasRef} className="hidden" />
          {faceLabel && (
            <div className="absolute bottom-1 left-1 rounded-full bg-black/50 px-2 py-0.5 text-[10px] text-white capitalize">
              {faceLabel} {Math.round(faceConfidence * 100)}%
            </div>
          )}
          {!isReady && !error && (
            <div className="absolute inset-0 flex items-center justify-center rounded-[0.75rem] bg-[#E7FFF4]">
              <span className="text-xs text-[#648078]">Starting…</span>
            </div>
          )}
        </div>

        {/* Controls + detected emotions */}
        <div className="flex flex-1 flex-col gap-2">
          <p className="text-sm font-medium text-[#163D33]">Live emotion detection</p>

          {error ? (
            <p className="text-xs text-[#A34F38]">{error}</p>
          ) : (
            <>
              {/* Detected emotion pills */}
              <div className="flex flex-wrap gap-2">
                {faceLabel && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs text-[#648078]">Face:</span>
                    <span className="rounded-full bg-[var(--brand-primary-soft)] px-2 py-0.5 text-xs text-[var(--brand-primary-muted)] capitalize">
                      {faceLabel}
                    </span>
                  </div>
                )}
                {voiceLabel && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs text-[#648078]">Voice:</span>
                    <span className="rounded-full bg-[var(--brand-primary-soft)] px-2 py-0.5 text-xs text-[var(--brand-primary-muted)] capitalize">
                      {voiceLabel}
                    </span>
                  </div>
                )}
                {!faceLabel && !voiceLabel && isReady && !isProcessingVoice && (
                  <p className="text-xs text-[#648078]">Waiting for detection…</p>
                )}
                {isProcessingVoice && (
                  <p className="text-xs text-[#648078]">Analyzing voice…</p>
                )}
              </div>

              {/* Voice record button */}
              {isReady && (
                <button
                  type="button"
                  onClick={isRecording ? handleStopRecording : handleStartRecording}
                  disabled={isProcessingVoice}
                  className={`mt-1 inline-flex w-fit items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${
                    isRecording
                      ? "border-red-300 bg-red-50 text-red-600 hover:bg-red-100"
                      : "border-[#DDF5EA] bg-white text-[#648078] hover:bg-[#F0FFF7]"
                  }`}
                >
                  {/* mic icon */}
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    <line x1="12" y1="19" x2="12" y2="23" />
                    <line x1="8" y1="23" x2="16" y2="23" />
                  </svg>
                  {isRecording ? "Stop recording" : "Analyze voice"}
                </button>
              )}
            </>
          )}

          <p className="text-xs text-[#648078]">
            Camera detects facial expression in real time. Press "Analyze voice" to detect emotion from speech.
          </p>
        </div>
      </div>
    </div>
  )
}
