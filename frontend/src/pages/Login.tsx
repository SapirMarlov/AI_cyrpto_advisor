import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import SplitText from "@/components/SplitText";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

type IntroPhase = "hero" | "form";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [phase, setPhase] = useState<IntroPhase>("hero");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const revealForm = useCallback(() => {
    setPhase("form");
  }, []);

  useEffect(() => {
    // Safety net if GSAP/ScrollTrigger does not fire in some environments.
    const timeoutId = window.setTimeout(revealForm, 4800);
    return () => window.clearTimeout(timeoutId);
  }, [revealForm]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setServerError(null);

    if (!email.trim() || password.length < 8) {
      setFieldError("Enter a valid email and a password of at least 8 characters.");
      return;
    }

    setFieldError(null);
    setPending(true);
    const result = await login(email.trim(), password);
    setPending(false);

    if (!result.ok) {
      setServerError(result.message);
      return;
    }

    navigate("/onboarding");
  }

  const showForm = phase === "form";
  const layoutEase = "ease-[cubic-bezier(0.33,0.1,0.2,1)]";

  return (
    <main
      className={cn(
        "flex items-center justify-center px-4 transition-[min-height] duration-[1400ms]",
        layoutEase,
        showForm ? "min-h-[70vh]" : "min-h-[calc(100svh-4rem)]",
      )}
    >
      <div
        className={cn(
          "w-full max-w-md transition-[gap] duration-[1400ms]",
          layoutEase,
          showForm ? "flex flex-col gap-6" : "flex flex-col gap-0",
        )}
      >
        <div className="space-y-2 text-center">
          <SplitText
            text="AI Crypto Advisor"
            tag="h1"
            className={cn(
              "font-semibold tracking-tight transition-[font-size,letter-spacing] duration-[1400ms]",
              layoutEase,
              showForm ? "text-3xl" : "text-5xl md:text-6xl",
            )}
            delay={55}
            duration={1.1}
            ease="power2.out"
            splitType="chars"
            from={{ opacity: 0, y: 24 }}
            to={{ opacity: 1, y: 0 }}
            threshold={0}
            rootMargin="0px"
            textAlign="center"
            onLetterAnimationComplete={revealForm}
          />
          <p
            className={cn(
              "text-muted-foreground text-sm transition-all duration-[1100ms]",
              layoutEase,
              showForm
                ? "translate-y-0 opacity-100 delay-300"
                : "pointer-events-none -translate-y-1 opacity-0",
            )}
            aria-hidden={!showForm}
          >
            Sign in to your personalized crypto dashboard.
          </p>
        </div>

        <div
          className={cn(
            "transition-all duration-[1400ms]",
            layoutEase,
            showForm
              ? "translate-y-0 scale-100 opacity-100 delay-500"
              : "pointer-events-none translate-y-6 scale-[0.99] opacity-0",
          )}
          aria-hidden={!showForm}
          {...(!showForm ? { inert: "" } : {})}
        >
          <Card className="transition-shadow duration-300">
            <CardHeader>
              <CardTitle>Log in</CardTitle>
              <CardDescription>Use the email and password for your account.</CardDescription>
            </CardHeader>
            <form onSubmit={onSubmit}>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="login-email">Email</Label>
                  <Input
                    id="login-email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    disabled={pending || !showForm}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="login-password">Password</Label>
                  <Input
                    id="login-password"
                    type="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    disabled={pending || !showForm}
                    required
                  />
                </div>
                {fieldError ? (
                  <p className="text-destructive text-sm" role="alert">
                    {fieldError}
                  </p>
                ) : null}
                {serverError ? (
                  <p className="text-destructive text-sm" role="alert">
                    {serverError}
                  </p>
                ) : null}
              </CardContent>
              <CardFooter className="flex flex-col gap-3">
                <Button type="submit" className="w-full" disabled={pending || !showForm}>
                  {pending ? "Signing in…" : "Log in"}
                </Button>
                <p className="text-muted-foreground text-sm">
                  Need an account?{" "}
                  <Link className="text-primary underline-offset-4 hover:underline" to="/signup">
                    Sign up
                  </Link>
                </p>
              </CardFooter>
            </form>
          </Card>
        </div>
      </div>
    </main>
  );
}
