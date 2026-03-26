import * as React from "react"
import * as SliderPrimitive from "@radix-ui/react-slider"

import { cn } from "~/lib/utils"

function Slider({
  className,
  ...props
}: React.ComponentProps<typeof SliderPrimitive.Root>) {
  return (
    <SliderPrimitive.Root
      data-slot="slider"
      className={cn(
        "relative flex w-full touch-none select-none items-center",
        className
      )}
      {...props}
    >
      <SliderPrimitive.Track className="relative h-2.5 w-full grow overflow-hidden rounded-full bg-white/50">
        <SliderPrimitive.Range className="absolute h-full rounded-full bg-[var(--brand-primary)]" />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb className="block size-5 rounded-full border border-white/60 bg-[#FDFBF7] shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-primary)]/40 disabled:pointer-events-none disabled:opacity-50" />
    </SliderPrimitive.Root>
  )
}

export { Slider }
