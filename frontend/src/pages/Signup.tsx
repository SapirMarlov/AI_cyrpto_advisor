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

export function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setServerError(null);

    if (!name.trim() || !email.trim() || password.length < 8) {
      setFieldError(
        "Enter your name, a valid email, and a password of at least 8 characters.",
      );
      return;
    }

    setFieldError(null);
    setPending(true);
    const result = await signup(email.trim(), password, name.trim());
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
            Create an account to start your daily crypto briefing.
          </p>
        </div>

        <Card className="transition-shadow duration-300">
          <CardHeader>
            <CardTitle>Sign up</CardTitle>
            <CardDescription>Choose a name, email, and a secure password.</CardDescription>
          </CardHeader>
          <form onSubmit={onSubmit}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="signup-name">Name</Label>
                <Input
                  id="signup-name"
                  type="text"
                  autoComplete="name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  disabled={pending}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="signup-email">Email</Label>
                <Input
                  id="signup-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  disabled={pending}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="signup-password">Password</Label>
                <Input
                  id="signup-password"
                  type="password"
                  autoComplete="new-password"
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
                {pending ? "Creating account…" : "Create account"}
              </Button>
              <p className="text-muted-foreground text-sm">
                Already have an account?{" "}
                <Link className="text-primary underline-offset-4 hover:underline" to="/login">
                  Log in
                </Link>
              </p>
            </CardFooter>
          </form>
        </Card>
      </div>
    </main>
  );
}
