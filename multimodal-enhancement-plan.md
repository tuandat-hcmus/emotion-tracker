# Multimodal Emotion Detection — Enhancement Plan

> Senior AI/Data Engineer review of `emotion-tracker` codebase + `emotion-tracker.md`.
> Addresses all requirements in `prompt.txt`.

---

## 1. Executive Summary

The existing system already has a solid foundation:
- **Text emotion**: XLM-RoBERTa (7-label canonical schema) — keep as-is
- **STT**: OpenAI Whisper — reuse
- **WebSocket streaming**: `/v1/conversations/ws` — reuse pattern

What we are adding:
- **Face emotion**: Real-time webcam frame analysis via a SOTA vision model
- **Audio prosody emotion**: Wav2Vec2-based audio emotion on raw audio (parallel to text)
- **Fusion layer**: Reciprocal Rank Fusion (RRF) combining all three modalities
- **New API**: `/v1/multimodal/*` router with REST + WebSocket
- **Minimal UI addition**: Webcam strip + emotion result panel inside `/app/journal`

---

## 2. Updated Architecture

```
FRONTEND (/app/journal — extended)
┌────────────────────────────────────────────────────────┐
│  [Existing UI: text area, voice record button]          │
│                                                         │
│  [NEW] MultimodalCapture component                      │
│    ├── WebcamFeed (canvas, 2 fps frame capture)         │
│    ├── MicCapture (MediaRecorder, reuses existing)      │
│    └── EmotionOverlay (live face + voice + fused bars)  │
│                                                         │
│  WebSocket → /v1/multimodal/ws/{session_id}             │
│    send: { type:"frame", data:"base64jpeg" }            │
│    send: { type:"audio_chunk", data:"base64webm" }      │
│    send: { type:"audio_final" }                         │
│    recv: { type:"face_emotion", scores:{...} }          │
│    recv: { type:"voice_emotion", scores:{...} }         │
│    recv: { type:"fused_emotion", label, scores, conf }  │
└────────────────────────────────────────────────────────┘
                        │ WebSocket + REST
                        ▼
BACKEND (new router: backend/app/api/multimodal.py)
┌────────────────────────────────────────────────────────┐
│  /v1/multimodal/                                        │
│    POST  /sessions          → create session            │
│    POST  /frame             → analyze single frame      │
│    POST  /sessions/{id}/end → finalize + fuse + save   │
│    WS    /ws/{session_id}   → real-time stream          │
│                                                         │
│  Service Layer (new files):                             │
│    face_emotion_service.py  ← ViT/DeepFace model       │
│    audio_emotion_service.py ← Wav2Vec2 model           │
│    fusion_service_mm.py     ← RRF fusion                │
│    multimodal_session.py    ← session state mgmt       │
│                                                         │
│  Existing services reused:                              │
│    text_emotion_service.py  ← XLM-RoBERTa (unchanged)  │
│    stt_service.py           ← Whisper (unchanged)       │
│    checkin_processing_service.py (extended)             │
└────────────────────────────────────────────────────────┘
                        │
                        ▼
              PostgreSQL (1 new table + 1 new column)
```

---

## 3. Recommended SOTA Models & Libraries

### 3a. Face Emotion Recognition

| Option | Model | Accuracy | Latency | Notes |
|---|---|---|---|---|
| **Recommended** | `trpakov/vit-face-expression` (HuggingFace) | ~92% FER2013 | ~80ms GPU / ~300ms CPU | ViT-base, same HF pipeline as existing XLM-RoBERTa |
| Alternative | `deepface` library (VGGFace2 + emotion classifier) | ~88% | ~150ms CPU | Easy install, no GPU required, wraps multiple backends |
| Lightweight | `fer` library (Mini-Xception on FER2013) | ~72% | ~30ms CPU | Best for low-resource deployment |

**Decision**: Use `deepface` for CPU-friendly deployment with optional ViT upgrade. `deepface` outputs the same 7 labels: angry, disgust, fear, happy, sad, surprise, neutral.

Label mapping to canonical schema: `happy → joy`, rest unchanged.

