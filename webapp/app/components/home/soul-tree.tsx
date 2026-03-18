import { ContactShadows, Float, OrbitControls, Sparkles } from "@react-three/drei"
import { Canvas, useFrame } from "@react-three/fiber"
import { useMemo, useRef } from "react"
import * as THREE from "three"

import { cn } from "~/lib/utils"

export type EmotionState = "calm" | "reflective" | "stressed" | "hopeful"

type SoulTreeProps = {
  emotion?: EmotionState
  className?: string
}

const PALETTE = {
  calm: {
    main: "#7E9F8B",
    accent: "#81B29A",
    glow: "#A8C3D8",
    trunk: "#A17C5B",
    magic: "#FDFBF7",
  },
  reflective: {
    main: "#7C8FA6",
    accent: "#A8C3D8",
    glow: "#DCE6EF",
    trunk: "#8E735B",
    magic: "#EEF4F8",
  },
  stressed: {
    main: "#8A6343",
    accent: "#E07A5F",
    glow: "#5C4D43",
    trunk: "#4A3B32",
    magic: "#A17C5B",
  },
  hopeful: {
    main: "#7E9F8B",
    accent: "#C6DDB8",
    glow: "#F2D8A7",
    trunk: "#B58A63",
    magic: "#FFF5E3",
  },
} satisfies Record<
  EmotionState,
  {
    main: string
    accent: string
    glow: string
    trunk: string
    magic: string
  }
>

// Bổ sung flowerScale để điều khiển độ nở của hoa
const EMOTION_MOTION = {
  calm: { droop: 0, branchFloat: 0.8, canopyFloat: 0.7, sparkles: 18, flowerScale: 0.5 },
  reflective: { droop: 0.15, branchFloat: 0.55, canopyFloat: 0.45, sparkles: 24, flowerScale: 0 },
  stressed: { droop: 0.8, branchFloat: 0.3, canopyFloat: 0.2, sparkles: 10, flowerScale: 0 },
  hopeful: { droop: -0.08, branchFloat: 1.3, canopyFloat: 1.05, sparkles: 42, flowerScale: 1 },
} satisfies Record<
  EmotionState,
  {
    droop: number
    branchFloat: number
    canopyFloat: number
    sparkles: number
    flowerScale: number
  }
>

