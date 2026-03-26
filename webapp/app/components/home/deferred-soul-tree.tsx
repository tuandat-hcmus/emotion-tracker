import {
  Suspense,
  lazy,
  startTransition,
  useEffect,
  useState,
  type ComponentProps,
} from "react"

import type SoulTree from "~/components/home/soul-tree"
import { cn } from "~/lib/utils"

const LazySoulTree = lazy(() => import("~/components/home/soul-tree"))

type IdleWindow = Window & {
  cancelIdleCallback?: (handle: number) => void
  requestIdleCallback?: (
    callback: () => void,
    options?: { timeout?: number }
  ) => number
}

type DeferredSoulTreeProps = ComponentProps<typeof SoulTree> & {
  deferMs?: number
}

function SoulTreeFallback({
  className,
}: {
  className?: string
}) {
  return (
    <div
      className={cn(
        "relative w-full overflow-hidden rounded-3xl border border-white/40 bg-[radial-gradient(circle_at_top,rgba(168,195,216,0.34),rgba(253,251,247,0.88),rgba(126,159,139,0.2))] shadow-sm",
        className
      )}
    >
      <div className="absolute inset-0">
        <div className="absolute left-1/2 top-[18%] h-28 w-28 -translate-x-[4.8rem] rounded-full bg-[#BFD7C8]/90 blur-[1px]" />
        <div className="absolute left-1/2 top-[12%] h-36 w-36 -translate-x-1/2 rounded-full bg-[#8FAE9B]/88 blur-[1px]" />
        <div className="absolute left-1/2 top-[20%] h-24 w-24 translate-x-[4.2rem] rounded-full bg-[#D7E4EE]/84 blur-[1px]" />
        <div className="absolute left-1/2 bottom-[18%] h-40 w-10 -translate-x-1/2 rounded-full bg-[#A67E5B]/82" />
        <div className="absolute bottom-[10%] left-1/2 h-16 w-40 -translate-x-1/2 rounded-full bg-[var(--brand-primary)]/18 blur-2xl" />
      </div>
    </div>
  )
}

export function DeferredSoulTree({
  className,
  deferMs = 180,
  ...props
}: DeferredSoulTreeProps) {
  const [shouldLoad, setShouldLoad] = useState(false)

  useEffect(() => {
    const idleWindow = window as IdleWindow
    let timeoutId: number | null = null
    let idleId: number | null = null

    const loadTree = () => {
      startTransition(() => {
        setShouldLoad(true)
      })
    }

    if (idleWindow.requestIdleCallback) {
      idleId = idleWindow.requestIdleCallback(loadTree, {
        timeout: deferMs + 400,
      })
    } else {
      timeoutId = window.setTimeout(loadTree, deferMs)
    }

    return () => {
      if (idleId !== null && idleWindow.cancelIdleCallback) {
        idleWindow.cancelIdleCallback(idleId)
      }

      if (timeoutId !== null) {
        window.clearTimeout(timeoutId)
      }
    }
  }, [deferMs])

  if (!shouldLoad) {
    return <SoulTreeFallback className={className} />
  }

  return (
    <Suspense fallback={<SoulTreeFallback className={className} />}>
      <LazySoulTree className={className} {...props} />
    </Suspense>
  )
}
