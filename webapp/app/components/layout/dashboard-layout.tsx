import { NavLink, Outlet } from "react-router"

import { useSoulForest } from "~/context/soul-forest-context"

const navigation = [
  { label: "Home", to: "/app/home" },
  { label: "Journal", to: "/app/journal" },
]

export function DashboardLayout() {
  const { currentMood, intensity, lastQuote } = useSoulForest()

  return (
    <div className="h-svh overflow-hidden bg-[#FDFBF7] text-[#2F3E36]">
      <div className="mx-auto flex h-full max-w-7xl flex-col gap-6 px-4 py-4 sm:px-6 lg:flex-row lg:px-8">
        <aside className="w-full shrink-0 rounded-[2rem] border border-white/40 bg-white/30 p-5 shadow-sm backdrop-blur-md lg:sticky lg:top-4 lg:h-[calc(100svh-2rem)] lg:max-w-xs">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#7E9F8B] text-sm font-semibold text-white">
              SF
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-[#7E9F8B]">
                Soul Forest
              </p>
              <h1 className="text-xl font-semibold text-[#2F3E36]">
                Gentle dashboard
              </h1>
            </div>
          </div>

          <nav className="mt-8 flex flex-col gap-2">
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  [
                    "rounded-full px-4 py-3 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-[#7E9F8B] text-white"
                      : "bg-white/40 text-[#2F3E36] hover:bg-white/60",
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="mt-8 rounded-[1.75rem] bg-gradient-to-br from-[#A8C3D8]/35 to-[#7E9F8B]/25 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium">Forest pulse</p>
              <span className="rounded-full bg-white/40 px-3 py-1 text-xs">
                {currentMood}
              </span>
            </div>
            <p className="mt-2 text-sm leading-6 text-[#2F3E36]/75">
              Emotional intensity is currently resting at {intensity}%. Your
              latest reflection is shaping the canopy.
            </p>
          </div>

          <div className="mt-4 rounded-[1.75rem] bg-white/25 p-4">
            <p className="text-xs uppercase tracking-[0.28em] text-[#7E9F8B]">
              Latest grounding
            </p>
            <p className="mt-3 text-sm leading-6 text-[#2F3E36]/75">
              {lastQuote}
            </p>
          </div>
        </aside>

        <main className="min-h-0 flex-1 overflow-y-auto rounded-[2rem] border border-white/40 bg-white/30 p-5 shadow-sm backdrop-blur-md sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
