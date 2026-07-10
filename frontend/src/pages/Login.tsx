import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
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

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

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

  return (
    <main className="animate-in fade-in flex min-h-[70vh] items-center justify-center px-4 duration-300">
      <div className="w-full max-w-md space-y-6">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-semibold tracking-tight">AI Crypto Advisor</h1>
          <p className="text-muted-foreground text-sm">
            Sign in to your personalized crypto dashboard.
          </p>
        </div>

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
                  disabled={pending}
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
                  disabled={pending}
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
              <Button type="submit" className="w-full" disabled={pending}>
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
    </main>
  );
}
