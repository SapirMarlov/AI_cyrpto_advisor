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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:5000";

export async function getHealth(): Promise<ApiEnvelope<{ status: string }>> {
  const response = await fetch(`${API_BASE_URL}/api/health`, {
    method: "GET",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });

  return (await response.json()) as ApiEnvelope<{ status: string }>;
}
