import { type RouteConfig, index, route } from "@react-router/dev/routes"

export default [
  index("routes/landing-page.tsx"),
  route("login", "routes/login.tsx"),
  route("register", "routes/register.tsx"),
  route("app", "routes/app-layout.tsx", [
    index("routes/app-index.tsx"),
    route("home", "routes/dashboard-home.tsx"),
    route("journal", "routes/journal.tsx"),
  ]),
] satisfies RouteConfig
