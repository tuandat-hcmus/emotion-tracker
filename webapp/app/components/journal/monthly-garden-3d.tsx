/**
 * MonthlyGarden3D — 3D visualization for the monthly recap.
 *
 * 31 plant pots arranged in a circle using @react-three/fiber.
 * Each pot represents one day:  emotion → color,  intensity → plant size.
 * Day 1 has a small flag. Center shows the month number.
 */
import { Canvas, useFrame } from "@react-three/fiber"
import { useRef } from "react"
import * as THREE from "three"

// ─── Types ────────────────────────────────────────────────────────────────────

export type GardenDay = {
  day: number       // 1–31
  emotion: string   // primary emotion label
  intensity: number // 0–1
  hasEntry: boolean
}

type Props = {
  days: GardenDay[]
  monthNumber: number // 1–12
  className?: string
}

// ─── Emotion → color ──────────────────────────────────────────────────────────

const EMOTION_COLORS: Record<string, string> = {
  joy: "#F4C95D",
  happiness: "#F4C95D",
  happy: "#F4C95D",
  gratitude: "#F6A04B",
  pride: "#E88C4A",
  calm: "#A8C3D8",
  relief: "#B8D4C8",
  hope: "#7FC0B0",
  sadness: "#8BB4C8",
  loneliness: "#9AA8C0",
  emptiness: "#B4BED4",
  anxiety: "#C5A4C8",
  overwhelm: "#D4829A",
  anger: "#E87070",
  exhaustion: "#C8B4A0",
  neutral: "#A8C3A8",
  fear: "#C2A4C5",
}

function emotionHex(emotion: string): string {
  return EMOTION_COLORS[emotion.toLowerCase()] ?? EMOTION_COLORS.neutral
}

// ─── Individual pot ───────────────────────────────────────────────────────────

function Pot({
  position,
  rotationY,
  color,
  intensity,
  isEmpty,
  isDay1,
}: {
  position: [number, number, number]
  rotationY: number
  color: string
  intensity: number
  isEmpty: boolean
  isDay1: boolean
}) {
  const plantScale = isEmpty ? 0 : 0.75 + intensity * 0.65
  const stemScale = isEmpty ? 0 : 0.7 + intensity * 0.7

  return (
    <group position={position} rotation={[0, rotationY, 0]}>
      {/* Pot body */}
      <mesh position={[0, 0.175, 0]} castShadow>
        <cylinderGeometry args={[0.18, 0.22, 0.35, 16]} />
        <meshPhongMaterial color={isEmpty ? "#d0c4b4" : "#d4a57a"} opacity={isEmpty ? 0.5 : 1} transparent />
      </mesh>

      {/* Pot rim */}
      <mesh position={[0, 0.35, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.19, 0.036, 8, 24]} />
        <meshPhongMaterial color={isEmpty ? "#c0b4a0" : "#be9060"} opacity={isEmpty ? 0.5 : 1} transparent />
      </mesh>

      {/* Soil */}
      {!isEmpty && (
        <mesh position={[0, 0.37, 0]}>
          <cylinderGeometry args={[0.17, 0.17, 0.04, 16]} />
          <meshPhongMaterial color="#7a5c3a" />
        </mesh>
      )}

      {/* Stem */}
      {!isEmpty && (
        <mesh position={[0, 0.54, 0]} scale={[1, stemScale, 1]}>
          <cylinderGeometry args={[0.026, 0.032, 0.3, 8]} />
          <meshPhongMaterial color="#5a8a50" />
        </mesh>
      )}

      {/* Leaf / plant head */}
      {!isEmpty && (
        <mesh position={[0, 0.72, 0]} scale={plantScale}>
          <sphereGeometry args={[0.14, 12, 8]} />
          <meshPhongMaterial color={color} shininess={40} transparent opacity={0.92} />
        </mesh>
      )}

      {/* Day 1 flag */}
      {isDay1 && (
        <group>
          {/* Pole */}
          <mesh position={[0, 0.55, 0]}>
            <cylinderGeometry args={[0.012, 0.012, 0.55, 6]} />
            <meshPhongMaterial color="#ffffff" shininess={60} />
          </mesh>
          {/* Flag triangle */}
          <mesh position={[0.11, 0.76, 0]}>
            <planeGeometry args={[0.22, 0.13]} />
            <meshPhongMaterial color="#12c77f" side={THREE.DoubleSide} />
          </mesh>
        </group>
      )}
    </group>
  )
}