```python
# backend/app/services/face_emotion_service.py
from deepface import DeepFace
import numpy as np
import base64, cv2

LABEL_MAP = {"happy": "joy", "angry": "anger"}  # normalize to canonical

class FaceEmotionService:
    def analyze_frame(self, image_b64: str) -> dict | None:
        """Returns {label: str, scores: dict[str, float], confidence: float} or None if no face."""
        img_bytes = base64.b64decode(image_b64)
        img_array = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)

        try:
            result = DeepFace.analyze(
                img_path=img_array,
                actions=["emotion"],
                enforce_detection=True,
                detector_backend="opencv",  # fast; switch to "retinaface" for accuracy
                silent=True,
            )
            emotions: dict = result[0]["emotion"]  # {angry: 12.3, happy: 67.1, ...}
            # normalize keys
            normalized = {LABEL_MAP.get(k, k): v / 100.0 for k, v in emotions.items()}
            top_label = max(normalized, key=normalized.get)
            return {
                "label": top_label,
                "scores": normalized,
                "confidence": normalized[top_label],
            }
        except Exception:
            return None  # no face detected or error
```

### 3b. Audio (Prosody) Emotion Recognition

| Option | Model | Labels | Notes |
|---|---|---|---|
| **Recommended** | `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim` | dimensional (valence/arousal/dominance) | Maps to canonical via thresholds |
| Alternative | `speechbrain/emotion-recognition-wav2vec2-IEMOCAP` | 4-class (angry/happy/neutral/sad) | Simpler, faster |
| Fallback | Reuse text emotion from Whisper transcript | 7-class | Already implemented, zero new cost |

**Decision**: Use `speechbrain` IEMOCAP model for 4-class audio emotion; merge with existing text emotion (which covers 7 classes). Audio emotion provides prosody signal; text emotion provides semantic signal. Both feed RRF.

```python
# backend/app/services/audio_emotion_service.py
from speechbrain.inference.interfaces import foreign_class

IEMOCAP_TO_CANONICAL = {
    "ang": "anger", "hap": "joy", "neu": "neutral", "sad": "sadness"
}

class AudioEmotionService:
    def __init__(self):
        self.classifier = foreign_class(
            source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
            pymodule_file="custom_interface.py",
            classname="CustomEncoderWav2vec2Classifier",
            savedir="pretrained_models/emotion-recognition-wav2vec2-IEMOCAP",
        )

    def analyze_audio(self, audio_path: str) -> dict:
        """Returns {label: str, scores: dict[str, float], confidence: float}"""
        out_prob, score, index, text_lab = self.classifier.classify_file(audio_path)
        label_raw = text_lab[0]
        label = IEMOCAP_TO_CANONICAL.get(label_raw, "neutral")
        # build sparse scores (only 4 classes known)
        scores = {IEMOCAP_TO_CANONICAL.get(l, l): float(p) for l, p in zip(
            ["ang", "hap", "neu", "sad"], out_prob[0].tolist()
        )}
        return {"label": label, "scores": scores, "confidence": float(score)}
```

### 3c. Text Emotion (existing — no change)

`XLM-RoBERTa` fine-tuned for 7-label emotion via `local_emotion_model_service.py`. Already handles Vietnamese + English. **Do not modify.**

---

## 4. Emotion Fusion — Reciprocal Rank Fusion (RRF)

### Algorithm

RRF aggregates ranked lists from multiple sources. For each emotion label, compute:

```
RRF_score(emotion, modality) = 1 / (k + rank(emotion, modality))
Final_score(emotion) = Σ over all modalities: RRF_score(emotion, modality)
```

Where `k = 60` (standard constant — prevents top-ranked items from dominating).

### Implementation

