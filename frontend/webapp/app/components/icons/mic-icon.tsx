import type { ComponentProps } from "react"

import { cn } from "~/lib/utils"

export function MicIcon({
  className,
  ...props
}: ComponentProps<"svg">) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("h-4 w-4", className)}
      aria-hidden="true"
      {...props}
    >
      <path d="M12 3.5a2.8 2.8 0 0 0-2.8 2.8v5.6a2.8 2.8 0 1 0 5.6 0V6.3A2.8 2.8 0 0 0 12 3.5Z" />
      <path d="M6.5 10.8a5.5 5.5 0 1 0 11 0" />
      <path d="M12 18.3v2.2" />
      <path d="M8.8 20.5h6.4" />
    </svg>
  )
}
