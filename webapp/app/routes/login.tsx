import {
  ArrowRight01Icon,
  LockPasswordIcon,
  Mail01Icon,
} from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router"

import { AuthShell } from "~/components/auth/auth-shell"
import { Button } from "~/components/ui/button"
import { useAuth } from "~/context/auth-context"

function Field({
  children,
  label,
}: {
  children: React.ReactNode
  label: string
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-medium text-[#2F3E36]">
        {label}
      </span>
      {children}
    </label>
  )
}

function InputFrame({ children }: { children: React.ReactNode }) {
  return (
    <span className="flex items-center gap-3 rounded-[1.25rem] border border-white/45 bg-[#FDFBF7]/78 px-4 py-3">
      {children}
    </span>
  )
}

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState("")

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!email.trim() || !password.trim()) {
      setError("Please enter both email and password.")
      return
    }

    setError("")
    setIsSubmitting(true)

    try {
      await login(email.trim(), password)
      const done = localStorage.getItem("eflow_onboarding_done")
      navigate(done ? "/app/home" : "/onboarding")
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unable to sign in right now."
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthShell
      eyebrow="Welcome back"
      title="Sign in and keep going."
      description="Pick up your journal where you left off."
      helperLink={{ label: "Need an account?", to: "/register" }}
      highlights={["Private journal", "Gentle reflection", "Daily clarity"]}
    >
      <p className="text-xs tracking-[0.32em] text-[var(--brand-primary-muted)] uppercase">
        Sign in
      </p>

      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        <Field label="Email">
          <InputFrame>
            <HugeiconsIcon
              icon={Mail01Icon}
              size={18}
              strokeWidth={1.8}
              className="text-[var(--brand-primary-muted)]"
            />
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              className="w-full bg-transparent text-sm text-[#2F3E36] outline-none placeholder:text-[#2F3E36]/35"
            />
          </InputFrame>
        </Field>

        <Field label="Password">
          <InputFrame>
            <HugeiconsIcon
              icon={LockPasswordIcon}
              size={18}
              strokeWidth={1.8}
              className="text-[var(--brand-primary-muted)]"
            />
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              className="w-full bg-transparent text-sm text-[#2F3E36] outline-none placeholder:text-[#2F3E36]/35"
            />
          </InputFrame>
        </Field>

        {error ? (
          <p className="rounded-[1rem] bg-[#f4ddd4] px-4 py-3 text-sm text-[#8b4e3d]">
            {error}
          </p>
        ) : null}

        <Button
          type="submit"
          disabled={isSubmitting}
          className="h-12 w-full rounded-full border-0 bg-[var(--brand-primary)] text-[var(--brand-on-primary)] hover:bg-[var(--brand-primary-strong)]"
        >
          {isSubmitting ? "Signing in..." : "Sign in"}
          <HugeiconsIcon
            icon={ArrowRight01Icon}
            size={16}
            strokeWidth={1.8}
            className="ml-2"
          />
        </Button>
      </form>

      <div className="mt-6 flex items-center justify-between gap-3 text-sm text-[#2F3E36]/64">
        <Link to="/register" className="transition-colors hover:text-[#2F3E36]">
          Create a new account
        </Link>
        <span className="rounded-full bg-white/60 px-4 py-2">
          Private by default
        </span>
      </div>
    </AuthShell>
  )
}