```python
# backend/app/services/fusion_service_mm.py

CANONICAL_LABELS = ["anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral"]
K = 60

def reciprocal_rank_fusion(
    modality_scores: list[dict[str, float]],
    modality_weights: list[float] | None = None,
) -> dict:
    """
    Args:
        modality_scores: list of {emotion_label: score} dicts, one per modality.
                         Scores must be non-negative (confidence or probability).
                         A modality can have sparse scores (only known labels).
        modality_weights: optional weight per modality (default: equal weights).
    Returns:
        {
            "label": str,              # top emotion
            "scores": dict[str,float], # normalized final scores
            "confidence": float,       # score of top emotion
            "modality_contributions": list[str],  # which modalities contributed
        }
    """
    if not modality_scores:
        return {"label": "neutral", "scores": {}, "confidence": 0.0, "modality_contributions": []}

    if modality_weights is None:
        modality_weights = [1.0] * len(modality_scores)

    # Normalize weights
    total_w = sum(modality_weights)
    modality_weights = [w / total_w for w in modality_weights]

    rrf_totals: dict[str, float] = {label: 0.0 for label in CANONICAL_LABELS}
    contributions = []

    for scores, weight in zip(modality_scores, modality_weights):
        if not scores:
            continue
        contributions.append(True)
        # Fill missing canonical labels with 0
        full_scores = {label: scores.get(label, 0.0) for label in CANONICAL_LABELS}
        # Rank: highest score = rank 1
        ranked = sorted(full_scores.items(), key=lambda x: x[1], reverse=True)
        for rank_idx, (label, _) in enumerate(ranked, start=1):
            rrf_totals[label] += weight * (1.0 / (K + rank_idx))

    # Normalize to sum=1
    total = sum(rrf_totals.values()) or 1.0
    normalized = {label: score / total for label, score in rrf_totals.items()}
    top_label = max(normalized, key=normalized.get)

    return {
        "label": top_label,
        "scores": normalized,
        "confidence": normalized[top_label],
        "modality_contributions": ["face", "audio", "text"][: len(contributions)],
    }


def fuse_multimodal(
    face_result: dict | None,     # from FaceEmotionService
    audio_result: dict | None,    # from AudioEmotionService
    text_result: dict | None,     # from local_emotion_model_service
) -> dict:
    """Convenience wrapper with default modality weights: face=0.35, audio=0.30, text=0.35"""
    modality_scores = []
    weights = []
    modality_names = []

    if face_result and face_result.get("scores"):
        modality_scores.append(face_result["scores"])
        weights.append(0.35)
        modality_names.append("face")

    if audio_result and audio_result.get("scores"):
        modality_scores.append(audio_result["scores"])
        weights.append(0.30)
        modality_names.append("audio")

    if text_result and text_result.get("scores"):
        modality_scores.append(text_result["scores"])
        weights.append(0.35)
        modality_names.append("text")

    result = reciprocal_rank_fusion(modality_scores, weights)
    result["modality_contributions"] = modality_names
    return result
```

### Example Fusion

| Emotion | Face Score | Audio Score | Text Score | Face Rank | Audio Rank | Text Rank | RRF Total |
|---|---|---|---|---|---|---|---|
| joy | 0.68 | 0.10 | 0.55 | 1 | 5 | 1 | 1/61 + 1/65 + 1/61 = 0.0479 |
| neutral | 0.15 | 0.45 | 0.20 | 3 | 1 | 3 | 1/63 + 1/61 + 1/63 = 0.0480 |
| sadness | 0.05 | 0.30 | 0.18 | 6 | 2 | 4 | 1/66 + 1/62 + 1/64 = 0.0470 |

In this case **neutral** wins despite lower raw scores, because it ranked highly in audio (prosody was calm). This is RRF's key benefit: prevents any single modality from dominating.

---

## 5. New Backend API Design

### New Router: `backend/app/api/multimodal.py`

Register in `main.py`:
```python
from app.api import multimodal
app.include_router(multimodal.router, prefix="/v1/multimodal", tags=["multimodal"])
```

---

#### `POST /v1/multimodal/sessions`

Start a multimodal check-in session.

```
Request: {}  (no body, uses JWT auth)

Response 201:
{
  "session_id": "uuid",
  "status": "active",
  "started_at": "2026-03-29T10:00:00Z"
}
```

---

#### `POST /v1/multimodal/frame`

Analyze a single webcam frame on demand (REST, no WebSocket needed for still analysis).

```
Request:
{
  "image_b64": "string",       // base64-encoded JPEG
  "session_id": "uuid | null"  // optional — associate with session
}

Response 200:
{
  "face_detected": true,
  "label": "joy",
  "confidence": 0.72,
  "scores": {
    "anger": 0.03,
    "disgust": 0.01,
    "fear": 0.02,
    "joy": 0.72,
    "sadness": 0.04,
    "surprise": 0.12,
    "neutral": 0.06
  },
  "processing_ms": 145
}

Response 200 (no face):
{
  "face_detected": false,
  "label": null,
  "confidence": 0.0,
  "scores": {}
}
```

---

#### `POST /v1/multimodal/sessions/{session_id}/end`

