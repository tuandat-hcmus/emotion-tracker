import {
  ContactShadows,
  Float,
  OrbitControls,
  Sparkles,
  SpotLight,
} from "@react-three/drei"
import { Canvas, useFrame } from "@react-three/fiber"
import { memo, useEffect, useMemo, useRef, useState } from "react"
import * as THREE from "three"

import { type SoulEmotion } from "~/lib/emotions"
import { cn } from "~/lib/utils"

export type EmotionState = SoulEmotion

type SoulTreeProps = {
  emotion?: EmotionState
  score?: number
  animateTransition?: boolean
  className?: string
}

type Palette = {
  accent: string
  glow: string
  magic: string
  main: string
  trunk: string
}

const PALETTE: Record<EmotionState, Palette> = {
  joy: {
    main: "#FFD400",
    accent: "#FFF1A1",
    glow: "#FFE88A",
    trunk: "#A97946",
    magic: "#FFD400",
  },
  surprise: {
    main: "#FF3E9B",
    accent: "#FF8C00",
    glow: "#FFD400",
    trunk: "#A97946",
    magic: "#FF8C00",
  },
  neutral: {
    main: "#6FAF4F",
    accent: "#BFE296",
    glow: "#E8F8D8",
    trunk: "#8B6A4A",
    magic: "#D7F2BA",
  },
  sadness: {
    main: "#78B7E8",
    accent: "#B8DBF4",
    glow: "#E7F5FF",
    trunk: "#7A695D",
    magic: "#B8DBF4",
  },
  disgust: {
    main: "#A9AEB8",
    accent: "#D4D8DE",
    glow: "#EEF1F4",
    trunk: "#7B6B63",
    magic: "#C9CED6",
  },
  anxiety: {
    main: "#FF7A59",
    accent: "#FF3E9B",
    glow: "#FFD9A3",
    trunk: "#7A5A4A",
    magic: "#FFD400",
  },
  anger: {
    main: "#D62828",
    accent: "#FF8C00",
    glow: "#FFB067",
    trunk: "#6B4638",
    magic: "#FF8C00",
  },
}

function getTreeState(score: number) {
  const clampedScore = THREE.MathUtils.clamp(score, 0, 100)

  return {
    branchFloat: THREE.MathUtils.mapLinear(clampedScore, 0, 100, 0.2, 1.25),
    canopyFloat: THREE.MathUtils.mapLinear(clampedScore, 0, 100, 0.08, 0.9),
    droop: THREE.MathUtils.mapLinear(clampedScore, 0, 100, 1.1, -0.18),
    effectStrength: THREE.MathUtils.mapLinear(clampedScore, 0, 100, 0.45, 1.1),
    foliageScale:
      clampedScore < 40
        ? THREE.MathUtils.mapLinear(clampedScore, 0, 40, 0.42, 1)
        : 1,
    flowerScale:
      clampedScore > 58
        ? THREE.MathUtils.mapLinear(clampedScore, 58, 100, 0, 1.15)
        : 0,
    showLowerBranch: clampedScore >= 24,
    showUpperBranchA: clampedScore >= 52,
    showUpperBranchB: clampedScore >= 78,
  }
}

type TreeState = ReturnType<typeof getTreeState>

