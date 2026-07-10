import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

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
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  getQuestions,
  saveAnswers,
  type OnboardingQuestion,
} from "@/services/apiClient";

type AnswersState = Record<string, string | string[]>;

export function OnboardingPage() {
  const { refreshMe } = useAuth();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState<OnboardingQuestion[]>([]);
  const [answers, setAnswers] = useState<AnswersState>({});
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setLoadError(null);
      const result = await getQuestions();
      if (cancelled) {
        return;
      }
      if (!result.ok) {
        setLoadError(result.error.message);
        setQuestions([]);
        setLoading(false);
        return;
      }
      setQuestions(result.data.questions);
      setLoading(false);
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  function setSingleAnswer(questionId: string, value: string) {
    setAnswers((current) => ({ ...current, [questionId]: value }));
  }

  function toggleMultiAnswer(questionId: string, optionId: string) {
    setAnswers((current) => {
      const existing = current[questionId];
      const selected = Array.isArray(existing) ? existing : [];
      const next = selected.includes(optionId)
        ? selected.filter((id) => id !== optionId)
        : [...selected, optionId];
      return { ...current, [questionId]: next };
    });
  }

  function validateAnswers(): string | null {
    for (const question of questions) {
      const value = answers[question.id];
      if (question.type === "single") {
        if (typeof value !== "string" || !value) {
          return `Please answer: ${question.prompt}`;
        }
      } else if (!Array.isArray(value) || value.length === 0) {
        return `Please select at least one option for: ${question.prompt}`;
      }
    }
    return null;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setServerError(null);
    const validationMessage = validateAnswers();
    if (validationMessage) {
      setFieldError(validationMessage);
      return;
    }

    setFieldError(null);
    setPending(true);
    const result = await saveAnswers(answers);
    setPending(false);

    if (!result.ok) {
      setServerError(result.error.message);
      return;
    }

    await refreshMe();
    navigate("/dashboard");
  }

  return (
    <main className="animate-in fade-in mx-auto flex min-h-[70vh] max-w-2xl flex-col justify-center px-4 py-8 duration-300">
      <div className="mb-6 space-y-2 text-center">
        <h1 className="text-3xl font-semibold tracking-tight">AI Crypto Advisor</h1>
        <p className="text-muted-foreground text-sm">
          Tell us your preferences so we can personalize your daily dashboard.
        </p>
      </div>

      <Card className="transition-shadow duration-300">
        <CardHeader>
          <CardTitle>Onboarding quiz</CardTitle>
          <CardDescription>Answer a few questions to finish setup.</CardDescription>
        </CardHeader>

        {loading ? (
          <CardContent>
            <p className="text-muted-foreground text-sm">Loading questions…</p>
          </CardContent>
        ) : null}

        {!loading && loadError ? (
          <CardContent>
            <p className="text-destructive text-sm" role="alert">
              {loadError}
            </p>
          </CardContent>
        ) : null}

        {!loading && !loadError && questions.length === 0 ? (
          <CardContent>
            <p className="text-muted-foreground text-sm">No onboarding questions available.</p>
          </CardContent>
        ) : null}

        {!loading && !loadError && questions.length > 0 ? (
          <form onSubmit={onSubmit}>
            <CardContent className="space-y-8">
              {questions.map((question) => {
                const current = answers[question.id];
                return (
                <fieldset key={question.id} className="space-y-3">
                  <legend className="text-sm font-medium">{question.prompt}</legend>

                  {question.type === "single" ? (
                    <RadioGroup
                      value={typeof current === "string" ? current : ""}
                      onValueChange={(value) => setSingleAnswer(question.id, value)}
                      disabled={pending}
                    >
                      {question.options.map((option) => (
                        <div key={option.id} className="flex items-center gap-2">
                          <RadioGroupItem
                            id={`${question.id}-${option.id}`}
                            value={option.id}
                          />
                          <Label htmlFor={`${question.id}-${option.id}`}>{option.label}</Label>
                        </div>
                      ))}
                    </RadioGroup>
                  ) : (
                    <div className="space-y-2">
                      {question.options.map((option) => {
                        const selected = Array.isArray(current) ? current : [];
                        const checked = selected.includes(option.id);
                        return (
                          <div key={option.id} className="flex items-center gap-2">
                            <Checkbox
                              id={`${question.id}-${option.id}`}
                              checked={checked}
                              disabled={pending}
                              onCheckedChange={() =>
                                toggleMultiAnswer(question.id, option.id)
                              }
                            />
                            <Label htmlFor={`${question.id}-${option.id}`}>
                              {option.label}
                            </Label>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </fieldset>
                );
              })}

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
            <CardFooter>
              <Button type="submit" className="w-full" disabled={pending}>
                {pending ? "Saving…" : "Finish onboarding"}
              </Button>
            </CardFooter>
          </form>
        ) : null}
      </Card>
    </main>
  );
}