Finalize session: run audio emotion + text emotion on accumulated data → fuse → save as JournalEntry.

```
Request:
{
  "transcript_override": "string | null"
}

Response 200:
{
  "entry_id": "uuid",
  "fused_emotion": {
    "label": "joy",
    "confidence": 0.68,
    "scores": { ... },
    "modality_contributions": ["face", "audio", "text"]
  },
  "face_summary": { "label": "joy", "confidence": 0.71, "frame_count": 24 },
  "audio_summary": { "label": "neutral", "confidence": 0.45 },
  "text_summary": { "label": "joy", "confidence": 0.62 },
  "ai_response": "...",         // empathetic response from existing pipeline
  "gentle_suggestion": "..."
}
```

---

#### `WebSocket /v1/multimodal/ws/{session_id}`

Real-time stream for live feedback during check-in.

**Client → Server messages:**

```jsonc
// Send webcam frame (2 fps recommended)
{ "type": "frame", "data": "base64jpeg_string" }

// Send audio chunk (same format as existing conversation WS)
{ "type": "audio_chunk", "chunk": "base64_webm", "extension": ".webm" }

// Signal end of audio
{ "type": "audio_final" }

// Send transcribed text (from browser Web Speech API fallback)
{ "type": "user_text", "text": "I'm feeling really anxious today" }
```

**Server → Client messages:**

```jsonc
// Face emotion result per frame
{
  "type": "face_emotion",
  "face_detected": true,
  "label": "joy",
  "confidence": 0.72,
  "scores": { "joy": 0.72, "neutral": 0.15, ... }
}

// Audio/voice emotion (after audio_final received)
{
  "type": "voice_emotion",
  "transcript": "I'm feeling really anxious today",
  "audio_label": "neutral",        // from prosody model
  "text_label": "fear",            // from XLM-RoBERTa on transcript
  "audio_scores": { ... },
  "text_scores": { ... }
}

// Fused result (after voice_emotion computed)
{
  "type": "fused_emotion",
  "label": "fear",
  "confidence": 0.61,
  "scores": { "fear": 0.61, "neutral": 0.22, "sadness": 0.10, ... },
  "modality_contributions": ["face", "audio", "text"]
}

// Error
{ "type": "error", "message": "No face detected in last 10 seconds" }
```

---

## 6. Database Changes

### Option A: Extend `JournalEntry` (add column via Alembic migration)

```python
# Add to JournalEntry model
multimodal_metadata_text = Column(String, nullable=True)
# Stores JSON:
# {
#   "fusion_method": "rrf",
#   "face": {"label": "joy", "confidence": 0.72, "frame_count": 24},
#   "audio": {"label": "neutral", "confidence": 0.45},
#   "text": {"label": "joy", "confidence": 0.62},
#   "weights": {"face": 0.35, "audio": 0.30, "text": 0.35},
#   "session_id": "uuid"
# }
```

Migration file (`alembic/versions/006_add_multimodal.py`):
```python
def upgrade():
    op.add_column("journal_entries",
        sa.Column("multimodal_metadata_text", sa.String(), nullable=True))
```

This is non-breaking — existing entries will have `null` for this column.

### Option B: New `MultimodalSession` table (cleaner, more extensible)

```python
class MultimodalSession(Base):
    __tablename__ = "multimodal_sessions"
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"), index=True)
    entry_id = Column(UUID, ForeignKey("journal_entries.id"), nullable=True)
    status = Column(String, default="active")   # active / ended
    face_frame_count = Column(Integer, default=0)
    face_summary_text = Column(String, nullable=True)   # JSON
    audio_summary_text = Column(String, nullable=True)  # JSON
    text_summary_text = Column(String, nullable=True)   # JSON
    fused_summary_text = Column(String, nullable=True)  # JSON
    started_at = Column(DateTime)
    ended_at = Column(DateTime, nullable=True)
```

**Recommendation**: Use Option A for speed of delivery; migrate to Option B if multimodal data needs independent querying.

---

## 7. Frontend Changes (Minimal)

Only modify `webapp/app/routes/journal.tsx`. Add a `MultimodalCapture` component toggle — hidden by default, revealed when user clicks "Use Camera & Mic".

### New component: `webapp/app/components/MultimodalCapture.tsx`