// --------------------------------------------------------
// COMPONENT HOA (BLOOMING FLOWER)
// --------------------------------------------------------
function Flower({
  position,
  targetScale,
  color = "#FFD1DC", // Màu cánh hoa hồng nhạt chữa lành
}: {
  position: [number, number, number]
  targetScale: number
  color?: string
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const currentScale = useRef(0)

  useFrame((_, delta) => {
    // Lerp giúp hoa nở ra hoặc tàn đi một cách từ từ
    currentScale.current = THREE.MathUtils.lerp(
      currentScale.current,
      targetScale,
      delta * 2.5
    )
    if (meshRef.current) {
      meshRef.current.scale.setScalar(currentScale.current)
    }
  })

  return (
    <mesh ref={meshRef} position={position}>
      <icosahedronGeometry args={[0.1, 0]} />
      <meshStandardMaterial color={color} flatShading roughness={0.4} />
    </mesh>
  )
}

// --------------------------------------------------------
// COMPONENT CỤM LÁ (CÓ KÈM HOA)
// --------------------------------------------------------
type FoliageProps = {
  position: [number, number, number]
  scale?: number | [number, number, number]
  colorType: "main" | "accent" | "glow"
  emotion: EmotionState
}

function FoliageCluster({ position, scale = 1, colorType, emotion }: FoliageProps) {
  const material1 = useRef<THREE.MeshStandardMaterial>(null)
  const material2 = useRef<THREE.MeshStandardMaterial>(null)
  const material3 = useRef<THREE.MeshStandardMaterial>(null)
  const targetColor = useMemo(() => new THREE.Color(), [])

  const flowerScale = EMOTION_MOTION[emotion].flowerScale

  useFrame((_, delta) => {
    targetColor.set(PALETTE[emotion][colorType])
    material1.current?.color.lerp(targetColor, delta * 2)
    material2.current?.color.lerp(targetColor, delta * 2)
    material3.current?.color.lerp(targetColor, delta * 2)
  })

  return (
    <group position={position} scale={scale}>
      {/* Các tán lá */}
      <mesh scale={[1.2, 0.7, 1.2]} position={[0, 0, 0]}>
        <dodecahedronGeometry args={[0.3, 0]} />
        <meshStandardMaterial ref={material1} flatShading roughness={0.8} />
      </mesh>
      <mesh scale={[1, 0.6, 1]} position={[-0.15, 0.05, 0.1]}>
        <dodecahedronGeometry args={[0.2, 0]} />
        <meshStandardMaterial ref={material2} flatShading roughness={0.8} />
      </mesh>
      <mesh scale={[1, 0.6, 1]} position={[0.15, -0.05, -0.1]}>
        <dodecahedronGeometry args={[0.25, 0]} />
        <meshStandardMaterial ref={material3} flatShading roughness={0.8} />
      </mesh>

      {/* Hoa mọc xen kẽ trên tán lá */}
      <Flower position={[0.25, 0.15, 0.1]} targetScale={flowerScale} color="#FFD1DC" />
      <Flower position={[-0.2, 0.1, 0.25]} targetScale={flowerScale * 0.8} color="#FFF0F5" />
      <Flower position={[0.05, 0.2, -0.2]} targetScale={flowerScale * 0.9} color="#FFB7B2" />
    </group>
  )
}

// --------------------------------------------------------
// COMPONENT CÀNH CÂY (DYNAMIC BRANCH)
// --------------------------------------------------------
type BranchProps = {
  position: [number, number, number]
  baseRotation: [number, number, number]
  scale?: number
  emotion: EmotionState
  isVisible?: boolean // Quyết định cành có mọc ra hay rụt vào
}

function Branch({ position, baseRotation, scale = 1, emotion, isVisible = true }: BranchProps) {
  const branchLength = 0.8
  const groupRef = useRef<THREE.Group>(null)
  
  // Lưu trữ tỷ lệ (scale) hiện tại của toàn bộ cụm cành
  const currentScale = useRef(isVisible ? scale : 0)

  useFrame((_, delta) => {
    if (!groupRef.current) return

    // 1. Logic Rũ cành (Droop)
    const droopAmount = EMOTION_MOTION[emotion].droop
    const targetEuler = new THREE.Euler(
      baseRotation[0] + droopAmount,
      baseRotation[1],
      baseRotation[2]
    )
    const targetQuaternion = new THREE.Quaternion().setFromEuler(targetEuler)
    groupRef.current.quaternion.slerp(targetQuaternion, delta * 2)

    // 2. Logic Mọc/Thu cành (Scale lerp)
    const targetScale = isVisible ? scale : 0
    currentScale.current = THREE.MathUtils.lerp(currentScale.current, targetScale, delta * 1.5)
    // Dùng setScalar để áp dụng tỷ lệ cho cả trục X, Y, Z
    groupRef.current.scale.setScalar(currentScale.current)
  })

  return (
    // Xóa thuộc tính scale={scale} ở thẻ group vì ta đã quản lý nó bằng ref ở useFrame
    <group ref={groupRef} position={position}>
      <mesh position={[0, branchLength / 2, 0]}>
        <cylinderGeometry args={[0.015, 0.05, branchLength, 5]} />
        <meshStandardMaterial color={PALETTE[emotion].trunk} flatShading roughness={0.9} />
      </mesh>
      <Float
        speed={EMOTION_MOTION[emotion].branchFloat}
        rotationIntensity={0.15}
        floatIntensity={0.4}
      >
        <group position={[0, branchLength, 0]}>
          <FoliageCluster position={[0, 0, 0]} scale={1.2} colorType="main" emotion={emotion} />
          <FoliageCluster position={[0.1, 0.1, 0.1]} scale={0.7} colorType="glow" emotion={emotion} />
        </group>
      </Float>
    </group>
  )
}

// --------------------------------------------------------
// COMPONENT RỤNG LÁ
// --------------------------------------------------------
function FallingLeaves({ active }: { active: boolean }) {
  const groupRef = useRef<THREE.Group>(null)
  const leafConfigs = useMemo(
    () =>
      Array.from({ length: 15 }, () => ({
        origin: new THREE.Vector3(
          (Math.random() - 0.5) * 1.2,
          1.25 + Math.random() * 1.1,
          (Math.random() - 0.5) * 1
        ),
        settleX: (Math.random() - 0.5) * 1.5,
        settleZ: (Math.random() - 0.5) * 1.2,
        sway: 0.12 + Math.random() * 0.12,
        fallSpeed: 0.7 + Math.random() * 0.35,
        spinX: 1.2 + Math.random() * 1.6,
        spinZ: 0.9 + Math.random() * 1.3,
        delay: Math.random() * 2.4,
        scale: 0.08 + Math.random() * 0.08,
      })),
    []
  )

  useFrame((state, delta) => {
    if (!groupRef.current) return

    groupRef.current.children.forEach((leaf, index) => {
      const config = leafConfigs[index]

      if (!config) return

      if (!active) {
        leaf.visible = false
        return
      }

      leaf.visible = true

      const cycle = 3.6
      const fallWindow = 2.45
      const elapsed =
        (state.clock.elapsedTime * config.fallSpeed + config.delay) % cycle
      const progress = Math.min(elapsed / fallWindow, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      const windOffset =
        Math.sin(state.clock.elapsedTime * 2.4 + config.delay) * config.sway
      const flutter = Math.sin(state.clock.elapsedTime * 5.2 + index) * 0.05

      leaf.position.x =
        config.origin.x + config.settleX * eased + windOffset * (1 - eased * 0.35)
      leaf.position.z =
        config.origin.z +
        config.settleZ * eased +
        Math.cos(state.clock.elapsedTime * 2 + config.delay) *
          config.sway *
          0.6 +
        flutter
      leaf.position.y = THREE.MathUtils.lerp(config.origin.y, -0.92, eased)

      if (elapsed > fallWindow) {
        const settleProgress = (elapsed - fallWindow) / (cycle - fallWindow)
        leaf.position.y = THREE.MathUtils.lerp(-0.92, -0.98, settleProgress)
        leaf.rotation.x += delta * 0.4
        leaf.rotation.z += delta * 0.25
      } else {
        leaf.rotation.x += delta * config.spinX
        leaf.rotation.z += delta * config.spinZ
      }
    })
  })

  return (
    <group ref={groupRef} visible={active}>
      {leafConfigs.map((config, index) => (
        <mesh
          key={index}
          position={config.origin.toArray()}
          scale={config.scale}
        >
          <dodecahedronGeometry args={[0.5, 0]} />
          <meshStandardMaterial color="#8A6343" flatShading />
        </mesh>
      ))}
    </group>
  )
}

// --------------------------------------------------------
// COMPONENT CÂY TỔNG
// --------------------------------------------------------
function Tree({ emotion }: { emotion: EmotionState }) {
  const trunkMaterial = useRef<THREE.MeshStandardMaterial>(null)
  const targetTrunkColor = useMemo(() => new THREE.Color(), [])

  useFrame((_, delta) => {
    targetTrunkColor.set(PALETTE[emotion].trunk)
    trunkMaterial.current?.color.lerp(targetTrunkColor, delta * 2)
  })

  return (
    <group position={[0, -1, 0]}>
      {/* Thân cây chính */}
      <mesh position={[0, 0.75, 0]}>
        <cylinderGeometry args={[0.08, 0.25, 1.5, 6]} />
        <meshStandardMaterial ref={trunkMaterial} flatShading roughness={1} />
      </mesh>

      {/* Tán lá trên cùng */}
      <Float speed={EMOTION_MOTION[emotion].canopyFloat} rotationIntensity={0.1} floatIntensity={0.2}>
        <group position={[0, 1.6, 0]}>
          <FoliageCluster position={[0, 0, 0]} scale={2.2} colorType="main" emotion={emotion} />
          <FoliageCluster position={[0, 0.3, 0]} scale={1.5} colorType="accent" emotion={emotion} />
          <FoliageCluster position={[0.2, 0.1, 0.2]} scale={1.2} colorType="glow" emotion={emotion} />
        </group>
      </Float>

      {/* --- CÁC CÀNH CỐ ĐỊNH (Luôn mọc) --- */}
      <Branch position={[0.15, 0.4, 0]} baseRotation={[0, 0, -1.2]} scale={0.9} emotion={emotion} />
      <Branch position={[-0.12, 0.7, 0]} baseRotation={[0, 0, 1.1]} scale={0.8} emotion={emotion} />
      <Branch position={[0, 0.9, 0.12]} baseRotation={[1.2, 0, 0]} scale={0.85} emotion={emotion} />
      <Branch position={[0, 1.1, -0.1]} baseRotation={[-1, 0, 0]} scale={0.7} emotion={emotion} />

      {/* --- CÁC CÀNH ĐỘNG (Chỉ mọc ra khi tích cực) --- */}
      {/* Cành mọc thấp khi bình yên hoặc hy vọng */}
      <Branch 
        position={[-0.15, 0.45, 0.1]} 
        baseRotation={[0.5, 0, 1.3]} 
        scale={0.75} 
        emotion={emotion} 
        isVisible={emotion === "calm" || emotion === "hopeful"} 
      />
      {/* Hai cành mọc vươn cao khi tràn đầy hy vọng */}
      <Branch 
        position={[0.12, 0.8, -0.1]} 
        baseRotation={[-0.8, 0.5, -1]} 
        scale={0.8} 
        emotion={emotion} 
        isVisible={emotion === "hopeful"} 
      />
      <Branch 
        position={[0, 0.6, 0.15]} 
        baseRotation={[1.4, -0.2, 0]} 
        scale={0.65} 
        emotion={emotion} 
        isVisible={emotion === "hopeful"} 
      />

      <Sparkles
        count={EMOTION_MOTION[emotion].sparkles}
        scale={3.5}
        size={2}
        speed={0.2}
        opacity={0.6}
        color={PALETTE[emotion].magic}
        position={[0, 1.5, 0]}
      />

      <FallingLeaves active={emotion === "stressed"} />
    </group>
  )
}

// --------------------------------------------------------
// COMPONENT CONTAINER
// --------------------------------------------------------
export default function SoulTree({ emotion = "calm", className }: SoulTreeProps) {
  return (
    <div
      className={cn(
        "h-125 w-full overflow-hidden rounded-3xl border border-white/40 bg-linear-to-b from-[#A8C3D8]/20 to-[#FDFBF7] shadow-sm",
        className
      )}
    >
      <Canvas camera={{ position: [0, 1.5, 6], fov: 40 }}>
        <ambientLight intensity={0.7} color="#FDFBF7" />
        <directionalLight position={[5, 10, 5]} intensity={1.5} color="#FDFBF7" castShadow />
        <directionalLight position={[-5, -5, -5]} intensity={0.5} color={PALETTE[emotion].accent} />

        <Tree emotion={emotion} />

        <ContactShadows position={[0, -1, 0]} opacity={0.35} scale={12} blur={2} far={3} color="#2F3E36" />
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          autoRotate
          autoRotateSpeed={emotion === "stressed" ? 0.22 : 0.4}
          maxPolarAngle={Math.PI / 2 + 0.1}
          minPolarAngle={Math.PI / 4}
        />
      </Canvas>
    </div>
  )
}