function Flower({
  color = "#FFD4EC",
  position,
  targetScale,
}: {
  position: [number, number, number]
  targetScale: number
  color?: string
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const currentScale = useRef(0)

  useFrame((_, delta) => {
    currentScale.current = THREE.MathUtils.lerp(
      currentScale.current,
      targetScale,
      delta * 2.4
    )

    if (meshRef.current) {
      meshRef.current.scale.setScalar(currentScale.current)
    }
  })

  return (
    <mesh ref={meshRef} position={position}>
      <icosahedronGeometry args={[0.1, 0]} />
      <meshStandardMaterial color={color} flatShading roughness={0.42} />
    </mesh>
  )
}

function FoliageCluster({
  colorType,
  emotion,
  position,
  scale = 1,
  treeState,
}: {
  position: [number, number, number]
  scale?: number | [number, number, number]
  colorType: "main" | "accent" | "glow"
  emotion: EmotionState
  treeState: TreeState
}) {
  const material1 = useRef<THREE.MeshStandardMaterial>(null)
  const material2 = useRef<THREE.MeshStandardMaterial>(null)
  const material3 = useRef<THREE.MeshStandardMaterial>(null)
  const targetColor = useMemo(() => new THREE.Color(), [])
  const groupRef = useRef<THREE.Group>(null)

  useFrame((state, delta) => {
    targetColor.set(PALETTE[emotion][colorType])
    material1.current?.color.lerp(targetColor, delta * 2)
    material2.current?.color.lerp(targetColor, delta * 2)
    material3.current?.color.lerp(targetColor, delta * 2)

    // Hiệu ứng bùng cháy Anger: Tự phát sáng emissive
    if (emotion === "anger") {
      const material = material1.current
      if (material) {
        material.emissive.set("#D62828")
        material.emissiveIntensity = 0.5 + Math.sin(state.clock.elapsedTime * 10) * 0.5
      }
    } else {
      material1.current?.emissive.set("#000")
      if (material1.current) material1.current.emissiveIntensity = 0
    }

    if (groupRef.current) {
      const baseScale = typeof scale === "number" ? scale : scale[0]
      const targetScale = baseScale * treeState.foliageScale
      groupRef.current.scale.setScalar(
        THREE.MathUtils.lerp(groupRef.current.scale.x, targetScale, delta * 2)
      )
    }
  })

  return (
    <group ref={groupRef} position={position} scale={scale}>
      <mesh scale={[1.2, 0.7, 1.2]}>
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

      <Flower position={[0.25, 0.15, 0.1]} targetScale={treeState.flowerScale} />
      <Flower
        position={[-0.2, 0.1, 0.25]}
        targetScale={treeState.flowerScale * 0.8}
        color="#FFF0F5"
      />
      <Flower
        position={[0.05, 0.2, -0.2]}
        targetScale={treeState.flowerScale * 0.9}
        color="#FFB9D9"
      />
    </group>
  )
}

function Branch({
  baseRotation,
  emotion,
  isVisible = true,
  position,
  scale = 1,
  treeState,
}: {
  position: [number, number, number]
  baseRotation: [number, number, number]
  scale?: number
  emotion: EmotionState
  isVisible?: boolean
  treeState: TreeState
}) {
  const branchLength = 0.8
  const groupRef = useRef<THREE.Group>(null)
  const currentScale = useRef(isVisible ? scale : 0)

  useFrame((_, delta) => {
    if (!groupRef.current) {
      return
    }

    const targetEuler = new THREE.Euler(
      baseRotation[0] + treeState.droop,
      baseRotation[1],
      baseRotation[2]
    )
    const targetQuaternion = new THREE.Quaternion().setFromEuler(targetEuler)
    groupRef.current.quaternion.slerp(targetQuaternion, delta * 2)

    const targetScale = isVisible ? scale : 0
    currentScale.current = THREE.MathUtils.lerp(
      currentScale.current,
      targetScale,
      delta * 1.5
    )
    groupRef.current.scale.setScalar(currentScale.current)
  })

  return (
    <group ref={groupRef} position={position}>
      <mesh position={[0, branchLength / 2, 0]}>
        <cylinderGeometry args={[0.015, 0.05, branchLength, 5]} />
        <meshStandardMaterial
          color={PALETTE[emotion].trunk}
          flatShading
          roughness={0.9}
        />
      </mesh>
      <Float
        speed={treeState.branchFloat}
        rotationIntensity={0.15}
        floatIntensity={0.4}
      >
        <group position={[0, branchLength, 0]}>
          <FoliageCluster
            position={[0, 0, 0]}
            scale={1.2}
            colorType="main"
            emotion={emotion}
            treeState={treeState}
          />
          <FoliageCluster
            position={[0.1, 0.1, 0.1]}
            scale={0.7}
            colorType="glow"
            emotion={emotion}
            treeState={treeState}
          />
        </group>
      </Float>
    </group>
  )
}

// ================= CÁC HIỆU ỨNG MÔI TRƯỜNG =================

function JoySunlight({
  active,
  intensity,
}: {
  active: boolean
  intensity: number
}) {
  const groupRef = useRef<THREE.Group>(null)

  useFrame((state) => {
    if (!groupRef.current) return
    groupRef.current.visible = active
    if (!active) return
    groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.28) * 0.08
  })

  return (
    <group ref={groupRef}>
      {/* Nguồn sáng rực rỡ phía trên mô phỏng mặt trời */}
      <pointLight 
        position={[0, 10, 0]} 
        intensity={10 * intensity} 
        color="#FFD400" 
        distance={15} 
      />
      {/* Ánh sáng ấm áp chiếu xiên */}
      <SpotLight
        position={[5, 8, 3]}
        angle={0.6}
        penumbra={1}
        intensity={8 * intensity}
        color="#FFD400"
        distance={20}
      />
      {/* Hiệu ứng tia nắng mờ ảo */}
      <mesh position={[0, 3, 0]} rotation={[0, 0, 0]}>
        <cylinderGeometry args={[0.2, 1.5, 6, 32, 1, true]} />
        <meshBasicMaterial
          color="#FFD400"
          transparent
          opacity={0.12 * intensity}
          side={THREE.DoubleSide}
          depthWrite={false}
          depthTest={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      {/* Hạt bụi nắng lấp lánh */}
      <Sparkles
        count={60}
        scale={[4, 6, 4]}
        size={3.5}
        speed={0.6}
        color="#FFD400"
        position={[0, 2, 0]}
      />
    </group>
  )
}

function RainField({
  active,
  intensity,
}: {
  active: boolean
  intensity: number
}) {
  const groupRef = useRef<THREE.Group>(null)
  const drops = useMemo(
    () =>
      Array.from({ length: 22 }, () => ({
        speed: 1.4 + Math.random() * 0.9,
        x: (Math.random() - 0.5) * 3.2,
        y: 0.8 + Math.random() * 2.8,
        z: (Math.random() - 0.5) * 1.5,
      })),
    []
  )

  useFrame((state) => {
    if (!groupRef.current) return
    groupRef.current.visible = active
    if (!active) return

    groupRef.current.children.forEach((child, index) => {
      const config = drops[index]
      if (!config) return

      const mesh = child as THREE.Mesh
      const fallDistance =
        ((state.clock.elapsedTime * (config.speed + intensity * 0.25) + index * 0.18) %
          3.8)

      mesh.position.set(
        config.x,
        2.8 - fallDistance + config.y * 0.12,
        config.z
      )
    })
  })

  return (
    <group ref={groupRef}>
      {drops.map((config, index) => (
        <mesh key={index} position={[config.x, config.y, config.z]}>
          <capsuleGeometry args={[0.015, 0.14, 3, 6]} />
          <meshBasicMaterial color="#B8DBF4" transparent opacity={0.7} />
        </mesh>
      ))}
    </group>
  )
}

function AngerEmberBurst({
  active,
  intensity,
}: {
  active: boolean
  intensity: number
}) {
  const lightRef = useRef<THREE.PointLight>(null)

  useFrame((state) => {
    if (!active) return
    if (lightRef.current) {
      lightRef.current.intensity = (4 + Math.sin(state.clock.elapsedTime * 15) * 2) * intensity
    }
  })

  return (
    <group visible={active}>
      {/* Lửa bùng lên từ gốc và tán lá */}
      <Sparkles
        count={80}
        scale={2.5}
        size={5}
        speed={3}
        color="#D62828"
        noise={1.5}
        position={[0, 1.5, 0]}
      />
      {/* Tia lửa cam nhỏ */}
      <Sparkles
        count={50}
        scale={1.5}
        size={3}
        speed={2}
        color="#FF8C00"
        position={[0, 1, 0]}
      />
      <pointLight
        ref={lightRef}
        position={[0, 1, 0.5]}
        color="#D62828"
        distance={6}
      />
    </group>
  )
}

function AnxietyAura({
  active,
  intensity,
}: {
  active: boolean
  intensity: number
}) {
  return (
    <group visible={active} position={[0, 1.6, 0]}>
      {/* Chỉ giữ lại các hạt bay xung quanh, bỏ vòng xoáy */}
      <Sparkles
        count={100}
        scale={2.5}
        size={2}
        speed={5}
        color="#FF3E9B"
        opacity={0.8 * intensity}
      />
    </group>
  )
}

function Tree({
  emotion,
  treeState,
}: {
  emotion: EmotionState
  treeState: TreeState
}) {
  const trunkMaterial = useRef<THREE.MeshStandardMaterial>(null)
  const targetTrunkColor = useMemo(() => new THREE.Color(), [])
  const groupRef = useRef<THREE.Group>(null)

  useFrame((state, delta) => {
    // Lerp màu thân cây
    targetTrunkColor.set(PALETTE[emotion].trunk)
    trunkMaterial.current?.color.lerp(targetTrunkColor, delta * 2)

    // Đưa cây về vị trí tĩnh (không rung lắc cho bất kỳ trạng thái nào)
    if (groupRef.current) {
      groupRef.current.position.x = THREE.MathUtils.lerp(groupRef.current.position.x, 0, delta * 4)
      groupRef.current.position.z = THREE.MathUtils.lerp(groupRef.current.position.z, 0, delta * 4)
    }
  })

  return (
    <group ref={groupRef} position={[0, -1, 0]}>
      <JoySunlight active={emotion === "joy"} intensity={treeState.effectStrength} />
      <RainField active={emotion === "sadness"} intensity={treeState.effectStrength} />
      <AngerEmberBurst
        active={emotion === "anger"}
        intensity={treeState.effectStrength}
      />
      <AnxietyAura
        active={emotion === "anxiety"}
        intensity={treeState.effectStrength}
      />

      <mesh position={[0, 0.75, 0]}>
        <cylinderGeometry args={[0.08, 0.25, 1.5, 6]} />
        <meshStandardMaterial ref={trunkMaterial} flatShading roughness={1} />
      </mesh>

      <Float
        speed={treeState.canopyFloat}
        rotationIntensity={0.1}
        floatIntensity={0.2}
      >
        <group position={[0, 1.6, 0]}>
          <FoliageCluster
            position={[0, 0, 0]}
            scale={2.2}
            colorType="main"
            emotion={emotion}
            treeState={treeState}
          />
          <FoliageCluster
            position={[0, 0.3, 0]}
            scale={1.5}
            colorType="accent"
            emotion={emotion}
            treeState={treeState}
          />
          <FoliageCluster
            position={[0.2, 0.1, 0.2]}
            scale={1.2}
            colorType="glow"
            emotion={emotion}
            treeState={treeState}
          />
        </group>
      </Float>

      <Branch
        position={[0.15, 0.4, 0]}
        baseRotation={[0, 0, -1.2]}
        scale={0.9}
        emotion={emotion}
        treeState={treeState}
      />
      <Branch
        position={[-0.12, 0.7, 0]}
        baseRotation={[0, 0, 1.1]}
        scale={0.8}
        emotion={emotion}
        treeState={treeState}
      />
      <Branch
        position={[0, 0.9, 0.12]}
        baseRotation={[1.2, 0, 0]}
        scale={0.85}
        emotion={emotion}
        treeState={treeState}
      />
      <Branch
        position={[0, 1.1, -0.1]}
        baseRotation={[-1, 0, 0]}
        scale={0.7}
        emotion={emotion}
        treeState={treeState}
      />

      <Branch
        position={[-0.15, 0.45, 0.1]}
        baseRotation={[0.5, 0, 1.3]}
        scale={0.75}
        emotion={emotion}
        isVisible={treeState.showLowerBranch}
        treeState={treeState}
      />
      <Branch
        position={[0.12, 0.8, -0.1]}
        baseRotation={[-0.8, 0.5, -1]}
        scale={0.8}
        emotion={emotion}
        isVisible={treeState.showUpperBranchA}
        treeState={treeState}
      />
      <Branch
        position={[0, 0.6, 0.15]}
        baseRotation={[1.4, -0.2, 0]}
        scale={0.65}
        emotion={emotion}
        isVisible={treeState.showUpperBranchB}
        treeState={treeState}
      />
    </group>
  )
}

const SoulTree = memo(function SoulTree({
  emotion = "neutral",
  score = 50,
  animateTransition = true,
  className,
}: SoulTreeProps) {
  const [displayEmotion, setDisplayEmotion] = useState<EmotionState>(emotion)

  useEffect(() => {
    if (!animateTransition) {
      setDisplayEmotion(emotion)
      return
    }

    const transitionTimer = window.setTimeout(() => {
      setDisplayEmotion(emotion)
    }, 120)

    return () => {
      window.clearTimeout(transitionTimer)
    }
  }, [animateTransition, emotion])

  const treeState = useMemo(() => getTreeState(score), [score])

  return (
    <div
      className={cn(
        "relative h-125 w-full overflow-hidden rounded-3xl border border-white/40 bg-linear-to-b from-[#A8C3D8]/18 to-[#FDFBF7] shadow-sm",
        className
      )}
    >
      <div className="absolute top-4 left-4 z-10 rounded-full bg-white/50 px-3 py-1 text-sm font-semibold text-gray-700 backdrop-blur-sm">
        Growth: {Math.round(score)}/100
      </div>

      <Canvas
        camera={{ position: [0, 1.5, 6], fov: 40 }}
        dpr={[1, 1.4]}
        shadows={false}
        performance={{ min: 0.75 }}
      >
        <ambientLight intensity={0.78} color="#FDFBF7" />
        <directionalLight position={[5, 10, 5]} intensity={1.55} color="#FDFBF7" />
        <directionalLight
          position={[-5, -5, -5]}
          intensity={0.58}
          color={PALETTE[displayEmotion].accent}
        />
        <pointLight
          position={[0, 2.9, 1.2]}
          intensity={displayEmotion === "joy" ? 1.9 : 1.15}
          color={PALETTE[displayEmotion].glow}
          distance={7}
        />

        <Tree emotion={displayEmotion} treeState={treeState} />

        <ContactShadows
          position={[0, -1, 0]}
          opacity={displayEmotion === "joy" ? 0.4 : displayEmotion === "anxiety" ? 0.12 : 0.24}
          scale={10}
          blur={displayEmotion === "joy" ? 1.1 : displayEmotion === "anxiety" ? 2.4 : 1.6}
          far={2.8}
          color="#2F3E36"
          resolution={256}
        />

        <OrbitControls
          enableZoom={false}
          enablePan={false}
          autoRotate
          autoRotateSpeed={
            displayEmotion === "anxiety" ? 2.5 
            : displayEmotion === "anger" ? 0.8 
            : displayEmotion === "joy" ? 0.15 
            : 0.24 // Mặc định cho các trạng thái còn lại bao gồm cả surprise
          }
          maxPolarAngle={Math.PI / 2 + 0.1}
          minPolarAngle={Math.PI / 4}
        />
      </Canvas>
    </div>
  )
})

export default SoulTree