Responsibilities:
- Request `getUserMedia({ video: true, audio: true })`
- Render `<video>` element (webcam feed, muted)
- Capture frame every 500ms via `<canvas>.toDataURL('image/jpeg', 0.7)`
- Send frame over WebSocket as `{ type: "frame", data: base64 }`
- Reuse existing `MediaRecorder` logic from `InteractiveVoiceModal` for audio chunks
- Listen for `face_emotion`, `voice_emotion`, `fused_emotion` WS messages
- Display live emotion bars

```tsx
// webapp/app/components/MultimodalCapture.tsx (skeleton)
import { useRef, useEffect, useState } from "react";

type EmotionScores = Record<string, number>;
interface MultimodalCaptureProps {
  sessionId: string;
  wsUrl: string;
  onFusedEmotion: (label: string, scores: EmotionScores) => void;
}

export function MultimodalCapture({ sessionId, wsUrl, onFusedEmotion }: MultimodalCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [faceEmotion, setFaceEmotion] = useState<{ label: string; confidence: number } | null>(null);
  const [fusedEmotion, setFusedEmotion] = useState<{ label: string; scores: EmotionScores } | null>(null);

  useEffect(() => {
    // 1. Open WebSocket
    wsRef.current = new WebSocket(`${wsUrl}/v1/multimodal/ws/${sessionId}`);
    wsRef.current.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === "face_emotion" && msg.face_detected) {
        setFaceEmotion({ label: msg.label, confidence: msg.confidence });
      }
      if (msg.type === "fused_emotion") {
        setFusedEmotion({ label: msg.label, scores: msg.scores });
        onFusedEmotion(msg.label, msg.scores);
      }
    };

    // 2. Start webcam
    navigator.mediaDevices.getUserMedia({ video: true, audio: false }).then((stream) => {
      if (videoRef.current) videoRef.current.srcObject = stream;
    });

    // 3. Capture frames at 2fps
    const frameInterval = setInterval(() => {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      if (!canvas || !video || wsRef.current?.readyState !== WebSocket.OPEN) return;
      canvas.width = 320;
      canvas.height = 240;
      canvas.getContext("2d")!.drawImage(video, 0, 0, 320, 240);
      const b64 = canvas.toDataURL("image/jpeg", 0.7).split(",")[1];
      wsRef.current.send(JSON.stringify({ type: "frame", data: b64 }));
    }, 500);

    return () => {
      clearInterval(frameInterval);
      wsRef.current?.close();
    };
  }, [sessionId, wsUrl]);

  return (
    <div className="flex gap-4 p-4 rounded-lg border border-border bg-card">
      {/* Webcam preview */}
      <div className="relative">
        <video ref={videoRef} autoPlay muted playsInline className="w-40 h-30 rounded object-cover" />
        <canvas ref={canvasRef} className="hidden" />
        {faceEmotion && (
          <div className="absolute bottom-1 left-1 bg-black/60 text-white text-xs px-1 rounded">
            {faceEmotion.label} {Math.round(faceEmotion.confidence * 100)}%
          </div>
        )}
      </div>

      {/* Fused emotion bars */}
      {fusedEmotion && (
        <div className="flex-1 space-y-1">
          <p className="text-xs font-medium text-muted-foreground">Fused emotion</p>
          {Object.entries(fusedEmotion.scores)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 4)
            .map(([label, score]) => (
              <div key={label} className="flex items-center gap-2">
                <span className="w-16 text-xs capitalize">{label}</span>
                <div className="flex-1 h-2 bg-muted rounded">
                  <div
                    className="h-2 bg-primary rounded transition-all duration-300"
                    style={{ width: `${Math.round(score * 100)}%` }}
                  />
                </div>
                <span className="text-xs w-8 text-right">{Math.round(score * 100)}%</span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
```

### Modify `journal.tsx` — add toggle button

Find the section with the voice recording button and add adjacent:

```tsx
{/* Existing: voice record button */}
{/* NEW: multimodal toggle */}
{isMultimodalOpen ? (
  <MultimodalCapture
    sessionId={multimodalSessionId}
    wsUrl={API_BASE_URL}
    onFusedEmotion={(label, scores) => setPreviewEmotion({ label, scores })}
  />
) : (
  <button
    onClick={handleStartMultimodal}
    className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
  >
    {/* camera icon */} Use Camera & Mic
  </button>
)}
```

No other UI changes needed. The existing "emotion preview" display in the journal page can receive the fused result via `onFusedEmotion` callback.