// ─── Rotating scene ───────────────────────────────────────────────────────────

function Garden({ days, monthNumber }: { days: GardenDay[]; monthNumber: number }) {
  const groupRef = useRef<THREE.Group>(null!)

  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.rotation.y += 0.003
    }
  })

  const RING_RADIUS = 3.8
  const TOTAL = 31

  // Canvas texture for month number
  const canvas = document.createElement("canvas")
  canvas.width = 256
  canvas.height = 256
  const ctx = canvas.getContext("2d")
  if (ctx) {
    ctx.clearRect(0, 0, 256, 256)
    ctx.fillStyle = "#163D33"
    ctx.font = "bold 160px Georgia, serif"
    ctx.textAlign = "center"
    ctx.textBaseline = "middle"
    ctx.fillText(String(monthNumber), 128, 128)
  }
  const monthTex = new THREE.CanvasTexture(canvas)

  const FLOWER_COLORS = ["#f4c95d", "#f6a04b", "#d4829a", "#a8c3d8", "#c5a4c8", "#7fc0b0"]

  return (
    <group ref={groupRef}>
      {/* Ground circle */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
        <circleGeometry args={[RING_RADIUS + 0.6, 64]} />
        <meshPhongMaterial color="#dff3e8" />
      </mesh>

      {/* Center platform */}
      <mesh position={[0, 0.04, 0]}>
        <cylinderGeometry args={[0.72, 0.72, 0.08, 40]} />
        <meshPhongMaterial color="#c8ead8" />
      </mesh>

      {/* Center month number */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.12, 0]}>
        <planeGeometry args={[0.9, 0.9]} />
        <meshBasicMaterial map={monthTex} transparent />
      </mesh>

      {/* Mini flowers around center */}
      {FLOWER_COLORS.map((fc, i) => {
        const a = (i / 6) * Math.PI * 2
        return (
          <mesh key={`f${i}`} position={[Math.cos(a) * 0.43, 0.12, Math.sin(a) * 0.43]}>
            <sphereGeometry args={[0.07, 8, 6]} />
            <meshPhongMaterial color={fc} shininess={50} />
          </mesh>
        )
      })}

      {/* Pots */}
      {Array.from({ length: TOTAL }, (_, i) => {
        const d = i + 1
        const angle = (i / TOTAL) * Math.PI * 2 - Math.PI / 2
        const x = Math.cos(angle) * RING_RADIUS
        const z = Math.sin(angle) * RING_RADIUS
        const rotY = -angle + Math.PI / 2

        const dayData = days.find((item) => item.day === d)
        const isEmpty = !dayData?.hasEntry
        const color = dayData ? emotionHex(dayData.emotion) : "#a8c3a8"
        const intensity = dayData?.intensity ?? 0.5

        return (
          <Pot
            key={d}
            position={[x, 0, z]}
            rotationY={rotY}
            color={color}
            intensity={intensity}
            isEmpty={isEmpty}
            isDay1={d === 1}
          />
        )
      })}
    </group>
  )
}

// ─── Exported component ───────────────────────────────────────────────────────

export function MonthlyGarden3D({ days, monthNumber, className }: Props) {
  return (
    <div className={className} style={{ width: "100%", height: "100%" }}>
      <Canvas
        camera={{ position: [0, 5.5, 7.5], fov: 52 }}
        shadows
        gl={{ antialias: true }}
        style={{ background: "#0a1a12" }}
      >
        <fog attach="fog" args={["#0a1a12", 8, 22]} />
        <ambientLight intensity={0.7} />
        <directionalLight
          position={[4, 8, 4]}
          intensity={1.4}
          castShadow
          shadow-mapSize={[1024, 1024]}
          color="#fff5e0"
        />
        <pointLight position={[-4, 3, -4]} intensity={0.5} distance={20} color="#a8c3d8" />

        <Garden days={days} monthNumber={monthNumber} />
      </Canvas>
    </div>
  )
}
