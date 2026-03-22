import fileSvg from "~/assets/file.svg?raw"
import { cn } from "~/lib/utils"

type SvgLogoProps = {
  className?: string
  label?: string
}

const themedWordmark = fileSvg
  .replaceAll('fill="#000000"', 'fill="currentColor"')

function RawSvg({
  className,
  label,
  markup,
}: SvgLogoProps & {
  markup: string
}) {
  return (
    <span
      aria-label={label}
      className={cn(
        "inline-flex items-center justify-center [&_svg]:block [&_svg]:h-full [&_svg]:w-full",
        className
      )}
      dangerouslySetInnerHTML={{ __html: markup }}
      role={label ? "img" : undefined}
    />
  )
}

export function EFlowLogoMark({
  className,
  label = "eFlow logo",
}: SvgLogoProps) {
  return <RawSvg className={className} label={label} markup={themedWordmark} />
}

export function EFlowWordmark({
  className,
  label = "eFlow wordmark",
}: SvgLogoProps) {
  return <RawSvg className={className} label={label} markup={themedWordmark} />
}