---

## 8. Integration Plan (Step-by-Step)

### Phase 1 — Backend Core (no frontend changes needed to test)

1. `pip install deepface speechbrain` (add to `requirements-ai.txt`)
2. Create `backend/app/services/face_emotion_service.py`
3. Create `backend/app/services/audio_emotion_service.py`
4. Create `backend/app/services/fusion_service_mm.py`
5. Create `backend/app/services/multimodal_session_service.py` (session state: stores accumulated face scores per session in memory or Redis)
6. Create `backend/app/api/multimodal.py` with REST + WebSocket endpoints
7. Register router in `main.py`
8. Write Alembic migration `006_add_multimodal.py`
9. Test via `POST /v1/multimodal/frame` with a sample base64 JPEG

### Phase 2 — Frontend Integration

1. Create `MultimodalCapture.tsx` component
2. Modify `journal.tsx` to add camera toggle button
3. Wire `onFusedEmotion` to existing emotion preview state
4. Test end-to-end: open camera → speak → see live emotion bars → submit → check journal entry

### Phase 3 — Finalization

1. Add `multimodal_metadata_text` column to `JournalEntry`
2. Persist face/audio/text/fused summaries in `multimodal_metadata_text` JSON
3. Update `CheckinDetail` Pydantic schema to include `multimodal_metadata`
4. Extend journal history display to show `🎥` indicator for multimodal entries

---

## 9. New Python Dependencies

```
# requirements-ai.txt additions
deepface>=0.0.93
speechbrain>=1.0.0
opencv-python-headless>=4.9.0   # for deepface frame decoding (no GUI)
tf-keras>=2.16.0                # deepface TF backend (or use torch backend)
```

Note: `deepface` downloads model weights on first use (~500MB). Pre-download in Docker build step:
```dockerfile
RUN python -c "from deepface import DeepFace; DeepFace.build_model('Emotion')"
```

---

## 10. Performance Considerations

| Operation | Expected latency | Mitigation |
|---|---|---|
| Face inference per frame (CPU) | 200–400ms | Run in `asyncio.to_thread()` so WS isn't blocked; cap at 2fps |
| Audio emotion (Wav2Vec2, CPU) | 500–1500ms | Run once at session end, not per chunk |
| Text emotion (XLM-RoBERTa) | 50–200ms | Already optimized; unchanged |
| RRF fusion | < 1ms | Pure Python dict ops |
| End-to-end WS round-trip | 300–500ms | Acceptable for live feedback |

For GPU deployment, face inference drops to ~30ms and audio to ~200ms.

**Frame accumulation strategy** (for session-level face summary):
```python
# Don't store all raw scores — maintain a rolling top-3 accumulator
face_accumulator = defaultdict(float)
for frame_result in session_frames:
    for label, score in frame_result["scores"].items():
        face_accumulator[label] += score
# Normalize by frame count for session-level summary
```

---

## 11. Modality Weight Tuning Guidance

The default weights `face=0.35, audio=0.30, text=0.35` are conservative starting points. Tune based on:

| Scenario | Recommended weights |
|---|---|
| User typing only (no camera/mic) | `text=1.0` — fall back to existing pipeline |
| Good lighting, clear audio | `face=0.40, audio=0.30, text=0.30` |
| Poor lighting / no face detected | Drop face modality; `audio=0.45, text=0.55` |
| Audio noisy / low confidence | Drop audio; `face=0.50, text=0.50` |

The `fuse_multimodal()` function already handles absent modalities by excluding them from RRF.

---

## 12. Summary of Changes

| Area | Change | Effort |
|---|---|---|
| Backend services | 4 new service files | Medium |
| Backend API | 1 new router file (REST + WS) | Medium |
| Database | 1 Alembic migration, 1 column | Low |
| Frontend component | 1 new component `MultimodalCapture.tsx` | Medium |
| Frontend route | ~20 lines added to `journal.tsx` | Low |
| Dependencies | 3 new Python packages | Low |
| Existing code | **No changes to existing services, models, or routes** | None |

The existing `JournalEntry`, `XLM-RoBERTa` pipeline, `Whisper STT`, and `Gemini` renderer remain completely untouched. The new multimodal path is an additive extension that feeds its fused result back into the existing check-in processing pipeline as the `emotion_label`.
