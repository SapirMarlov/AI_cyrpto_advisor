export type ApiSuccess<T> = {
  ok: true;
  data: T;
  error: null;
};

export type ApiError = {
  ok: false;
  data: null;
  error: {
    code: string;
    message: string;
  };
};

export type ApiEnvelope<T> = ApiSuccess<T> | ApiError;

export type User = {
  id: number;
  email: string;
};

export type AuthUserData = {
  user: User;
};

export type MeData = {
  user: User;
  onboarding_completed: boolean;
};

export type OnboardingQuestionOption = {
  id: string;
  label: string;
};

export type OnboardingQuestion = {
  id: string;
  prompt: string;
  type: "single" | "multi";
  options: OnboardingQuestionOption[];
};

export type QuestionsData = {
  questions: OnboardingQuestion[];
};

export type PreferencesData = {
  user_id: number;
  answers: Record<string, string | string[]>;
  onboarding_completed: boolean;
  updated_at?: string;
};

export type SaveAnswersData = {
  onboarding_completed: boolean;
  preferences: PreferencesData;
};

export type SectionError = {
  code: string;
  message: string;
} | null;

export type DashboardSection<T> = {
  data: T | null;
  error: SectionError;
  stale: boolean;
};

export type NewsItem = {
  title: string;
  url: string;
  source: string;
  published_at: string | null;
};

export type NewsData = {
  items: NewsItem[];
};

export type PriceQuote = {
  usd: number | null;
  change_24h: number | null;
  [key: string]: unknown;
};

export type PricesData = {
  prices: Record<string, PriceQuote>;
};

export type InsightData = {
  insight_text: string;
  generated_by: string;
};

export type MemeData = {
  title: string;
  image_url: string;
  permalink?: string;
  subreddit?: string;
  upvotes?: number;
  [key: string]: unknown;
};

export type DailyDashboardData = {
  generated_at: string;
  sections: {
    news: DashboardSection<NewsData>;
    prices: DashboardSection<PricesData>;
    insight: DashboardSection<InsightData>;
    meme: DashboardSection<MemeData>;
  };
};

export type VoteType = "up" | "down";
export type VoteItemType = "news" | "insight" | "meme";

export type VoteData = {
  id: number;
  user_id: number;
  item_id: string;
  item_type: VoteItemType;
  vote_type: VoteType;
  created_at: string;
  updated_at: string;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:5000";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function parseEnvelope<T>(payload: unknown): ApiEnvelope<T> {
  if (!isRecord(payload) || typeof payload.ok !== "boolean") {
    return {
      ok: false,
      data: null,
      error: { code: "malformed_response", message: "Invalid API response" },
    };
  }

  if (payload.ok === true) {
    return { ok: true, data: payload.data as T, error: null };
  }

  const error = isRecord(payload.error) ? payload.error : null;
  const code = typeof error?.code === "string" ? error.code : "unknown_error";
  const message =
    typeof error?.message === "string" ? error.message : "Request failed";

  return {
    ok: false,
    data: null,
    error: { code, message },
  };
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<ApiEnvelope<T>> {
  const url = `${API_BASE_URL}${path}`;
  try {
    const response = await fetch(url, {
      ...options,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers ?? {}),
      },
    });

    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      return {
        ok: false,
        data: null,
        error: { code: "malformed_response", message: "Invalid API response" },
      };
    }

    return parseEnvelope<T>(payload);
  } catch {
    return {
      ok: false,
      data: null,
      error: { code: "network_error", message: "Network request failed" },
    };
  }
}

export async function getHealth(): Promise<ApiEnvelope<{ status: string }>> {
  return request<{ status: string }>("/api/health");
}

export async function signup(
  email: string,
  password: string,
): Promise<ApiEnvelope<AuthUserData>> {
  return request<AuthUserData>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function login(
  email: string,
  password: string,
): Promise<ApiEnvelope<AuthUserData>> {
  return request<AuthUserData>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function logout(): Promise<ApiEnvelope<{ loggedOut: boolean }>> {
  return request<{ loggedOut: boolean }>("/api/auth/logout", {
    method: "POST",
  });
}

export async function me(): Promise<ApiEnvelope<MeData>> {
  return request<MeData>("/api/auth/me");
}

export async function getQuestions(): Promise<ApiEnvelope<QuestionsData>> {
  return request<QuestionsData>("/api/onboarding/questions");
}

export async function saveAnswers(
  answers: Record<string, string | string[]>,
): Promise<ApiEnvelope<SaveAnswersData>> {
  return request<SaveAnswersData>("/api/onboarding/answers", {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}

export async function getDailyDashboard(): Promise<
  ApiEnvelope<DailyDashboardData>
> {
  return request<DailyDashboardData>("/api/dashboard/daily");
}

export async function vote(
  itemId: string,
  itemType: VoteItemType,
  voteType: VoteType,
): Promise<ApiEnvelope<VoteData>> {
  return request<VoteData>("/api/feedback/vote", {
    method: "POST",
    body: JSON.stringify({
      item_id: itemId,
      item_type: itemType,
      vote_type: voteType,
    }),
  });
}
